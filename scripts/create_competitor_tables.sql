-- =============================================================================
-- CHUNK 8: Competitor Pricing Tables
-- =============================================================================
-- Tables for competitor price tracking and mapping configuration
-- =============================================================================

-- Competitor mapping config (internal category → competitor product)
IF OBJECT_ID('appconfig.competitor_mapping', 'U') IS NOT NULL
    DROP TABLE appconfig.competitor_mapping;
GO

CREATE TABLE appconfig.competitor_mapping (
    id                      INT IDENTITY(1,1) PRIMARY KEY,
    tenant_id               INT NOT NULL,
    category_id             INT NOT NULL,
    category_name           NVARCHAR(100) NOT NULL,
    competitor_vehicle_type NVARCHAR(100) NOT NULL,      -- e.g., 'economy', 'compact', 'suv'
    competitor_source       NVARCHAR(50) NOT NULL DEFAULT 'booking_com',
    weight                  DECIMAL(3,2) NOT NULL DEFAULT 1.0,  -- Weight for this mapping
    is_active               BIT NOT NULL DEFAULT 1,
    created_at              DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at              DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    CONSTRAINT UQ_competitor_mapping UNIQUE (tenant_id, category_id, competitor_vehicle_type)
);
GO

-- Insert default mappings for YELO categories
INSERT INTO appconfig.competitor_mapping 
(tenant_id, category_id, category_name, competitor_vehicle_type)
VALUES
(1, 27, 'Economy', 'economy'),
(1, 2, 'Compact', 'compact'),
(1, 3, 'Standard', 'standard'),
(1, 29, 'Full-size', 'fullsize'),
(1, 13, 'SUV', 'suv'),
(1, 1, 'Luxury', 'luxury');
GO

-- Competitor price cache table
IF OBJECT_ID('dynamicpricing.competitor_prices', 'U') IS NOT NULL
    DROP TABLE dynamicpricing.competitor_prices;
GO

CREATE TABLE dynamicpricing.competitor_prices (
    id                      INT IDENTITY(1,1) PRIMARY KEY,
    tenant_id               INT NOT NULL,
    branch_id               INT NOT NULL,
    city_name               NVARCHAR(100) NOT NULL,
    category_id             INT NOT NULL,
    price_date              DATE NOT NULL,
    competitor_name         NVARCHAR(100) NOT NULL,
    competitor_vehicle_type NVARCHAR(100) NOT NULL,
    daily_price             DECIMAL(18,4) NOT NULL,
    weekly_price            DECIMAL(18,4) NULL,
    monthly_price           DECIMAL(18,4) NULL,
    currency                NVARCHAR(10) NOT NULL DEFAULT 'SAR',
    data_source             NVARCHAR(50) NOT NULL DEFAULT 'booking_com',
    fetched_at              DATETIME2 NOT NULL DEFAULT GETDATE(),
    expires_at              DATETIME2 NOT NULL,
    
    CONSTRAINT UQ_competitor_prices UNIQUE (tenant_id, branch_id, category_id, price_date, competitor_name)
);
GO

CREATE INDEX IX_competitor_prices_date ON dynamicpricing.competitor_prices(price_date);
CREATE INDEX IX_competitor_prices_category ON dynamicpricing.competitor_prices(category_id);
CREATE INDEX IX_competitor_prices_expires ON dynamicpricing.competitor_prices(expires_at);
GO

-- Competitor index (aggregated) table
IF OBJECT_ID('dynamicpricing.competitor_index', 'U') IS NOT NULL
    DROP TABLE dynamicpricing.competitor_index;
GO

CREATE TABLE dynamicpricing.competitor_index (
    id                      INT IDENTITY(1,1) PRIMARY KEY,
    tenant_id               INT NOT NULL,
    branch_id               INT NOT NULL,
    category_id             INT NOT NULL,
    index_date              DATE NOT NULL,
    competitor_avg_price    DECIMAL(18,4) NOT NULL,      -- Avg of top 3 competitors
    competitor_min_price    DECIMAL(18,4) NULL,
    competitor_max_price    DECIMAL(18,4) NULL,
    competitors_count       INT NOT NULL DEFAULT 0,
    our_base_price          DECIMAL(18,4) NULL,
    price_position          DECIMAL(5,2) NULL,           -- Our price vs competitor avg (ratio)
    created_at              DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    CONSTRAINT UQ_competitor_index UNIQUE (tenant_id, branch_id, category_id, index_date)
);
GO

CREATE INDEX IX_competitor_index_date ON dynamicpricing.competitor_index(index_date);
GO

PRINT 'Competitor pricing tables created successfully';
GO
