from ministry_parser import parse_gel_day_from_zip, filter_dipae
from database_manager import initialize_database, save_admissions_data, preview_table


year = 2024
exam_category = "ΓΕΛ Ημερήσια"

initialize_database()

df_all = parse_gel_day_from_zip(year)
df_dipae = filter_dipae(df_all)

source_file = df_dipae["source_file"].iloc[0]

save_admissions_data(
    df=df_dipae,
    year=year,
    exam_category=exam_category,
    source_file=source_file
)

print("Η εισαγωγή ολοκληρώθηκε.")
print()
print("Έτος:", year)
print("Κατηγορία:", exam_category)
print("Αρχείο:", source_file)
print("Εγγραφές ΔΙ.ΠΑ.Ε. που αποθηκεύτηκαν:", len(df_dipae))

print()
print("Πρώτες εγγραφές από τον πίνακα admissions:")
print(preview_table("admissions", limit=10))

print()
print("Imports log:")
print(preview_table("imports_log", limit=10))