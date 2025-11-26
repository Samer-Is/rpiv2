"""
STEP 0-D: Data preparation and training dataset creation.

This module:
1. Extracts data from key tables (Fleet.VehicleHistory, Rental.Contract, etc.)
2. Applies date filter (2023-01-01 onwards)
3. Calculates fleet utilization from VehicleHistory
4. Prepares features for demand prediction
5. Saves training data to .parquet format
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Tuple, Dict
from db import DatabaseConnection
import config

logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


def extract_vehicle_history(db: DatabaseConnection) -> pd.DataFrame:
    """
    Extract vehicle history data from Fleet.VehicleHistory.
    
    This is the MANDATORY source for utilization calculation.
    
    Args:
        db: Database connection object
        
    Returns:
        pd.DataFrame: Vehicle history records from 2023-01-01 onwards
    """
    logger.info("Extracting Fleet.VehicleHistory data...")
    
    query = f"""
    SELECT 
        Id,
        CAST(CreationTime AS DATETIME) as CreationTime,
        CAST(OperationDateTime AS DATETIME) as OperationDateTime,
        VehicleId,
        StatusId,
        BranchId,
        CurrentLocationId,
        Odometer,
        OperationId,
        ReferenceNo,
        TenantId,
        AdditionalStatuses,
        IsActive
    FROM [Fleet].[VehicleHistory]
    WHERE OperationDateTime >= '{config.MIN_DATE}'
        AND IsActive = 1
    ORDER BY OperationDateTime, VehicleId
    """
    
    df = db.execute_query(query)
    logger.info(f"  ✓ Extracted {len(df):,} vehicle history records")
    logger.info(f"  ✓ Date range: {df['OperationDateTime'].min()} to {df['OperationDateTime'].max()}")
    logger.info(f"  ✓ Unique vehicles: {df['VehicleId'].nunique():,}")
    
    return df


def extract_contracts(db: DatabaseConnection) -> pd.DataFrame:
    """
    Extract rental contract data from Rental.Contract.
    
    Args:
        db: Database connection object
        
    Returns:
        pd.DataFrame: Contract records from 2023-01-01 onwards
    """
    logger.info("Extracting Rental.Contract data...")
    
    query = f"""
    SELECT 
        Id,
        ContractNumber,
        CAST(CreationTime AS DATETIME) as CreationTime,
        CAST(Start AS DATETIME) as Start,
        CAST([End] AS DATETIME) as [End],
        CAST(ActualDropOffDate AS DATETIME) as ActualDropOffDate,
        StatusId,
        FinancialStatusId,
        VehicleId,
        PickupBranchId,
        DropoffBranchId,
        CustomerId,
        DailyRateAmount,
        MonthlyRateAmount,
        CurrencyId,
        RentalRateId,
        BookingId,
        TenantId,
        Discriminator
    FROM [Rental].[Contract]
    WHERE Start >= '{config.MIN_DATE}'
    ORDER BY Start
    """
    
    df = db.execute_query(query)
    logger.info(f"  ✓ Extracted {len(df):,} contract records")
    logger.info(f"  ✓ Date range: {df['Start'].min()} to {df['Start'].max()}")
    logger.info(f"  ✓ Unique customers: {df['CustomerId'].nunique():,}")
    
    return df


def extract_bookings(db: DatabaseConnection) -> pd.DataFrame:
    """
    Extract booking data from Rental.Bookings.
    
    Args:
        db: Database connection object
        
    Returns:
        pd.DataFrame: Booking records from 2023-01-01 onwards
    """
    logger.info("Extracting Rental.Bookings data...")
    
    query = f"""
    SELECT 
        Id,
        BookingNumber,
        CAST(CreationTime AS DATETIME) as CreationTime,
        CAST(PickupDate AS DATETIME) as PickupDate,
        CAST(DropoffDate AS DATETIME) as DropoffDate,
        StatusId,
        PickupBranchId,
        DropoffBranchId,
        ModelId,
        Year,
        RentalRateId,
        SourceId,
        TotalPaidAmount,
        TotalDueAmount,
        TenantId
    FROM [Rental].[Bookings]
    WHERE CreationTime >= '{config.MIN_DATE}'
    ORDER BY CreationTime
    """
    
    df = db.execute_query(query)
    logger.info(f"  ✓ Extracted {len(df):,} booking records")
    logger.info(f"  ✓ Date range: {df['CreationTime'].min()} to {df['CreationTime'].max()}")
    
    return df


def extract_rental_rates(db: DatabaseConnection) -> pd.DataFrame:
    """
    Extract rental rate configurations from Rental.RentalRates.
    
    Args:
        db: Database connection object
        
    Returns:
        pd.DataFrame: Rental rate records
    """
    logger.info("Extracting Rental.RentalRates data...")
    
    query = f"""
    SELECT 
        Id,
        CAST(Start AS DATETIME) as Start,
        CAST([End] AS DATETIME) as [End],
        CountryId,
        BranchId,
        ModelId,
        Year,
        DailyFreeKm,
        MonthlyFreeKM,
        ExtraKmCost,
        IsActive,
        SchemaId
    FROM [Rental].[RentalRates]
    WHERE IsActive = 1
    ORDER BY Start
    """
    
    df = db.execute_query(query)
    logger.info(f"  ✓ Extracted {len(df):,} rental rate records")
    
    return df


def extract_supporting_data(db: DatabaseConnection) -> Dict[str, pd.DataFrame]:
    """
    Extract supporting dimensional data.
    
    Args:
        db: Database connection object
        
    Returns:
        Dict of DataFrames with supporting tables
    """
    logger.info("Extracting supporting dimensional data...")
    
    supporting = {}
    
    # Branches
    query = "SELECT Id, Name, CityId, CountryId, IsActive, IsAirport FROM [Rental].[Branches]"
    supporting['branches'] = db.execute_query(query)
    logger.info(f"  ✓ Branches: {len(supporting['branches'])} records")
    
    # Cities
    query = "SELECT Id, Name, CountryId, IsActive FROM [Rental].[Cities]"
    supporting['cities'] = db.execute_query(query)
    logger.info(f"  ✓ Cities: {len(supporting['cities'])} records")
    
    # Countries
    query = "SELECT Id, Name, IsoCodeAlpha3, IsoCodeAlpha2 FROM [Rental].[Countries]"
    supporting['countries'] = db.execute_query(query)
    logger.info(f"  ✓ Countries: {len(supporting['countries'])} records")
    
    # Vehicles
    query = """
    SELECT Id, PlateNo, ModelId, Year, StatusId, BranchId, FuelId
    FROM [Fleet].[Vehicles]
    WHERE IsDeleted = 0
    """
    supporting['vehicles'] = db.execute_query(query)
    logger.info(f"  ✓ Vehicles: {len(supporting['vehicles'])} records")
    
    return supporting


def calculate_utilization(vehicle_history: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate fleet utilization from Fleet.VehicleHistory.
    
    Utilization = % of time vehicles are in 'Rented' status vs 'Available' status.
    
    This function:
    1. Groups by date and branch
    2. Counts vehicles in different statuses
    3. Calculates utilization percentage
    
    Args:
        vehicle_history: Raw vehicle history data
        
    Returns:
        pd.DataFrame: Utilization metrics by date and branch
    """
    logger.info("Calculating fleet utilization...")
    
    # Convert to datetime
    vehicle_history['Date'] = pd.to_datetime(vehicle_history['OperationDateTime']).dt.date
    
    # Group by date, branch, and status
    status_counts = vehicle_history.groupby(['Date', 'BranchId', 'StatusId']).agg({
        'VehicleId': 'nunique'
    }).reset_index()
    status_counts.columns = ['Date', 'BranchId', 'StatusId', 'VehicleCount']
    
    # Calculate total vehicles per date/branch
    total_vehicles = status_counts.groupby(['Date', 'BranchId'])['VehicleCount'].sum().reset_index()
    total_vehicles.columns = ['Date', 'BranchId', 'TotalVehicles']
    
    # Pivot to get status columns
    status_pivot = status_counts.pivot_table(
        index=['Date', 'BranchId'],
        columns='StatusId',
        values='VehicleCount',
        fill_value=0
    ).reset_index()
    
    # Merge with totals
    utilization = status_pivot.merge(total_vehicles, on=['Date', 'BranchId'])
    
    # Calculate utilization percentage (will need to map StatusId to actual status names)
    # For now, we'll keep all status counts
    
    logger.info(f"  ✓ Calculated utilization for {len(utilization)} date-branch combinations")
    logger.info(f"  ✓ Date range: {utilization['Date'].min()} to {utilization['Date'].max()}")
    
    return utilization


