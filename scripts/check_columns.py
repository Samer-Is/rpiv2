"""Check column names in Rental.Contract"""
import pyodbc
conn = pyodbc.connect(
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost;Database=eJarDbSTGLite;Trusted_Connection=yes;"
)
cursor = conn.cursor()
cursor.execute("""
    SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'Rental' AND TABLE_NAME = 'Contract'
    ORDER BY ORDINAL_POSITION
""")
print("Columns in Rental.Contract:")
for row in cursor.fetchall():
    print(f"  {row[0]}")
conn.close()
