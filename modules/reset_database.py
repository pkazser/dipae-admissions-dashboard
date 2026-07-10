from database_manager import get_connection, DATABASE_PATH


conn = get_connection()
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS departments")
cursor.execute("DROP TABLE IF EXISTS admissions")
cursor.execute("DROP TABLE IF EXISTS imports_log")

conn.commit()
conn.close()

print("Διαγράφηκαν οι πίνακες από τη βάση:")
print(DATABASE_PATH)