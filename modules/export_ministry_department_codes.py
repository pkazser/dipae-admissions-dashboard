from pathlib import Path
import pandas as pd
from database_manager import load_admissions


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "data" / "reference" / "ministry_department_codes_2024.csv"


df = load_admissions(year=2024)

if df.empty:
    raise ValueError("Δεν υπάρχουν δεδομένα admissions για το 2024 στη βάση.")

codes_df = (
    df[
        [
            "ministry_department_code",
            "department_name_raw",
            "institution",
        ]
    ]
    .drop_duplicates()
    .sort_values("department_name_raw")
)

codes_df.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig"
)

print("Το αρχείο δημιουργήθηκε:")
print(OUTPUT_PATH)

print()
print("Σύνολο μοναδικών τμημάτων:")
print(len(codes_df))

print()
print(codes_df)