def prepare_training_features(
    contracts: pd.DataFrame,
    bookings: pd.DataFrame,
    utilization: pd.DataFrame,
    supporting: Dict[str, pd.DataFrame]
) -> pd.DataFrame:
    """
    Prepare features for demand prediction model.
    
    Features include:
    - Temporal: day of week, month, season, holidays (will be added in STEP 0-F)
    - Location: branch, city, country, airport flag
    - Historical: past bookings, past utilization
    - Pricing: historical rates (if available)
    
    Args:
        contracts: Contract data
        bookings: Booking data
        utilization: Calculated utilization
        supporting: Supporting dimensional data
        
    Returns:
        pd.DataFrame: Feature matrix for training
    """
    logger.info("Preparing training features...")
    
    # Start with contracts as base
    features = contracts.copy()
    
    # Add temporal features
    features['Start'] = pd.to_datetime(features['Start'])
    features['DayOfWeek'] = features['Start'].dt.dayofweek
    features['Month'] = features['Start'].dt.month
    features['Quarter'] = features['Start'].dt.quarter
    features['IsWeekend'] = features['DayOfWeek'].isin([5, 6]).astype(int)
    
    # Add contract duration
    features['End'] = pd.to_datetime(features['End'])
    features['ContractDurationDays'] = (features['End'] - features['Start']).dt.days
    
    # Merge with branches to get location info
    features = features.merge(
        supporting['branches'][['Id', 'CityId', 'CountryId', 'IsAirport']],
        left_on='PickupBranchId',
        right_on='Id',
        how='left',
        suffixes=('', '_branch')
    )
    
    # Add vehicle info
    features = features.merge(
        supporting['vehicles'][['Id', 'ModelId', 'Year']],
        left_on='VehicleId',
        right_on='Id',
        how='left',
        suffixes=('', '_vehicle')
    )
    
    logger.info(f"  ✓ Prepared {len(features)} training samples")
    logger.info(f"  ✓ Feature count: {len(features.columns)} columns")
    
    return features


