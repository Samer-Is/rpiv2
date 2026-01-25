-- =============================================================================
-- CHUNK 7: Forecast Demand Table DDL
-- =============================================================================
-- Stores 30-day demand forecasts from multi-model trainer
-- =============================================================================

IF OBJECT_ID('dynamicpricing.forecast_demand_30d', 'U') IS NOT NULL
    DROP TABLE dynamicpricing.forecast_demand_30d;
GO

CREATE TABLE dynamicpricing.forecast_demand_30d (
    id                  INT IDENTITY(1,1) PRIMARY KEY,
    tenant_id           INT NOT NULL,
    run_date            DATE NOT NULL,           -- Date when forecast was generated
    branch_id           INT NOT NULL,
    category_id         INT NOT NULL,
    forecast_date       DATE NOT NULL,           -- Date being forecasted
    horizon_day         INT NOT NULL,            -- 1..30
    forecast_demand     DECIMAL(10,2) NOT NULL,  -- Predicted demand
    model_name          VARCHAR(50) NOT NULL,    -- e.g., 'lightgbm', 'lstm', 'naive'
    model_version       VARCHAR(50) NULL,        -- Model version/timestamp
    lower_bound         DECIMAL(10,2) NULL,      -- Prediction interval lower
    upper_bound         DECIMAL(10,2) NULL,      -- Prediction interval upper
    created_at          DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    CONSTRAINT UQ_forecast_demand UNIQUE (tenant_id, run_date, branch_id, category_id, forecast_date)
);
GO

CREATE INDEX IX_forecast_demand_run ON dynamicpricing.forecast_demand_30d(run_date);
CREATE INDEX IX_forecast_demand_branch ON dynamicpricing.forecast_demand_30d(branch_id, category_id);
CREATE INDEX IX_forecast_demand_tenant ON dynamicpricing.forecast_demand_30d(tenant_id, run_date);
GO

-- Model evaluation metrics table
IF OBJECT_ID('dynamicpricing.model_evaluation_metrics', 'U') IS NOT NULL
    DROP TABLE dynamicpricing.model_evaluation_metrics;
GO

CREATE TABLE dynamicpricing.model_evaluation_metrics (
    id                  INT IDENTITY(1,1) PRIMARY KEY,
    tenant_id           INT NOT NULL,
    model_name          VARCHAR(50) NOT NULL,
    model_version       VARCHAR(50) NULL,
    evaluation_date     DATE NOT NULL,
    mae                 DECIMAL(10,4) NOT NULL,  -- Mean Absolute Error
    mape                DECIMAL(10,4) NULL,      -- Mean Absolute Percentage Error
    smape               DECIMAL(10,4) NULL,      -- Symmetric MAPE
    rmse                DECIMAL(10,4) NULL,      -- Root Mean Squared Error
    is_best_model       BIT NOT NULL DEFAULT 0,  -- Is this the selected best model?
    training_samples    INT NULL,
    validation_samples  INT NULL,
    training_time_sec   DECIMAL(10,2) NULL,
    created_at          DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    CONSTRAINT UQ_model_eval UNIQUE (tenant_id, model_name, evaluation_date)
);
GO

-- Best model selection table
IF OBJECT_ID('dynamicpricing.best_model_selection', 'U') IS NOT NULL
    DROP TABLE dynamicpricing.best_model_selection;
GO

CREATE TABLE dynamicpricing.best_model_selection (
    id                  INT IDENTITY(1,1) PRIMARY KEY,
    tenant_id           INT NOT NULL,
    selected_model      VARCHAR(50) NOT NULL,
    selection_metric    VARCHAR(20) NOT NULL DEFAULT 'mae',
    metric_value        DECIMAL(10,4) NOT NULL,
    selection_date      DATE NOT NULL,
    model_path          VARCHAR(500) NULL,       -- Path to saved model file
    created_at          DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    CONSTRAINT UQ_best_model UNIQUE (tenant_id, selection_date)
);
GO

PRINT 'Forecast tables created successfully';
GO
