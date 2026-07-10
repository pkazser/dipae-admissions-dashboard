from ministry_parser import parse_gel_day_from_zip, filter_dipae


year = 2024

df_all = parse_gel_day_from_zip(year)
df_dipae = filter_dipae(df_all)

print("Σύνολο εγγραφών στο ΓΕΛ Ημερήσια:")
print(len(df_all))

print()
print("Εγγραφές ΔΙ.ΠΑ.Ε.:")
print(len(df_dipae))

print()
print("Στήλες:")
print(df_dipae.columns.tolist())

print()
print("Πρώτες εγγραφές ΔΙ.ΠΑ.Ε.:")
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
    ].head(20)
)