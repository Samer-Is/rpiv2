"""
Database connection and operations module for Dynamic Pricing Engine MVP.

This module provides:
- Database connection utilities (SQL Server with Windows Auth)
- Table discovery and metadata retrieval
- Data extraction functions
- Query execution helpers
"""

import pyodbc
import pandas as pd
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
import config

# Setup logging
logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Database connection manager for SQL Server with Windows Authentication.
    """
    
    def __init__(self):
        """Initialize database connection parameters from config."""
        self.config = config.DB_CONFIG
        self.connection = None
        self.cursor = None
    
    def connect(self) -> bool:
        """
        Establish database connection using Windows Authentication.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            conn_string = config.CONNECTION_STRING.format(**self.config)
            self.connection = pyodbc.connect(conn_string)
            self.cursor = self.connection.cursor()
            logger.info(f"Successfully connected to database: {self.config['database']}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Database connection closed")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """
        Execute SQL query and return results as pandas DataFrame.
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            pd.DataFrame: Query results
        """
        try:
            if params:
                return pd.read_sql(query, self.connection, params=params)
            else:
                return pd.read_sql(query, self.connection)
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


def read_db_dictionary(file_path: Path = config.DB_DICTIONARY_FILE) -> pd.DataFrame:
    """
    Read and parse database dictionary file.
    
    The database dictionary contains schema metadata in format:
    SchemaName TableName ColumnID ColumnName DataType MaxLength IsNullable IsIdentity IsPrimaryKey DefaultValue
    
    Args:
        file_path: Path to database dictionary file
        
    Returns:
        pd.DataFrame: Parsed database schema information
    """
    logger.info(f"Reading database dictionary from: {file_path}")
    
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Parse lines (skip header if exists)
        data = []
        for line in lines[1:]:  # Skip first line (header)
            parts = line.strip().split('\t')
            if len(parts) >= 10:
                # Extract line number (first part before |)
                if '|' in parts[0]:
                    parts[0] = parts[0].split('|')[1]
                
                data.append({
                    'SchemaName': parts[0],
                    'TableName': parts[1],
                    'ColumnID': parts[2],
                    'ColumnName': parts[3],
                    'DataType': parts[4],
                    'MaxLength': parts[5],
                    'IsNullable': parts[6],
                    'IsIdentity': parts[7],
                    'IsPrimaryKey': parts[8],
                    'DefaultValue': parts[9] if len(parts) > 9 else None,
                })
        
        df = pd.DataFrame(data)
        logger.info(f"Successfully parsed {len(df)} columns from {len(df.groupby(['SchemaName', 'TableName']))} tables")
        
        return df
    
    except Exception as e:
        logger.error(f"Failed to read database dictionary: {str(e)}")
        raise


def get_table_summary(db_dict: pd.DataFrame) -> pd.DataFrame:
    """
    Generate summary statistics for each table in the database.
    
    Args:
        db_dict: Database dictionary DataFrame
        
    Returns:
        pd.DataFrame: Summary with columns: SchemaName, TableName, ColumnCount, PKCount, HasIdentity
    """
    logger.info("Generating table summary from database dictionary")
    
    summary = db_dict.groupby(['SchemaName', 'TableName']).agg({
        'ColumnName': 'count',
        'IsPrimaryKey': lambda x: (x == '1').sum(),
        'IsIdentity': lambda x: (x == '1').sum(),
    }).reset_index()
    
    summary.columns = ['SchemaName', 'TableName', 'ColumnCount', 'PKCount', 'IdentityCount']
    summary = summary.sort_values(['SchemaName', 'TableName'])
    
    logger.info(f"Generated summary for {len(summary)} tables")
    
    return summary


