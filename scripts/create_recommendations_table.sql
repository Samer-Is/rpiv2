-- CHUNK 9: Create recommendations_30d table for storing pricing recommendations
-- This table stores all pricing recommendations with explanations

USE eJarDbSTGLite;
GO

-- Drop table if exists for clean recreation
IF OBJECT_ID('dynamicpricing.recommendations_30d', 'U') IS NOT NULL
    DROP TABLE dynamicpricing.recommendations_30d;
GO

-- Create recommendations table
CREATE TABLE dynamicpricing.recommendations_30d (
    id INT IDENTITY(1,1) PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 1,
    run_date DATE NOT NULL,
    branch_id INT NOT NULL,
    category_id INT NOT NULL,
    forecast_date DATE NOT NULL,
    horizon_day INT NOT NULL,  -- 1 to 30
    
    -- Base prices (current)
    base_daily DECIMAL(10,2) NOT NULL,
    base_weekly DECIMAL(10,2) NOT NULL,
    base_monthly DECIMAL(10,2) NOT NULL,
    
    -- Recommended prices
    rec_daily DECIMAL(10,2) NOT NULL,
    rec_weekly DECIMAL(10,2) NOT NULL,
    rec_monthly DECIMAL(10,2) NOT NULL,
    
    -- Premium/discount percentage
    premium_discount_pct DECIMAL(8,4) NOT NULL,  -- positive = premium, negative = discount
    
    -- Signal values used in calculation
    utilization_signal DECIMAL(8,4) NULL,        -- utilization score
    forecast_signal DECIMAL(8,4) NULL,           -- forecast demand score
    competitor_signal DECIMAL(8,4) NULL,         -- competitor index score
    weather_signal DECIMAL(8,4) NULL,            -- weather impact score
    holiday_signal DECIMAL(8,4) NULL,            -- holiday/event impact score
    
    -- Weighted combination
    raw_adjustment_pct DECIMAL(8,4) NULL,        -- before guardrails
    
    -- Guardrail application
    guardrail_min_price DECIMAL(10,2) NULL,
    guardrail_max_discount_pct DECIMAL(8,4) NULL,
    guardrail_max_premium_pct DECIMAL(8,4) NULL,
    guardrail_applied BIT DEFAULT 0,             -- was adjustment clamped?
    
    -- Explainability
    explanation_text NVARCHAR(1000) NULL,
    
    -- Model tracking
    model_name NVARCHAR(100) NULL,
    model_version NVARCHAR(50) NULL,
    
    -- Approval workflow
    status NVARCHAR(20) DEFAULT 'pending',       -- pending, approved, skipped
    approved_at DATETIME NULL,
    approved_by NVARCHAR(100) NULL,
    
    -- Timestamps
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    
    -- Indexes and constraints
    CONSTRAINT FK_rec_tenant FOREIGN KEY (tenant_id) REFERENCES appconfig.tenants(id),
    CONSTRAINT UQ_rec_per_day UNIQUE (tenant_id, run_date, branch_id, category_id, forecast_date)
);
GO

-- Create indexes for performance
CREATE INDEX IX_rec_branch_date ON dynamicpricing.recommendations_30d (branch_id, forecast_date);
CREATE INDEX IX_rec_category ON dynamicpricing.recommendations_30d (category_id);
CREATE INDEX IX_rec_status ON dynamicpricing.recommendations_30d (status);
CREATE INDEX IX_rec_run_date ON dynamicpricing.recommendations_30d (run_date);
GO

-- Create view for latest recommendations per branch/category
CREATE OR ALTER VIEW dynamicpricing.vw_latest_recommendations AS
SELECT 
    r.*,
    b.BranchNameEn as branch_name,
    c.CategoryNameEn as category_name
FROM dynamicpricing.recommendations_30d r
INNER JOIN (
    SELECT tenant_id, branch_id, category_id, forecast_date, MAX(run_date) as latest_run
    FROM dynamicpricing.recommendations_30d
    GROUP BY tenant_id, branch_id, category_id, forecast_date
) latest ON r.tenant_id = latest.tenant_id 
         AND r.branch_id = latest.branch_id 
         AND r.category_id = latest.category_id
         AND r.forecast_date = latest.forecast_date
         AND r.run_date = latest.latest_run
LEFT JOIN eJarDbSTGLite.fleet.Branches b ON r.branch_id = b.BranchId
LEFT JOIN eJarDbSTGLite.fleet.CarCategories c ON r.category_id = c.CategoryId;
GO

PRINT 'CHUNK 9: recommendations_30d table created successfully';
GO
