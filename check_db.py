import sqlite3

# Connect to the database
conn = sqlite3.connect('data/navmed_radiation_exam.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print(f"Found {len(tables)} tables in the database:")
for table in tables:
    print(f"  - {table[0]}")

# Check sample data
try:
    cursor.execute("SELECT COUNT(*) FROM examinations")
    exam_count = cursor.fetchone()[0]
    print(f"\nExaminations table has {exam_count} records")
except Exception as e:
    print(f"Error checking examinations table: {e}")

conn.close()
print("Database check complete!") 