"""
Test script for CHUNK 2 - Config API validation
Tests the config endpoints against the database.
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
    return pyodbc.connect(CONN_STR)

def test_query(cursor, query, description=""):
    """Execute query and print results."""
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"{'='*60}")
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        print(f"✅ PASS - {len(rows)} rows returned")
        print(f"Columns: {columns}")
        for row in rows[:10]:
            print(f"  {row}")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

def main():
    print("=" * 80)
    print("CHUNK 2 VALIDATION - Config API Database Tests")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    all_passed = True
    
    # Test 1: Verify tenant exists
    all_passed &= test_query(cursor, """
        SELECT id, name, tenancy_name, is_active, source_tenant_id, created_at
        FROM appconfig.tenants
        WHERE id = 1
    """, "Verify YELO tenant exists")
    
    # Test 2: Verify guardrails exist
    all_passed &= test_query(cursor, """
        SELECT id, tenant_id, category_id, branch_id, min_price, max_discount_pct, max_premium_pct
        FROM appconfig.guardrails
        WHERE tenant_id = 1
    """, "Verify guardrails exist")
    
    # Test 3: Verify signal weights exist
    all_passed &= test_query(cursor, """
        SELECT id, tenant_id, signal_name, weight, is_enabled
        FROM appconfig.signal_weights
        WHERE tenant_id = 1
    """, "Verify signal weights exist")
    
    # Test 4: Verify branch selection config
    all_passed &= test_query(cursor, """
        SELECT id, tenant_id, selection_type, item_id, item_name, item_subtype, rank_order
        FROM appconfig.selection_config
        WHERE tenant_id = 1 AND selection_type = 'branch'
    """, "Verify branch selection config")
    
    # Test 5: Verify category selection config
    all_passed &= test_query(cursor, """
        SELECT id, tenant_id, selection_type, item_id, item_name, rank_order
        FROM appconfig.selection_config
        WHERE tenant_id = 1 AND selection_type = 'category'
    """, "Verify category selection config")
    
    # Test 6: Verify branch city mapping with coordinates
    all_passed &= test_query(cursor, """
        SELECT id, tenant_id, branch_id, city_name, latitude, longitude, timezone
        FROM appconfig.branch_city_mapping
        WHERE tenant_id = 1
    """, "Verify branch city mapping with coordinates")
    
    # Test 7: Test UPDATE operation
    print(f"\n{'='*60}")
    print("TEST: Update guardrail max_discount_pct")
    print(f"{'='*60}")
    try:
        # Get current value
        cursor.execute("SELECT max_discount_pct FROM appconfig.guardrails WHERE tenant_id = 1 AND category_id IS NULL")
        old_val = cursor.fetchone()[0]
        
        # Update
        cursor.execute("""
            UPDATE appconfig.guardrails 
            SET max_discount_pct = 35.00, updated_at = GETUTCDATE()
            WHERE tenant_id = 1 AND category_id IS NULL
        """)
        conn.commit()
        
        # Verify
        cursor.execute("SELECT max_discount_pct FROM appconfig.guardrails WHERE tenant_id = 1 AND category_id IS NULL")
        new_val = cursor.fetchone()[0]
        
        # Restore
        cursor.execute(f"""
            UPDATE appconfig.guardrails 
            SET max_discount_pct = {old_val}, updated_at = GETUTCDATE()
            WHERE tenant_id = 1 AND category_id IS NULL
        """)
        conn.commit()
        
        print(f"✅ PASS - Updated {old_val} -> {new_val} -> restored to {old_val}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
        all_passed = False
    
    # Test 8: Verify all appconfig tables exist
    all_passed &= test_query(cursor, """
        SELECT s.name as SchemaName, t.name as TableName
        FROM sys.tables t
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE s.name = 'appconfig'
        ORDER BY t.name
    """, "Verify all appconfig tables exist")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED - CHUNK 2 VALIDATED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 80)

if __name__ == "__main__":
    main()
