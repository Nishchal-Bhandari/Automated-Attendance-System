import sqlite3

# Connect to database
conn = sqlite3.connect('attendance_enhanced.db')
cursor = conn.cursor()

# Check what tables exist
print("=== TABLES IN DATABASE ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"Table: {table[0]}")

if not tables:
    print("No tables found!")
    conn.close()
    exit()

# Check if student table exists (could be 'student' or 'students')
table_name = None
for table in tables:
    if 'student' in table[0].lower():
        table_name = table[0]
        break

if table_name:
    print(f"\n=== STUDENTS IN TABLE '{table_name}' ===")
    cursor.execute(f'SELECT * FROM {table_name} LIMIT 5')
    rows = cursor.fetchall()
    
    # Get column names
    cursor.execute(f'PRAGMA table_info({table_name})')
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    print(f"Columns: {column_names}")
    
    for row in rows:
        print(f"Row: {row}")
    
    print(f"\nTotal rows in {table_name}: ", end="")
    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
    count = cursor.fetchone()[0]
    print(count)

conn.close()