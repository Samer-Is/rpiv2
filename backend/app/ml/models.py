"""
Forecasting Models - CHUNK 7
Multi-model demand forecasting for dynamic pricing
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


@dataclass
class ForecastResult:
    """Result from a forecasting model."""
    forecast_date: date
    horizon_day: int
    forecast_demand: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None


@dataclass
class ModelMetrics:
    """Evaluation metrics for a model."""
    mae: float
    mape: Optional[float] = None
    smape: Optional[float] = None
    rmse: Optional[float] = None


class BaseForecastModel(ABC):
    """Abstract base class for all forecasting models."""
    
    name: str = "base"
    version: str = "1.0"
    
    @abstractmethod
    def fit(self, train_df: pd.DataFrame) -> None:
        """Train the model on historical data."""
        pass
    
    @abstractmethod
    def predict(self, horizon: int, context_df: pd.DataFrame = None) -> List[ForecastResult]:
        """Generate forecasts for the given horizon."""
        pass
    
    def evaluate(self, y_true: np.ndarray, y_pred: np.ndarray) -> ModelMetrics:
        """Compute evaluation metrics."""
        mae = np.mean(np.abs(y_true - y_pred))
        
        # MAPE (avoid division by zero)
        mask = y_true != 0
        if mask.sum() > 0:
            mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
        else:
            mape = None
        
        # sMAPE
        denominator = (np.abs(y_true) + np.abs(y_pred)) / 2
        mask = denominator != 0
        if mask.sum() > 0:
            smape = np.mean(np.abs(y_true[mask] - y_pred[mask]) / denominator[mask]) * 100
        else:
            smape = None
        
        # RMSE
        rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
        
        return ModelMetrics(mae=mae, mape=mape, smape=smape, rmse=rmse)


class SeasonalNaiveModel(BaseForecastModel):
    """
    Seasonal Naive baseline model.
    Forecasts using the value from the same day of the previous week.
    """
    
    name = "seasonal_naive"
    version = "1.0"
    
    def __init__(self, seasonal_period: int = 7):
        self.seasonal_period = seasonal_period
        self.history: Optional[np.ndarray] = None
        self.last_date: Optional[date] = None
    
    def fit(self, train_df: pd.DataFrame) -> None:
        """Store the last seasonal_period values for naive forecasting."""
        # Expect train_df to have 'demand_date' and 'executed_rentals_count'
        df = train_df.sort_values('demand_date')
        self.history = df['executed_rentals_count'].values
        self.last_date = df['demand_date'].max()
        logger.info(f"SeasonalNaive fitted with {len(self.history)} observations")
    
    def predict(self, horizon: int, context_df: pd.DataFrame = None) -> List[ForecastResult]:
        """Forecast using seasonal naive (same day last week)."""
        if self.history is None:
            raise ValueError("Model not fitted")
        
        results = []
        for h in range(1, horizon + 1):
            # Get value from same day last week (or cycle through history)
            idx = -self.seasonal_period + ((h - 1) % self.seasonal_period)
            if abs(idx) <= len(self.history):
                forecast = float(self.history[idx])
            else:
                forecast = float(np.mean(self.history[-self.seasonal_period:]))
            
            forecast_date = pd.Timestamp(self.last_date) + pd.Timedelta(days=h)
            results.append(ForecastResult(
                forecast_date=forecast_date.date(),
                horizon_day=h,
                forecast_demand=max(0, forecast)
            ))
        
        return results


class SimpleETSModel(BaseForecastModel):
    """
    Simple Exponential Smoothing model with trend and seasonality.
    Implements Holt-Winters using numpy (no statsmodels dependency).
    """
    
    name = "simple_ets"
    version = "1.0"
    
    def __init__(self, alpha: float = 0.3, beta: float = 0.1, gamma: float = 0.2, 
                 seasonal_period: int = 7):
        self.alpha = alpha  # Level smoothing
        self.beta = beta    # Trend smoothing
        self.gamma = gamma  # Seasonal smoothing
        self.seasonal_period = seasonal_period
        self.level: float = 0
        self.trend: float = 0
        self.seasonal: Optional[np.ndarray] = None
        self.last_date: Optional[date] = None
    
    def fit(self, train_df: pd.DataFrame) -> None:
        """Fit Holt-Winters exponential smoothing."""
        df = train_df.sort_values('demand_date')
        y = df['executed_rentals_count'].values.astype(float)
        n = len(y)
        m = self.seasonal_period
        
        if n < 2 * m:
            # Not enough data, use simple exponential smoothing
            self.level = np.mean(y)
            self.trend = 0
            self.seasonal = np.ones(m)
            self.last_date = df['demand_date'].max()
            return
        
        # Initialize components
        # Level: average of first season
        self.level = np.mean(y[:m])
        
        # Trend: average difference between seasons
        self.trend = (np.mean(y[m:2*m]) - np.mean(y[:m])) / m
        
        # Seasonal: ratio of first season to level
        self.seasonal = np.zeros(m)
        for i in range(m):
            self.seasonal[i] = y[i] / max(self.level, 1)
        
        # Smooth through the data
        for t in range(m, n):
            season_idx = t % m
            prev_level = self.level
            
            # Update level
            self.level = self.alpha * (y[t] / max(self.seasonal[season_idx], 0.01)) + \
                        (1 - self.alpha) * (self.level + self.trend)
            
            # Update trend
            self.trend = self.beta * (self.level - prev_level) + \
                        (1 - self.beta) * self.trend
            
            # Update seasonal
            self.seasonal[season_idx] = self.gamma * (y[t] / max(self.level, 1)) + \
                                       (1 - self.gamma) * self.seasonal[season_idx]
        
        self.last_date = df['demand_date'].max()
        logger.info(f"ETS fitted: level={self.level:.2f}, trend={self.trend:.2f}")
    
    def predict(self, horizon: int, context_df: pd.DataFrame = None) -> List[ForecastResult]:
        """Generate forecasts using Holt-Winters."""
        if self.seasonal is None:
            raise ValueError("Model not fitted")
        
        results = []
        for h in range(1, horizon + 1):
            season_idx = h % self.seasonal_period
            forecast = (self.level + h * self.trend) * self.seasonal[season_idx]
            
            forecast_date = pd.Timestamp(self.last_date) + pd.Timedelta(days=h)
            results.append(ForecastResult(
                forecast_date=forecast_date.date(),
                horizon_day=h,
                forecast_demand=max(0, forecast)
            ))
        
        return results


class LightGBMGlobalModel(BaseForecastModel):
    """
    LightGBM global model for multi-series forecasting.
    Trains on all branch×category combinations with entity embeddings.
    """
    
    name = "lightgbm"
    version = "1.0"
    
    def __init__(self, n_estimators: int = 100, max_depth: int = 6, 
                 learning_rate: float = 0.1):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.model = None
        self.feature_names: List[str] = []
        self.train_df: Optional[pd.DataFrame] = None
    
    def _create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features for LightGBM model."""
        features = pd.DataFrame()
        
        # Entity features
        features['branch_id'] = df['branch_id'].astype('category').cat.codes
        features['category_id'] = df['category_id'].astype('category').cat.codes
        
        # Time features
        features['day_of_week'] = df['day_of_week']
        features['day_of_month'] = df['day_of_month']
        features['week_of_year'] = df['week_of_year']
        features['month_of_year'] = df['month_of_year']
        features['quarter'] = df['quarter']
        features['is_weekend'] = df['is_weekend'].astype(int)
        
        # Calendar features
        if 'is_public_holiday' in df.columns:
            features['is_public_holiday'] = df['is_public_holiday'].astype(int)
        if 'is_religious_holiday' in df.columns:
            features['is_religious_holiday'] = df['is_religious_holiday'].astype(int)
        
        # Lag features
        if 'rentals_lag_1d' in df.columns:
            features['rentals_lag_1d'] = df['rentals_lag_1d'].fillna(0)
        if 'rentals_lag_7d' in df.columns:
            features['rentals_lag_7d'] = df['rentals_lag_7d'].fillna(0)
        if 'rentals_rolling_7d_avg' in df.columns:
            features['rentals_rolling_7d_avg'] = df['rentals_rolling_7d_avg'].fillna(0)
        if 'rentals_rolling_30d_avg' in df.columns:
            features['rentals_rolling_30d_avg'] = df['rentals_rolling_30d_avg'].fillna(0)
        
        # Weather features (if available)
        if 'temperature_avg' in df.columns:
            features['temperature_avg'] = df['temperature_avg'].fillna(30)  # Default for KSA
        if 'precipitation_mm' in df.columns:
            features['precipitation_mm'] = df['precipitation_mm'].fillna(0)
        
        # Event features
        if 'event_score' in df.columns:
            features['event_score'] = df['event_score'].fillna(0)
        if 'has_major_event' in df.columns:
            features['has_major_event'] = df['has_major_event'].astype(int)
        
        # Price features
        if 'avg_base_price_paid' in df.columns:
            features['avg_base_price_paid'] = df['avg_base_price_paid'].fillna(
                df['avg_base_price_paid'].median()
            )
        
        self.feature_names = list(features.columns)
        return features
    
    def fit(self, train_df: pd.DataFrame) -> None:
        """Train LightGBM model on feature store data."""
        try:
            import lightgbm as lgb
        except ImportError:
            logger.error("LightGBM not installed. Run: pip install lightgbm")
            raise
        
        # Create features
        X = self._create_features(train_df)
        y = train_df['executed_rentals_count'].values
        
        # Store train_df for later reference
        self.train_df = train_df.copy()
        
        # Train model
        self.model = lgb.LGBMRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            objective='regression',
            metric='mae',
            verbose=-1,
            random_state=42
        )
        
        self.model.fit(X, y)
        logger.info(f"LightGBM fitted with {len(X)} samples, {len(self.feature_names)} features")
    
    def predict(self, horizon: int, context_df: pd.DataFrame = None) -> List[ForecastResult]:
        """
        Generate forecasts for horizon days.
        context_df should contain the last known values for the series.
        """
        if self.model is None:
            raise ValueError("Model not fitted")
        
        if context_df is None:
            context_df = self.train_df
        
        results = []
        last_date = context_df['demand_date'].max()
        
        # Get unique branch/category combinations
        series = context_df[['branch_id', 'category_id']].drop_duplicates()
        
        for _, row in series.iterrows():
            branch_id = row['branch_id']
            category_id = row['category_id']
            
            # Get last known values for this series
            series_data = context_df[
                (context_df['branch_id'] == branch_id) & 
                (context_df['category_id'] == category_id)
            ].sort_values('demand_date')
            
            if len(series_data) == 0:
                continue
            
            # Generate forecasts for each horizon day
            for h in range(1, horizon + 1):
                forecast_date = pd.Timestamp(last_date) + pd.Timedelta(days=h)
                
                # Create feature row
                feature_row = self._create_forecast_features(
                    series_data, forecast_date, branch_id, category_id, h
                )
                
                # Predict
                X = pd.DataFrame([feature_row])[self.feature_names]
                forecast = float(self.model.predict(X)[0])
                
                results.append(ForecastResult(
                    forecast_date=forecast_date.date(),
                    horizon_day=h,
                    forecast_demand=max(0, forecast)
                ))
        
        return results
    
    def _create_forecast_features(
        self, series_data: pd.DataFrame, forecast_date: pd.Timestamp,
        branch_id: int, category_id: int, horizon: int
    ) -> Dict[str, Any]:
        """Create features for a single forecast point."""
        last_row = series_data.iloc[-1]
        
        features = {
            'branch_id': series_data['branch_id'].astype('category').cat.codes.iloc[0],
            'category_id': series_data['category_id'].astype('category').cat.codes.iloc[0],
            'day_of_week': forecast_date.dayofweek,
            'day_of_month': forecast_date.day,
            'week_of_year': forecast_date.isocalendar()[1],
            'month_of_year': forecast_date.month,
            'quarter': (forecast_date.month - 1) // 3 + 1,
            'is_weekend': 1 if forecast_date.dayofweek >= 5 else 0,
            'is_public_holiday': 0,  # Would need calendar lookup
            'is_religious_holiday': 0,
        }
        
        # Lag features (use last known values)
        if 'rentals_lag_1d' in self.feature_names:
            features['rentals_lag_1d'] = last_row.get('executed_rentals_count', 0)
        if 'rentals_lag_7d' in self.feature_names:
            if len(series_data) >= 7:
                features['rentals_lag_7d'] = series_data.iloc[-7]['executed_rentals_count']
            else:
                features['rentals_lag_7d'] = last_row.get('executed_rentals_count', 0)
        if 'rentals_rolling_7d_avg' in self.feature_names:
            features['rentals_rolling_7d_avg'] = series_data['executed_rentals_count'].tail(7).mean()
        if 'rentals_rolling_30d_avg' in self.feature_names:
            features['rentals_rolling_30d_avg'] = series_data['executed_rentals_count'].tail(30).mean()
        
        # Weather (default values for future)
        if 'temperature_avg' in self.feature_names:
            features['temperature_avg'] = 30.0
        if 'precipitation_mm' in self.feature_names:
            features['precipitation_mm'] = 0.0
        
        # Events
        if 'event_score' in self.feature_names:
            features['event_score'] = 0.0
        if 'has_major_event' in self.feature_names:
            features['has_major_event'] = 0
        
        # Price
        if 'avg_base_price_paid' in self.feature_names:
            features['avg_base_price_paid'] = last_row.get('avg_base_price_paid', 200)
        
        return features


