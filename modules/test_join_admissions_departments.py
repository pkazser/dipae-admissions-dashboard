from database_manager import load_admissions_with_departments


df = load_admissions_with_departments(year=2024)

print("Σύνολο εγγραφών:")
print(len(df))

print()
print("Εγγραφές χωρίς αντιστοίχιση metadata:")
missing = df[df["department_code"].isna()]
print(len(missing))

if len(missing) > 0:
    print()
    print("Τμήματα που δεν αντιστοιχίστηκαν:")
    print(
        missing[
            [
                "ministry_department_code",
                "department_name_raw",
                "exam_category",
            ]
        ].drop_duplicates()
    )

print()
print("Πρώτες εγγραφές με metadata:")
print(
    df[
        [
            "year",
            "exam_category",
            "ministry_department_code",
            "department_code",
            "department_name_clean",
            "school",
            "city",
            "website",
            "final_positions",
            "admitted",
            "base_score",
        ]
    ].head(20)
)