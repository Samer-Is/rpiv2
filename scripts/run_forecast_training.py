"""
Run Forecast Training - CHUNK 7
Train multi-model forecasting pipeline and generate 30-day forecasts
"""
import sys
sys.path.insert(0, "backend")

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Connection string
CONN_STR = (
    "mssql+pyodbc://localhost/eJarDbSTGLite"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
)

engine = create_engine(CONN_STR)
Session = sessionmaker(bind=engine)
db = Session()

print("=" * 70)
print("CHUNK 7: Multi-Model Forecast Training Pipeline")
print("=" * 70)

from app.ml.trainer import ForecastTrainingService

service = ForecastTrainingService(db)

print("\nRunning full training pipeline for YELO (tenant_id=1)...")
print("-" * 70)

try:
    result = service.run_full_pipeline(tenant_id=1)
    
    print("\n" + "=" * 70)
    print("TRAINING RESULTS")
    print("=" * 70)
    print(f"Tenant ID: {result['tenant_id']}")
    print(f"Training samples: {result['train_samples']:,}")
    print(f"Validation samples: {result['validation_samples']:,}")
    print(f"\nModels trained: {', '.join(result['models_trained'])}")
    
    print(f"\nTraining times:")
    for model, time_sec in result['training_times'].items():
        if time_sec is not None:
            print(f"  {model}: {time_sec:.2f}s")
        else:
            print(f"  {model}: FAILED")
    
    print(f"\nModel Metrics (MAE):")
    for model, metrics in result['metrics'].items():
        mae = metrics['mae']
        mape = metrics.get('mape', 'N/A')
        print(f"  {model}: MAE={mae:.2f}, MAPE={mape if mape == 'N/A' else f'{mape:.2f}%'}")
    
    print(f"\n🏆 BEST MODEL: {result['best_model']}")
    print(f"\nForecasts generated: {result['forecasts_generated']:,}")
    
    # Validation
    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)
    
    # Check forecasts not flatline
    from sqlalchemy import text
    
    forecast_stats = db.execute(text("""
        SELECT 
            MIN(forecast_demand) as min_demand,
            MAX(forecast_demand) as max_demand,
            AVG(forecast_demand) as avg_demand,
            STDEV(forecast_demand) as std_demand,
            COUNT(DISTINCT horizon_day) as horizon_days
        FROM dynamicpricing.forecast_demand_30d
        WHERE tenant_id = 1 AND run_date = CAST(GETDATE() AS DATE)
    """)).fetchone()
    
    print(f"\nForecast Statistics:")
    print(f"  Min demand: {float(forecast_stats[0]):.2f}")
    print(f"  Max demand: {float(forecast_stats[1]):.2f}")
    print(f"  Avg demand: {float(forecast_stats[2]):.2f}")
    print(f"  Std demand: {float(forecast_stats[3]):.2f}" if forecast_stats[3] else "  Std demand: N/A")
    print(f"  Horizon days: {forecast_stats[4]}")
    
    # Validation checks
    checks = []
    
    # Check 1: Models trained
    check1 = len(result['models_trained']) >= 2
    checks.append(("At least 2 models trained", check1, len(result['models_trained'])))
    
    # Check 2: Best model selected
    check2 = result['best_model'] is not None
    checks.append(("Best model selected", check2, result['best_model']))
    
    # Check 3: MAE vs naive baseline
    naive_mae = result['metrics'].get('seasonal_naive', {}).get('mae', float('inf'))
    best_mae = result['metrics'].get(result['best_model'], {}).get('mae', float('inf'))
    check3 = best_mae <= naive_mae * 1.5  # Allow some tolerance
    checks.append(("Best MAE reasonable vs baseline", check3, f"{best_mae:.2f} vs {naive_mae:.2f}"))
    
    # Check 4: Forecasts not flatline
    check4 = forecast_stats[3] is not None and float(forecast_stats[3]) > 0.1
    checks.append(("Forecasts not flatline", check4, f"std={float(forecast_stats[3]):.2f}" if forecast_stats[3] else "N/A"))
    
    # Check 5: Correct horizon (30 days)
    check5 = forecast_stats[4] == 30
    checks.append(("Correct horizon (30 days)", check5, forecast_stats[4]))
    
    print("\nValidation Checks:")
    all_passed = True
    for name, passed, value in checks:
        status = '✅' if passed else '❌'
        print(f"  {status} {name}: {value}")
        if not passed:
            all_passed = False
    
    print(f"\nOverall: {'✅ ALL PASSED' if all_passed else '❌ SOME FAILED'}")
    
except Exception as e:
    logger.error(f"Training failed: {e}")
    import traceback
    traceback.print_exc()

finally:
    db.close()

print("\n" + "=" * 70)
print("Training pipeline complete!")
print("=" * 70)