class LSTMGlobalModel(BaseForecastModel):
    """
    PyTorch LSTM model for global multi-series forecasting.
    Uses CUDA if available.
    """
    
    name = "lstm"
    version = "1.0"
    
    def __init__(self, hidden_size: int = 64, num_layers: int = 2, 
                 sequence_length: int = 14, batch_size: int = 32,
                 epochs: int = 50, learning_rate: float = 0.001):
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.sequence_length = sequence_length
        self.batch_size = batch_size
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.model = None
        self.scaler = None
        self.device = None
        self.train_df: Optional[pd.DataFrame] = None
        self.feature_dim: int = 0
    
    def _check_gpu(self):
        """Check if CUDA is available."""
        try:
            import torch
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            if torch.cuda.is_available():
                logger.info(f"LSTM using GPU: {torch.cuda.get_device_name(0)}")
            else:
                logger.info("LSTM using CPU (no CUDA available)")
            return True
        except ImportError:
            logger.error("PyTorch not installed. Run: pip install torch")
            return False
    
    def _create_sequences(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for LSTM training."""
        # Group by branch×category
        sequences_X = []
        sequences_y = []
        
        for (branch_id, category_id), group in df.groupby(['branch_id', 'category_id']):
            group = group.sort_values('demand_date')
            
            # Features
            features = group[[
                'executed_rentals_count', 'day_of_week', 'is_weekend',
                'rentals_lag_1d', 'rentals_rolling_7d_avg'
            ]].fillna(0).values
            
            target = group['executed_rentals_count'].values
            
            # Create sequences
            for i in range(len(group) - self.sequence_length):
                X = features[i:i + self.sequence_length]
                y = target[i + self.sequence_length]
                sequences_X.append(X)
                sequences_y.append(y)
        
        return np.array(sequences_X), np.array(sequences_y)
    
    def fit(self, train_df: pd.DataFrame) -> None:
        """Train LSTM model."""
        if not self._check_gpu():
            raise ImportError("PyTorch required for LSTM model")
        
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader, TensorDataset
        
        self.train_df = train_df.copy()
        
        # Create sequences
        X, y = self._create_sequences(train_df)
        if len(X) == 0:
            raise ValueError("Not enough data for LSTM sequences")
        
        self.feature_dim = X.shape[2]
        
        # Normalize
        from sklearn.preprocessing import StandardScaler
        self.scaler = StandardScaler()
        X_flat = X.reshape(-1, self.feature_dim)
        X_flat = self.scaler.fit_transform(X_flat)
        X = X_flat.reshape(-1, self.sequence_length, self.feature_dim)
        
        # Convert to tensors
        X_tensor = torch.FloatTensor(X).to(self.device)
        y_tensor = torch.FloatTensor(y).to(self.device)
        
        # Create DataLoader
        dataset = TensorDataset(X_tensor, y_tensor)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        
        # Define LSTM model
        class LSTMModel(nn.Module):
            def __init__(self, input_size, hidden_size, num_layers):
                super().__init__()
                self.lstm = nn.LSTM(input_size, hidden_size, num_layers, 
                                   batch_first=True, dropout=0.2)
                self.fc = nn.Linear(hidden_size, 1)
            
            def forward(self, x):
                lstm_out, _ = self.lstm(x)
                out = self.fc(lstm_out[:, -1, :])
                return out.squeeze()
        
        self.model = LSTMModel(self.feature_dim, self.hidden_size, self.num_layers)
        self.model = self.model.to(self.device)
        
        # Training
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
        
        self.model.train()
        for epoch in range(self.epochs):
            total_loss = 0
            for batch_X, batch_y in dataloader:
                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            
            if (epoch + 1) % 10 == 0:
                avg_loss = total_loss / len(dataloader)
                logger.info(f"LSTM Epoch {epoch+1}/{self.epochs}, Loss: {avg_loss:.4f}")
        
        logger.info(f"LSTM fitted with {len(X)} sequences")
    
    def predict(self, horizon: int, context_df: pd.DataFrame = None) -> List[ForecastResult]:
        """Generate forecasts using LSTM."""
        if self.model is None:
            raise ValueError("Model not fitted")
        
        import torch
        
        if context_df is None:
            context_df = self.train_df
        
        results = []
        last_date = context_df['demand_date'].max()
        
        self.model.eval()
        with torch.no_grad():
            # Get unique series
            for (branch_id, category_id), group in context_df.groupby(['branch_id', 'category_id']):
                group = group.sort_values('demand_date')
                
                if len(group) < self.sequence_length:
                    continue
                
                # Get last sequence
                features = group[[
                    'executed_rentals_count', 'day_of_week', 'is_weekend',
                    'rentals_lag_1d', 'rentals_rolling_7d_avg'
                ]].fillna(0).values[-self.sequence_length:]
                
                # Normalize
                features_flat = self.scaler.transform(features)
                
                # Forecast iteratively
                sequence = features_flat.copy()
                
                for h in range(1, horizon + 1):
                    X = torch.FloatTensor(sequence).unsqueeze(0).to(self.device)
                    forecast = float(self.model(X).cpu().numpy())
                    
                    forecast_date = pd.Timestamp(last_date) + pd.Timedelta(days=h)
                    results.append(ForecastResult(
                        forecast_date=forecast_date.date(),
                        horizon_day=h,
                        forecast_demand=max(0, forecast)
                    ))
                    
                    # Update sequence for next prediction
                    new_row = np.array([forecast, forecast_date.dayofweek, 
                                       1 if forecast_date.dayofweek >= 5 else 0,
                                       forecast, np.mean(sequence[:, 0])])
                    new_row_scaled = self.scaler.transform(new_row.reshape(1, -1))
                    sequence = np.vstack([sequence[1:], new_row_scaled])
        
        return results