def create_training_dataset() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Main function to create training dataset.
    
    Returns:
        Tuple of (training_features, utilization, supporting_data_summary)
    """
    logger.info("=" * 80)
    logger.info("STEP 0-D: Creating Training Dataset")
    logger.info("=" * 80)
    
    try:
        with DatabaseConnection() as db:
            # Step 1: Extract raw data
            logger.info("\n1. Extracting raw data from database...")
            vehicle_history = extract_vehicle_history(db)
            contracts = extract_contracts(db)
            bookings = extract_bookings(db)
            rental_rates = extract_rental_rates(db)
            supporting = extract_supporting_data(db)
            
            # Step 2: Calculate utilization
            logger.info("\n2. Calculating fleet utilization...")
            utilization = calculate_utilization(vehicle_history)
            
            # Step 3: Prepare training features
            logger.info("\n3. Preparing training features...")
            training_features = prepare_training_features(
                contracts, bookings, utilization, supporting
            )
            
            # Step 4: Save to parquet
            logger.info("\n4. Saving training dataset...")
            training_path = config.TRAINING_DATA_FILE
            training_features.to_parquet(training_path, index=False)
            logger.info(f"  ✓ Training data saved: {training_path}")
            logger.info(f"  ✓ File size: {training_path.stat().st_size / 1024 / 1024:.2f} MB")
            
            # Also save utilization separately
            utilization_path = config.PROCESSED_DATA_DIR / 'utilization.parquet'
            utilization.to_parquet(utilization_path, index=False)
            logger.info(f"  ✓ Utilization data saved: {utilization_path}")
            
            logger.info("\n" + "=" * 80)
            logger.info("STEP 0-D: COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)
            logger.info(f"\nTraining dataset summary:")
            logger.info(f"  - Samples: {len(training_features):,}")
            logger.info(f"  - Features: {len(training_features.columns)}")
            logger.info(f"  - Date range: {training_features['Start'].min()} to {training_features['Start'].max()}")
            logger.info(f"  - Utilization records: {len(utilization):,}")
            
            return training_features, utilization, supporting
    
    except Exception as e:
        logger.error(f"STEP 0-D FAILED: {str(e)}")
        logger.error("\nPlease ensure:")
        logger.error("  1. Database connection is configured in config.py")
        logger.error("  2. Database contains data from 2023-01-01 onwards")
        logger.error("  3. All key tables exist and are accessible")
        raise


if __name__ == "__main__":
    # Run training dataset creation
    training_features, utilization, supporting = create_training_dataset()

