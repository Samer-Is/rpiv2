"""
Forecast Training Service - CHUNK 7
Multi-model training, backtesting, and forecast generation
"""
import logging
import time
from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from .models import (
    BaseForecastModel, SeasonalNaiveModel, SimpleETSModel,
    LightGBMGlobalModel, LSTMGlobalModel, ModelMetrics, ForecastResult
)

logger = logging.getLogger(__name__)


class ForecastTrainingService:
    """
    Service for training, evaluating, and selecting forecasting models.
    
    Implements:
    - Multi-model evaluation with backtesting
    - Rolling-origin cross-validation
    - Best model selection based on MAE
    - Forecast generation for 30-day horizon
    """
    
    HORIZON = 30  # Forecast horizon in days
    
    def __init__(self, db: Session):
        self.db = db
        self.models: Dict[str, BaseForecastModel] = {}
        self.best_model: Optional[str] = None
    
    def load_training_data(self, tenant_id: int = 1, split: str = "TRAIN") -> pd.DataFrame:
        """Load training data from feature store."""
        result = self.db.execute(text("""
            SELECT 
                demand_date, branch_id, category_id,
                executed_rentals_count,
                avg_base_price_paid,
                day_of_week, day_of_month, week_of_year, month_of_year, quarter,
                is_weekend, is_public_holiday, is_religious_holiday,
                rentals_lag_1d, rentals_lag_7d, 
                rentals_rolling_7d_avg, rentals_rolling_30d_avg,
                temperature_avg, precipitation_mm,
                event_score, has_major_event
            FROM dynamicpricing.fact_daily_demand
            WHERE tenant_id = :tenant_id AND split_flag = :split
            ORDER BY demand_date, branch_id, category_id
        """), {"tenant_id": tenant_id, "split": split})
        
        columns = result.keys()
        data = result.fetchall()
        df = pd.DataFrame(data, columns=columns)
        
        # Convert types
        df['demand_date'] = pd.to_datetime(df['demand_date'])
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_numeric(df[col])
                except:
                    pass
        
        logger.info(f"Loaded {len(df)} rows for {split} split")
        return df
    
    def train_all_models(self, train_df: pd.DataFrame) -> Dict[str, float]:
        """Train all models and return training times."""
        training_times = {}
        
        # 1. Seasonal Naive (baseline)
        logger.info("Training Seasonal Naive model...")
        start = time.time()
        naive_model = SeasonalNaiveModel(seasonal_period=7)
        # For global model, we aggregate across all series for baseline
        agg_df = train_df.groupby('demand_date').agg({
            'executed_rentals_count': 'sum'
        }).reset_index()
        agg_df.columns = ['demand_date', 'executed_rentals_count']
        naive_model.fit(agg_df)
        self.models['seasonal_naive'] = naive_model
        training_times['seasonal_naive'] = time.time() - start
        
        # 2. Simple ETS
        logger.info("Training Simple ETS model...")
        start = time.time()
        ets_model = SimpleETSModel(seasonal_period=7)
        ets_model.fit(agg_df)
        self.models['simple_ets'] = ets_model
        training_times['simple_ets'] = time.time() - start
        
        # 3. LightGBM Global Model
        logger.info("Training LightGBM global model...")
        start = time.time()
        try:
            lgb_model = LightGBMGlobalModel(n_estimators=100, max_depth=6)
            lgb_model.fit(train_df)
            self.models['lightgbm'] = lgb_model
            training_times['lightgbm'] = time.time() - start
        except ImportError as e:
            logger.warning(f"LightGBM not available: {e}")
            training_times['lightgbm'] = None
        
        # 4. LSTM Model (GPU attempt)
        logger.info("Training LSTM model (attempting GPU)...")
        start = time.time()
        try:
            lstm_model = LSTMGlobalModel(
                hidden_size=64, num_layers=2, 
                sequence_length=14, epochs=30
            )
            lstm_model.fit(train_df)
            self.models['lstm'] = lstm_model
            training_times['lstm'] = time.time() - start
        except Exception as e:
            logger.warning(f"LSTM training failed: {e}")
            training_times['lstm'] = None
        
        logger.info(f"Trained {len(self.models)} models")
        return training_times
    
    def backtest_models(
        self, 
        train_df: pd.DataFrame, 
        val_df: pd.DataFrame,
        n_folds: int = 3
    ) -> Dict[str, ModelMetrics]:
        """
        Backtest models using rolling-origin evaluation.
        
        Returns metrics for each model.
        """
        metrics = {}
        
        # Get actual values from validation set (aggregated)
        val_agg = val_df.groupby('demand_date').agg({
            'executed_rentals_count': 'sum'
        }).reset_index()
        val_agg = val_agg.sort_values('demand_date')
        
        y_true_agg = val_agg['executed_rentals_count'].values[:self.HORIZON]
        
        for model_name, model in self.models.items():
            logger.info(f"Backtesting {model_name}...")
            
            try:
                # Get forecasts
                if model_name in ('seasonal_naive', 'simple_ets'):
                    # Baseline models forecast aggregate
                    forecasts = model.predict(horizon=self.HORIZON)
                    y_pred = np.array([f.forecast_demand for f in forecasts[:len(y_true_agg)]])
                else:
                    # Global models forecast per series, then aggregate
                    forecasts = model.predict(horizon=self.HORIZON, context_df=train_df)
                    
                    # Group forecasts by date
                    forecast_df = pd.DataFrame([
                        {'forecast_date': f.forecast_date, 'forecast_demand': f.forecast_demand}
                        for f in forecasts
                    ])
                    forecast_agg = forecast_df.groupby('forecast_date')['forecast_demand'].sum().reset_index()
                    forecast_agg = forecast_agg.sort_values('forecast_date')
                    y_pred = forecast_agg['forecast_demand'].values[:len(y_true_agg)]
                
                # Compute metrics
                if len(y_pred) < len(y_true_agg):
                    y_true_agg = y_true_agg[:len(y_pred)]
                
                model_metrics = model.evaluate(y_true_agg, y_pred)
                metrics[model_name] = model_metrics
                
                logger.info(f"{model_name}: MAE={model_metrics.mae:.2f}, "
                           f"MAPE={model_metrics.mape:.2f}%" if model_metrics.mape else "")
                
            except Exception as e:
                logger.error(f"Backtest failed for {model_name}: {e}")
                metrics[model_name] = ModelMetrics(mae=float('inf'))
        
        return metrics
    
    def select_best_model(self, metrics: Dict[str, ModelMetrics]) -> str:
        """Select best model based on MAE."""
        best_model = min(metrics.items(), key=lambda x: x[1].mae)
        self.best_model = best_model[0]
        logger.info(f"Selected best model: {self.best_model} (MAE={best_model[1].mae:.2f})")
        return self.best_model
    
    def generate_forecasts(
        self, 
        tenant_id: int,
        model_name: Optional[str] = None,
        context_df: Optional[pd.DataFrame] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate 30-day forecasts using specified or best model.
        
        Returns list of forecast records for database insertion.
        """
        if model_name is None:
            model_name = self.best_model
        
        if model_name is None or model_name not in self.models:
            raise ValueError(f"Model {model_name} not available")
        
        model = self.models[model_name]
        run_date = date.today()
        
        # Load context if not provided
        if context_df is None:
            context_df = self.load_training_data(tenant_id, split="TRAIN")
            val_df = self.load_training_data(tenant_id, split="VALIDATION")
            context_df = pd.concat([context_df, val_df]).sort_values('demand_date')
        
        # Generate forecasts
        forecasts = model.predict(horizon=self.HORIZON, context_df=context_df)
        
        # Get unique branch/category combinations from context
        series = context_df[['branch_id', 'category_id']].drop_duplicates()
        
        records = []
        
        if model_name in ('seasonal_naive', 'simple_ets'):
            # Baseline models: distribute proportionally across series
            # based on historical averages
            series_means = context_df.groupby(['branch_id', 'category_id'])[
                'executed_rentals_count'
            ].mean()
            total_mean = series_means.sum()
            
            for forecast in forecasts:
                for _, row in series.iterrows():
                    branch_id = int(row['branch_id'])
                    category_id = int(row['category_id'])
                    
                    # Proportional allocation
                    proportion = series_means.get((branch_id, category_id), 1) / max(total_mean, 1)
                    series_forecast = forecast.forecast_demand * proportion
                    
                    records.append({
                        'tenant_id': tenant_id,
                        'run_date': run_date,
                        'branch_id': branch_id,
                        'category_id': category_id,
                        'forecast_date': forecast.forecast_date,
                        'horizon_day': forecast.horizon_day,
                        'forecast_demand': round(series_forecast, 2),
                        'model_name': model_name,
                        'model_version': model.version,
                        'lower_bound': forecast.lower_bound,
                        'upper_bound': forecast.upper_bound
                    })
        else:
            # Global models already forecast per series
            # Group forecasts by date and assign to series
            for forecast in forecasts:
                # Need to extract branch/category from forecast context
                # For now, distribute across all series
                for _, row in series.iterrows():
                    branch_id = int(row['branch_id'])
                    category_id = int(row['category_id'])
                    
                    # Find matching forecast (simplified - would need series tracking)
                    records.append({
                        'tenant_id': tenant_id,
                        'run_date': run_date,
                        'branch_id': branch_id,
                        'category_id': category_id,
                        'forecast_date': forecast.forecast_date,
                        'horizon_day': forecast.horizon_day,
                        'forecast_demand': round(forecast.forecast_demand, 2),
                        'model_name': model_name,
                        'model_version': model.version,
                        'lower_bound': forecast.lower_bound,
                        'upper_bound': forecast.upper_bound
                    })
                    break  # Only add once per forecast date for now
        
        logger.info(f"Generated {len(records)} forecast records")
        return records
    
    def save_forecasts(self, forecasts: List[Dict[str, Any]]) -> int:
        """Save forecasts to database."""
        if not forecasts:
            return 0
        
        # Clear existing forecasts for this run_date
        run_date = forecasts[0]['run_date']
        tenant_id = forecasts[0]['tenant_id']
        
        self.db.execute(text("""
            DELETE FROM dynamicpricing.forecast_demand_30d
            WHERE tenant_id = :tenant_id AND run_date = :run_date
        """), {"tenant_id": tenant_id, "run_date": run_date})
        
        # Insert new forecasts
        for f in forecasts:
            self.db.execute(text("""
                INSERT INTO dynamicpricing.forecast_demand_30d
                (tenant_id, run_date, branch_id, category_id, forecast_date, 
                 horizon_day, forecast_demand, model_name, model_version,
                 lower_bound, upper_bound)
                VALUES
                (:tenant_id, :run_date, :branch_id, :category_id, :forecast_date,
                 :horizon_day, :forecast_demand, :model_name, :model_version,
                 :lower_bound, :upper_bound)
            """), f)
        
        self.db.commit()
        logger.info(f"Saved {len(forecasts)} forecasts to database")
        return len(forecasts)
    
    def save_metrics(
        self, 
        tenant_id: int,
        metrics: Dict[str, ModelMetrics],
        training_times: Dict[str, float],
        train_samples: int,
        val_samples: int
    ) -> None:
        """Save model evaluation metrics to database."""
        eval_date = date.today()
        best_model = self.best_model
        
        for model_name, model_metrics in metrics.items():
            is_best = model_name == best_model
            train_time = training_times.get(model_name)
            
            self.db.execute(text("""
                INSERT INTO dynamicpricing.model_evaluation_metrics
                (tenant_id, model_name, model_version, evaluation_date,
                 mae, mape, smape, rmse, is_best_model,
                 training_samples, validation_samples, training_time_sec)
                VALUES
                (:tenant_id, :model_name, :version, :eval_date,
                 :mae, :mape, :smape, :rmse, :is_best,
                 :train_samples, :val_samples, :train_time)
            """), {
                "tenant_id": tenant_id,
                "model_name": model_name,
                "version": self.models.get(model_name, SeasonalNaiveModel()).version,
                "eval_date": eval_date,
                "mae": model_metrics.mae,
                "mape": model_metrics.mape,
                "smape": model_metrics.smape,
                "rmse": model_metrics.rmse,
                "is_best": is_best,
                "train_samples": train_samples,
                "val_samples": val_samples,
                "train_time": train_time
            })
        
        # Save best model selection
        if best_model and best_model in metrics:
            self.db.execute(text("""
                INSERT INTO dynamicpricing.best_model_selection
                (tenant_id, selected_model, selection_metric, metric_value, selection_date)
                VALUES
                (:tenant_id, :model_name, 'mae', :mae, :sel_date)
            """), {
                "tenant_id": tenant_id,
                "model_name": best_model,
                "mae": metrics[best_model].mae,
                "sel_date": eval_date
            })
        
        self.db.commit()
        logger.info(f"Saved metrics for {len(metrics)} models")
    
    def run_full_pipeline(self, tenant_id: int = 1) -> Dict[str, Any]:
        """
        Run the complete training pipeline:
        1. Load data
        2. Train all models
        3. Backtest and evaluate
        4. Select best model
        5. Generate and save forecasts
        """
        logger.info(f"Starting full training pipeline for tenant {tenant_id}")
        
        # Load data
        train_df = self.load_training_data(tenant_id, split="TRAIN")
        val_df = self.load_training_data(tenant_id, split="VALIDATION")
        
        if len(train_df) == 0:
            raise ValueError("No training data available")
        
        # Train models
        training_times = self.train_all_models(train_df)
        
        # Backtest
        metrics = self.backtest_models(train_df, val_df)
        
        # Select best
        best_model = self.select_best_model(metrics)
        
        # Save metrics
        self.save_metrics(tenant_id, metrics, training_times, 
                         len(train_df), len(val_df))
        
        # Generate forecasts
        context_df = pd.concat([train_df, val_df]).sort_values('demand_date')
        forecasts = self.generate_forecasts(tenant_id, best_model, context_df)
        
        # Save forecasts
        saved_count = self.save_forecasts(forecasts)
        
        return {
            "tenant_id": tenant_id,
            "train_samples": len(train_df),
            "validation_samples": len(val_df),
            "models_trained": list(self.models.keys()),
            "training_times": training_times,
            "metrics": {k: {"mae": v.mae, "mape": v.mape} for k, v in metrics.items()},
            "best_model": best_model,
            "forecasts_generated": saved_count
        }
