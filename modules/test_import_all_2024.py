from ministry_parser import parse_all_excels_from_zip, filter_dipae
from database_manager import initialize_database, save_admissions_dataframe, load_admissions, preview_table


year = 2024

initialize_database()

df_all, failed_files = parse_all_excels_from_zip(year)
df_dipae = filter_dipae(df_all)

if failed_files:
    print("Προσοχή: Κάποια αρχεία απέτυχαν:")
    print(failed_files)
else:
    print("Όλα τα αρχεία διαβάστηκαν επιτυχώς.")

save_admissions_dataframe(
    df=df_dipae,
    year=year
)

print()
print("Η μαζική εισαγωγή ολοκληρώθηκε.")
print("Έτος:", year)
print("Εγγραφές ΔΙ.ΠΑ.Ε. που αποθηκεύτηκαν:", len(df_dipae))

print()
print("Εγγραφές ανά κατηγορία:")
print(df_dipae["exam_category"].value_counts())

print()
print("Έλεγχος από τη βάση:")
df_db = load_admissions(year=year)
print("Εγγραφές στη βάση:", len(df_db))

print()
print("Κατηγορίες στη βάση:")
print(df_db["exam_category"].value_counts())

print()
print("Imports log:")
print(preview_table("imports_log", limit=10))