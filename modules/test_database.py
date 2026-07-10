from database_manager import initialize_database, preview_table, DATABASE_PATH


initialize_database()

print("Η βάση δημιουργήθηκε εδώ:")
print(DATABASE_PATH)

print()
print("Πρώτες γραμμές από τον πίνακα departments:")
df = preview_table("departments", limit=10)
print(df)

print()
print("Σύνολο τμημάτων στη βάση:")
print(len(preview_table("departments", limit=100)))