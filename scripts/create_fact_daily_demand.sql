-- =============================================================================
-- CHUNK 6: Feature Store - fact_daily_demand Table
-- =============================================================================
-- This table stores aggregated demand data for ML training and inference
-- Scope: MVP branches and categories for YELO tenant
-- Split: TRAIN (2023-2024-Q3) / VALIDATION (2024-Q4+)
-- =============================================================================

-- Drop if exists for clean slate
IF OBJECT_ID('dynamicpricing.fact_daily_demand', 'U') IS NOT NULL
    DROP TABLE dynamicpricing.fact_daily_demand;
GO

-- Create the fact table
CREATE TABLE dynamicpricing.fact_daily_demand (
    -- Primary key
    id                          INT IDENTITY(1,1) PRIMARY KEY,
    
    -- Dimension keys (grain: date × branch × category)
    tenant_id                   INT NOT NULL,
    demand_date                 DATE NOT NULL,
    branch_id                   INT NOT NULL,
    category_id                 INT NOT NULL,
    
    -- Target variable for ML
    executed_rentals_count      INT NOT NULL DEFAULT 0,
    
    -- Pricing features
    avg_base_price_paid         DECIMAL(18,4) NULL,
    min_base_price_paid         DECIMAL(18,4) NULL,
    max_base_price_paid         DECIMAL(18,4) NULL,
    
    -- Utilization features (from CHUNK 4 engine)
    utilization_contracts       DECIMAL(5,2) NULL,  -- % fleet rented
    utilization_bookings        DECIMAL(5,2) NULL,  -- % fleet booked
    
    -- Weather features (from CHUNK 5)
    temperature_max             DECIMAL(5,2) NULL,
    temperature_min             DECIMAL(5,2) NULL,
    temperature_avg             DECIMAL(5,2) NULL,
    precipitation_mm            DECIMAL(8,2) NULL,
    humidity_pct                DECIMAL(5,2) NULL,
    wind_speed_kmh              DECIMAL(6,2) NULL,
    
    -- Calendar features (from CHUNK 5)
    is_weekend                  BIT NOT NULL DEFAULT 0,
    is_public_holiday           BIT NOT NULL DEFAULT 0,
    is_school_holiday           BIT NOT NULL DEFAULT 0,
    is_religious_holiday        BIT NOT NULL DEFAULT 0,
    day_of_week                 TINYINT NOT NULL,       -- 0=Mon, 6=Sun
    day_of_month                TINYINT NOT NULL,
    week_of_year                TINYINT NOT NULL,
    month_of_year               TINYINT NOT NULL,
    quarter                     TINYINT NOT NULL,
    
    -- Event features (from CHUNK 5)
    event_score                 DECIMAL(5,2) NULL DEFAULT 0,  -- Aggregated event impact
    has_major_event             BIT NOT NULL DEFAULT 0,
    
    -- Lag features (will be computed in ML pipeline)
    rentals_lag_1d              INT NULL,               -- Yesterday's rentals
    rentals_lag_7d              INT NULL,               -- Same day last week
    rentals_rolling_7d_avg      DECIMAL(10,2) NULL,     -- 7-day moving average
    rentals_rolling_30d_avg     DECIMAL(10,2) NULL,     -- 30-day moving average
    
    -- ML split flag
    split_flag                  VARCHAR(20) NOT NULL DEFAULT 'TRAIN',
    
    -- Metadata
    created_at                  DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at                  DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    -- Constraints
    CONSTRAINT UQ_fact_daily_demand UNIQUE (tenant_id, demand_date, branch_id, category_id),
    CONSTRAINT CHK_split_flag CHECK (split_flag IN ('TRAIN', 'VALIDATION', 'TEST'))
);
GO

-- Create indexes for fast querying
CREATE INDEX IX_fact_daily_demand_date ON dynamicpricing.fact_daily_demand(demand_date);
CREATE INDEX IX_fact_daily_demand_branch ON dynamicpricing.fact_daily_demand(branch_id);
CREATE INDEX IX_fact_daily_demand_category ON dynamicpricing.fact_daily_demand(category_id);
CREATE INDEX IX_fact_daily_demand_split ON dynamicpricing.fact_daily_demand(split_flag);
CREATE INDEX IX_fact_daily_demand_tenant_date ON dynamicpricing.fact_daily_demand(tenant_id, demand_date);
GO

PRINT 'Table dynamicpricing.fact_daily_demand created successfully';
GO
