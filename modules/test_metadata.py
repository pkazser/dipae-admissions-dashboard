import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
METADATA_PATH = BASE_DIR / "data" / "reference" / "departments_metadata.csv"

df = pd.read_csv(METADATA_PATH, encoding="utf-8")

print(df.head())
print()
print("Σύνολο τμημάτων:", len(df))
print("Σχολές:", df["school"].nunique())
print("Πόλεις:", df["city"].unique())