def discover_key_tables(db_dict: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Discover and categorize key tables for dynamic pricing analysis.
    
    Based on instructions, we focus on:
    - Fleet.VehicleHistory (mandatory for utilization)
    - Rental.Contract (pricing history)
    - Rental.Bookings (demand signals)
    - Supporting tables for context
    
    Args:
        db_dict: Database dictionary DataFrame
        
    Returns:
        Dict mapping category to list of table names
    """
    logger.info("Discovering key tables for dynamic pricing")
    
    key_tables = {
        'utilization': [],
        'demand': [],
        'pricing': [],
        'context': [],
    }
    
    # Get unique schema.table combinations
    tables = db_dict.groupby(['SchemaName', 'TableName']).size().reset_index()[['SchemaName', 'TableName']]
    
    for _, row in tables.iterrows():
        schema = row['SchemaName']
        table = row['TableName']
        full_name = f"{schema}.{table}"
        
        # Categorize tables
        if schema == 'Fleet' and table == 'VehicleHistory':
            key_tables['utilization'].append(full_name)
        elif schema == 'Rental' and table in ['Bookings', 'Contract']:
            key_tables['demand'].append(full_name)
        elif schema == 'Rental' and table == 'RentalRates':
            key_tables['pricing'].append(full_name)
        elif schema in ['Fleet', 'Rental'] and table in ['Vehicles', 'Branches', 'Locations', 'Cities', 'Countries']:
            key_tables['context'].append(full_name)
    
    # Log findings
    for category, tables_list in key_tables.items():
        logger.info(f"  {category.upper()}: {len(tables_list)} tables")
        for table in tables_list:
            logger.info(f"    - {table}")
    
    return key_tables


def get_table_columns(db_dict: pd.DataFrame, schema: str, table: str) -> pd.DataFrame:
    """
    Get detailed column information for a specific table.
    
    Args:
        db_dict: Database dictionary DataFrame
        schema: Schema name
        table: Table name
        
    Returns:
        pd.DataFrame: Column details
    """
    return db_dict[
        (db_dict['SchemaName'] == schema) & 
        (db_dict['TableName'] == table)
    ].copy()


def validate_table_exists(db_dict: pd.DataFrame, schema: str, table: str) -> bool:
    """
    Check if a table exists in the database dictionary.
    
    Args:
        db_dict: Database dictionary DataFrame
        schema: Schema name
        table: Table name
        
    Returns:
        bool: True if table exists
    """
    exists = len(db_dict[
        (db_dict['SchemaName'] == schema) & 
        (db_dict['TableName'] == table)
    ]) > 0
    
    if exists:
        logger.info(f"✓ Table {schema}.{table} found in database dictionary")
    else:
        logger.warning(f"✗ Table {schema}.{table} NOT found in database dictionary")
    
    return exists


def get_table_row_count(db_conn: DatabaseConnection, schema: str, table: str) -> int:
    """
    Get row count for a specific table.
    
    Args:
        db_conn: Database connection object
        schema: Schema name
        table: Table name
        
    Returns:
        int: Number of rows in table
    """
    try:
        query = f"SELECT COUNT(*) as row_count FROM [{schema}].[{table}]"
        result = db_conn.execute_query(query)
        count = result['row_count'].iloc[0]
        logger.info(f"Table {schema}.{table} has {count:,} rows")
        return count
    except Exception as e:
        logger.error(f"Failed to get row count for {schema}.{table}: {str(e)}")
        return 0


def preview_table(db_conn: DatabaseConnection, schema: str, table: str, n_rows: int = 5) -> pd.DataFrame:
    """
    Preview first N rows of a table.
    
    Args:
        db_conn: Database connection object
        schema: Schema name
        table: Table name
        n_rows: Number of rows to preview
        
    Returns:
        pd.DataFrame: Preview data
    """
    try:
        query = f"SELECT TOP {n_rows} * FROM [{schema}].[{table}]"
        result = db_conn.execute_query(query)
        logger.info(f"Preview of {schema}.{table}: {len(result)} rows, {len(result.columns)} columns")
        return result
    except Exception as e:
        logger.error(f"Failed to preview {schema}.{table}: {str(e)}")
        return pd.DataFrame()


if __name__ == "__main__":
    """
    Test database connection and dictionary reading.
    """
    logger.info("=" * 80)
    logger.info("STEP 0-A: Testing database dictionary reading")
    logger.info("=" * 80)
    
    # Test 1: Read database dictionary
    try:
        db_dict = read_db_dictionary()
        logger.info(f"✓ Database dictionary loaded: {len(db_dict)} columns")
        
        # Test 2: Generate table summary
        summary = get_table_summary(db_dict)
        logger.info(f"✓ Table summary generated: {len(summary)} tables")
        
        # Test 3: Discover key tables
        key_tables = discover_key_tables(db_dict)
        logger.info("✓ Key tables discovered")
        
        # Test 4: Validate critical table exists
        validate_table_exists(db_dict, 'Fleet', 'VehicleHistory')
        validate_table_exists(db_dict, 'Rental', 'Contract')
        validate_table_exists(db_dict, 'Rental', 'Bookings')
        
        logger.info("=" * 80)
        logger.info("STEP 0-A: COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"STEP 0-A FAILED: {str(e)}")


