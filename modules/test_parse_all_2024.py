from ministry_parser import parse_all_excels_from_zip, filter_dipae


year = 2024

df_all, failed_files = parse_all_excels_from_zip(year)
df_dipae = filter_dipae(df_all)

print("Σύνολο εγγραφών από όλα τα Excel:")
print(len(df_all))

print()
print("Σύνολο εγγραφών ΔΙ.ΠΑ.Ε.:")
print(len(df_dipae))

print()
print("Εγγραφές ΔΙ.ΠΑ.Ε. ανά κατηγορία:")
print(df_dipae["exam_category"].value_counts())

print()
print("Αρχεία που απέτυχαν:")
print(failed_files)

print()
print("Πρώτες εγγραφές:")
print(
    df_dipae[
        [
            "year",
            "exam_category",
            "ministry_department_code",
            "institution",
            "department_name_raw",
            "final_positions",
            "admitted",
            "coverage",
            "first_score",
            "base_score",
        ]
    ].head(30)
)