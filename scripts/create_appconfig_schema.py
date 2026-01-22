"""
CHUNK 2: Create appconfig schema and configuration tables
This script creates the appconfig schema in eJarDbSTGLite with all required tables.
"""
import pyodbc
from datetime import datetime

CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost;"
    "Database=eJarDbSTGLite;"
    "Trusted_Connection=yes;"
)

def get_connection():
    return pyodbc.connect(CONN_STR, autocommit=True)

def run_ddl(cursor, sql, description=""):
    """Execute DDL statement."""
    print(f"\n{'='*60}")
    print(f"EXECUTING: {description}")
    print(f"{'='*60}")
    try:
        cursor.execute(sql)
        print("✅ SUCCESS")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    print("=" * 80)
    print("CHUNK 2: Creating appconfig Schema and Tables")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Create appconfig schema if not exists
    run_ddl(cursor, """
        IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'appconfig')
        BEGIN
            EXEC('CREATE SCHEMA appconfig')
        END
    """, "Create appconfig schema")
    
    # 2. Create appconfig.tenants table
    run_ddl(cursor, """
        IF NOT EXISTS (SELECT * FROM sys.tables t 
                       INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                       WHERE s.name = 'appconfig' AND t.name = 'tenants')
        BEGIN
            CREATE TABLE appconfig.tenants (
                id INT PRIMARY KEY,
                name NVARCHAR(255) NOT NULL,
                tenancy_name NVARCHAR(128) NOT NULL,
                is_active BIT NOT NULL DEFAULT 1,
                source_tenant_id INT NOT NULL,  -- Maps to dbo.AbpTenants.Id
                created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                updated_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                created_by NVARCHAR(255) NULL
            )
        END
    """, "Create appconfig.tenants table")
    
    # 3. Create appconfig.tenant_settings table
    run_ddl(cursor, """
        IF NOT EXISTS (SELECT * FROM sys.tables t 
                       INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                       WHERE s.name = 'appconfig' AND t.name = 'tenant_settings')
        BEGIN
            CREATE TABLE appconfig.tenant_settings (
                id INT IDENTITY(1,1) PRIMARY KEY,
                tenant_id INT NOT NULL,
                setting_key NVARCHAR(255) NOT NULL,
                setting_value NVARCHAR(MAX) NOT NULL,
                setting_type NVARCHAR(50) NOT NULL DEFAULT 'string',  -- string, int, float, bool, json
                description NVARCHAR(500) NULL,
                created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                updated_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                CONSTRAINT FK_tenant_settings_tenant FOREIGN KEY (tenant_id) REFERENCES appconfig.tenants(id),
                CONSTRAINT UQ_tenant_settings UNIQUE (tenant_id, setting_key)
            )
        END
    """, "Create appconfig.tenant_settings table")
    
    # 4. Create appconfig.guardrails table
    run_ddl(cursor, """
        IF NOT EXISTS (SELECT * FROM sys.tables t 
                       INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                       WHERE s.name = 'appconfig' AND t.name = 'guardrails')
        BEGIN
            CREATE TABLE appconfig.guardrails (
                id INT IDENTITY(1,1) PRIMARY KEY,
                tenant_id INT NOT NULL,
                category_id INT NULL,  -- NULL means applies to all categories
                branch_id INT NULL,    -- NULL means applies to all branches
                min_price DECIMAL(10,2) NOT NULL DEFAULT 50.00,
                max_price DECIMAL(10,2) NULL,
                min_discount_pct DECIMAL(5,2) NOT NULL DEFAULT 0.00,
                max_discount_pct DECIMAL(5,2) NOT NULL DEFAULT 30.00,
                min_premium_pct DECIMAL(5,2) NOT NULL DEFAULT 0.00,
                max_premium_pct DECIMAL(5,2) NOT NULL DEFAULT 50.00,
                is_active BIT NOT NULL DEFAULT 1,
                created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                updated_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                CONSTRAINT FK_guardrails_tenant FOREIGN KEY (tenant_id) REFERENCES appconfig.tenants(id)
            )
        END
    """, "Create appconfig.guardrails table")
    
    # 5. Create appconfig.signal_weights table
    run_ddl(cursor, """
        IF NOT EXISTS (SELECT * FROM sys.tables t 
                       INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                       WHERE s.name = 'appconfig' AND t.name = 'signal_weights')
        BEGIN
            CREATE TABLE appconfig.signal_weights (
                id INT IDENTITY(1,1) PRIMARY KEY,
                tenant_id INT NOT NULL,
                signal_name NVARCHAR(100) NOT NULL,  -- utilization, demand_forecast, weather, holiday, event, competitor
                weight DECIMAL(5,3) NOT NULL DEFAULT 1.000,  -- Weight multiplier
                is_enabled BIT NOT NULL DEFAULT 1,
                description NVARCHAR(500) NULL,
                created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                updated_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                CONSTRAINT FK_signal_weights_tenant FOREIGN KEY (tenant_id) REFERENCES appconfig.tenants(id),
                CONSTRAINT UQ_signal_weights UNIQUE (tenant_id, signal_name)
            )
        END
    """, "Create appconfig.signal_weights table")
    
    # 6. Create appconfig.utilization_status_config table
    run_ddl(cursor, """
        IF NOT EXISTS (SELECT * FROM sys.tables t 
                       INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                       WHERE s.name = 'appconfig' AND t.name = 'utilization_status_config')
        BEGIN
            CREATE TABLE appconfig.utilization_status_config (
                id INT IDENTITY(1,1) PRIMARY KEY,
                tenant_id INT NOT NULL,
                status_id BIGINT NOT NULL,
                status_name NVARCHAR(255) NOT NULL,
                status_type NVARCHAR(50) NOT NULL,  -- 'numerator' (occupied), 'denominator' (available), 'excluded'
                description NVARCHAR(500) NULL,
                is_active BIT NOT NULL DEFAULT 1,
                created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                updated_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                CONSTRAINT FK_utilization_status_tenant FOREIGN KEY (tenant_id) REFERENCES appconfig.tenants(id),
                CONSTRAINT UQ_utilization_status UNIQUE (tenant_id, status_id)
            )
        END
    """, "Create appconfig.utilization_status_config table")
    
    # 7. Create appconfig.branch_city_mapping table (for weather API)
    run_ddl(cursor, """
        IF NOT EXISTS (SELECT * FROM sys.tables t 
                       INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                       WHERE s.name = 'appconfig' AND t.name = 'branch_city_mapping')
        BEGIN
            CREATE TABLE appconfig.branch_city_mapping (
                id INT IDENTITY(1,1) PRIMARY KEY,
                tenant_id INT NOT NULL,
                branch_id INT NOT NULL,
                branch_name NVARCHAR(500) NULL,
                city_id INT NULL,
                city_name NVARCHAR(255) NULL,
                latitude DECIMAL(9,6) NULL,
                longitude DECIMAL(9,6) NULL,
                timezone NVARCHAR(100) NULL DEFAULT 'Asia/Riyadh',
                is_active BIT NOT NULL DEFAULT 1,
                created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                updated_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                CONSTRAINT FK_branch_city_tenant FOREIGN KEY (tenant_id) REFERENCES appconfig.tenants(id),
                CONSTRAINT UQ_branch_city UNIQUE (tenant_id, branch_id)
            )
        END
    """, "Create appconfig.branch_city_mapping table")
    
    # 8. Create appconfig.competitor_mapping table
    run_ddl(cursor, """
        IF NOT EXISTS (SELECT * FROM sys.tables t 
                       INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                       WHERE s.name = 'appconfig' AND t.name = 'competitor_mapping')
        BEGIN
            CREATE TABLE appconfig.competitor_mapping (
                id INT IDENTITY(1,1) PRIMARY KEY,
                tenant_id INT NOT NULL,
                category_id INT NOT NULL,
                category_name NVARCHAR(255) NULL,
                competitor_vehicle_type NVARCHAR(255) NOT NULL,  -- Booking.com vehicle type
                competitor_source NVARCHAR(100) NOT NULL DEFAULT 'booking.com',
                is_active BIT NOT NULL DEFAULT 1,
                created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                updated_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                CONSTRAINT FK_competitor_mapping_tenant FOREIGN KEY (tenant_id) REFERENCES appconfig.tenants(id),
                CONSTRAINT UQ_competitor_mapping UNIQUE (tenant_id, category_id, competitor_source)
            )
        END
    """, "Create appconfig.competitor_mapping table")
    
    # 9. Create appconfig.selection_config table (for top branches/categories)
    run_ddl(cursor, """
        IF NOT EXISTS (SELECT * FROM sys.tables t 
                       INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                       WHERE s.name = 'appconfig' AND t.name = 'selection_config')
        BEGIN
            CREATE TABLE appconfig.selection_config (
                id INT IDENTITY(1,1) PRIMARY KEY,
                tenant_id INT NOT NULL,
                selection_type NVARCHAR(50) NOT NULL,  -- 'branch', 'category'
                item_id INT NOT NULL,
                item_name NVARCHAR(500) NULL,
                item_subtype NVARCHAR(100) NULL,  -- For branches: 'airport', 'city'
                rank_order INT NOT NULL DEFAULT 0,
                is_active BIT NOT NULL DEFAULT 1,
                created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                updated_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                CONSTRAINT FK_selection_config_tenant FOREIGN KEY (tenant_id) REFERENCES appconfig.tenants(id),
                CONSTRAINT UQ_selection_config UNIQUE (tenant_id, selection_type, item_id)
            )
        END
    """, "Create appconfig.selection_config table")
    
    # 10. Create appconfig.audit_log table
    run_ddl(cursor, """
        IF NOT EXISTS (SELECT * FROM sys.tables t 
                       INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                       WHERE s.name = 'appconfig' AND t.name = 'audit_log')
        BEGIN
            CREATE TABLE appconfig.audit_log (
                id BIGINT IDENTITY(1,1) PRIMARY KEY,
                tenant_id INT NOT NULL,
                action_type NVARCHAR(100) NOT NULL,  -- 'config_change', 'approval', 'skip', 'model_retrain', etc.
                entity_type NVARCHAR(100) NOT NULL,  -- 'guardrail', 'signal_weight', 'recommendation', etc.
                entity_id NVARCHAR(255) NULL,
                old_value NVARCHAR(MAX) NULL,
                new_value NVARCHAR(MAX) NULL,
                user_id NVARCHAR(255) NULL,
                user_name NVARCHAR(255) NULL,
                ip_address NVARCHAR(50) NULL,
                notes NVARCHAR(MAX) NULL,
                created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                CONSTRAINT FK_audit_log_tenant FOREIGN KEY (tenant_id) REFERENCES appconfig.tenants(id)
            )
            
            CREATE INDEX IX_audit_log_tenant_created ON appconfig.audit_log(tenant_id, created_at DESC)
            CREATE INDEX IX_audit_log_action ON appconfig.audit_log(action_type, created_at DESC)
        END
    """, "Create appconfig.audit_log table")
    
    # 11. Insert YELO tenant record
    run_ddl(cursor, """
        IF NOT EXISTS (SELECT 1 FROM appconfig.tenants WHERE id = 1)
        BEGIN
            INSERT INTO appconfig.tenants (id, name, tenancy_name, is_active, source_tenant_id, created_by)
            VALUES (1, 'Yelo', 'Default', 1, 1, 'system_init')
        END
    """, "Insert YELO tenant record")
    
    # 12. Insert default guardrails for YELO
    run_ddl(cursor, """
        IF NOT EXISTS (SELECT 1 FROM appconfig.guardrails WHERE tenant_id = 1 AND category_id IS NULL)
        BEGIN
            INSERT INTO appconfig.guardrails (tenant_id, category_id, branch_id, min_price, min_discount_pct, max_discount_pct, min_premium_pct, max_premium_pct)
            VALUES (1, NULL, NULL, 50.00, 0.00, 30.00, 0.00, 50.00)
        END
    """, "Insert default guardrails for YELO")
    
    # 13. Insert default signal weights for YELO
    run_ddl(cursor, """
        IF NOT EXISTS (SELECT 1 FROM appconfig.signal_weights WHERE tenant_id = 1)
        BEGIN
            INSERT INTO appconfig.signal_weights (tenant_id, signal_name, weight, is_enabled, description) VALUES
            (1, 'utilization', 1.000, 1, 'Current and future utilization impact on pricing'),
            (1, 'demand_forecast', 1.000, 1, 'ML demand forecast signal'),
            (1, 'weather', 0.500, 1, 'Weather conditions impact'),
            (1, 'holiday', 1.000, 1, 'KSA holidays and events impact'),
            (1, 'event', 0.750, 1, 'News/events signal from GDELT'),
            (1, 'competitor', 0.500, 1, 'Competitor pricing signal')
        END
    """, "Insert default signal weights for YELO")
    
    # 14. Insert selection config from dynamicpricing.TopBranches
    run_ddl(cursor, """
        IF NOT EXISTS (SELECT 1 FROM appconfig.selection_config WHERE tenant_id = 1 AND selection_type = 'branch')
        BEGIN
            INSERT INTO appconfig.selection_config (tenant_id, selection_type, item_id, item_name, item_subtype, rank_order)
            SELECT 1, 'branch', BranchId, BranchName, BranchType, ROW_NUMBER() OVER (ORDER BY BranchId)
            FROM dynamicpricing.TopBranches
        END
    """, "Insert branch selection config from TopBranches")
    
    # 15. Insert selection config from dynamicpricing.TopCategories
    run_ddl(cursor, """
        IF NOT EXISTS (SELECT 1 FROM appconfig.selection_config WHERE tenant_id = 1 AND selection_type = 'category')
        BEGIN
            INSERT INTO appconfig.selection_config (tenant_id, selection_type, item_id, item_name, item_subtype, rank_order)
            SELECT 1, 'category', CategoryId, CategoryName, NULL, ROW_NUMBER() OVER (ORDER BY CategoryId)
            FROM dynamicpricing.TopCategories
        END
    """, "Insert category selection config from TopCategories")
    
    # 16. Insert branch city mapping with coordinates for MVP branches
    # Coordinates for KSA major cities
    run_ddl(cursor, """
        IF NOT EXISTS (SELECT 1 FROM appconfig.branch_city_mapping WHERE tenant_id = 1)
        BEGIN
            -- Insert from TopBranches with city coordinates
            INSERT INTO appconfig.branch_city_mapping (tenant_id, branch_id, branch_name, city_name, latitude, longitude, timezone)
            VALUES 
            -- Riyadh branches
            (1, 122, '{"en":"King Khalid Airport Terminal 5 - Riyadh","ar":"مطار الملك خالد الصالة 5 - الرياض"}', 'Riyadh', 24.9578, 46.6989, 'Asia/Riyadh'),
            (1, 2, '{"en":"Al Quds - Riyadh","ar":"القدس - الرياض"}', 'Riyadh', 24.7136, 46.6753, 'Asia/Riyadh'),
            (1, 211, '{"en":"Al Yarmuk - Riyadh","ar":"اليرموك - الرياض"}', 'Riyadh', 24.7136, 46.6753, 'Asia/Riyadh'),
            -- Jeddah branches
            (1, 15, '{"en":"King Abdulaziz Airport Terminal 1 - Jeddah","ar":"مطار الملك عبدالعزيز الصالة 1 - جدة"}', 'Jeddah', 21.6796, 39.1567, 'Asia/Riyadh'),
            -- Abha branches
            (1, 26, '{"en":"Abha Airport","ar":"مطار ابها"}', 'Abha', 18.2394, 42.6567, 'Asia/Riyadh'),
            -- Medina branches
            (1, 34, '{"en":"Al Khaldiyah - Al Madina","ar":"الخالدية - المدينة المنورة"}', 'Medina', 24.5247, 39.5692, 'Asia/Riyadh')
        END
    """, "Insert branch city mapping with coordinates")
    
    # Verify tables created
    cursor.execute("""
        SELECT s.name as SchemaName, t.name as TableName, 
               (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS c 
                WHERE c.TABLE_SCHEMA = s.name AND c.TABLE_NAME = t.name) as ColumnCount
        FROM sys.tables t
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE s.name = 'appconfig'
        ORDER BY t.name
    """)
    
    print("\n" + "=" * 80)
    print("APPCONFIG SCHEMA TABLES CREATED:")
    print("=" * 80)
    for row in cursor.fetchall():
        print(f"  {row[0]}.{row[1]} ({row[2]} columns)")
    
    # Verify data inserted
    cursor.execute("SELECT COUNT(*) FROM appconfig.tenants")
    tenant_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM appconfig.selection_config")
    selection_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM appconfig.signal_weights")
    weights_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM appconfig.branch_city_mapping")
    mapping_count = cursor.fetchone()[0]
    
    print("\n" + "=" * 80)
    print("DATA VERIFICATION:")
    print("=" * 80)
    print(f"  Tenants: {tenant_count}")
    print(f"  Selection Config: {selection_count}")
    print(f"  Signal Weights: {weights_count}")
    print(f"  Branch City Mapping: {mapping_count}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ CHUNK 2 - Schema Creation COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
