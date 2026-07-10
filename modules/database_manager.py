import sqlite3
from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "admissions.db"
METADATA_PATH = BASE_DIR / "data" / "reference" / "departments_metadata.csv"


def get_connection():
    """
    Δημιουργεί σύνδεση με τη SQLite βάση.
    Αν δεν υπάρχει ο φάκελος database, τον δημιουργεί.
    """
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    return conn


def create_tables():
    """
    Δημιουργεί τους βασικούς πίνακες της εφαρμογής.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        department_code TEXT PRIMARY KEY,
        ministry_department_code TEXT,
        department_name TEXT NOT NULL,
        school TEXT,
        city TEXT,
        website TEXT,
        active INTEGER DEFAULT 1,
        notes TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year INTEGER NOT NULL,
        exam_category TEXT NOT NULL,
        ministry_department_code TEXT,
        institution TEXT,
        department_name_raw TEXT NOT NULL,
        admission_type TEXT,
        scientific_fields TEXT,
        initial_positions INTEGER,
        final_positions INTEGER,
        admitted INTEGER,
        coverage REAL,
        first_score REAL,
        base_score REAL,
        source_file TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS imports_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year INTEGER,
        source_file TEXT,
        imported_rows INTEGER,
        imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
        notes TEXT
    )
    """)

    conn.commit()
    conn.close()


def load_departments_metadata():
    """
    Φορτώνει το departments_metadata.csv στον πίνακα departments.
    Πρώτα καθαρίζει τον πίνακα και μετά εισάγει ξανά τα δεδομένα,
    χωρίς να καταστρέφει τη δομή του πίνακα.
    """

    df = pd.read_csv(METADATA_PATH, encoding="utf-8")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM departments")

    df.to_sql(
        "departments",
        conn,
        if_exists="append",
        index=False
    )

    conn.commit()
    conn.close()


def initialize_database():
    """
    Εκτελεί όλη την αρχικοποίηση της βάσης.
    """
    create_tables()
    load_departments_metadata()


def preview_table(table_name, limit=10):
    """
    Εμφανίζει τις πρώτες γραμμές ενός πίνακα για έλεγχο.
    """

    conn = get_connection()

    query = f"SELECT * FROM {table_name} LIMIT {limit}"
    df = pd.read_sql_query(query, conn)

    conn.close()

    return df


def load_departments():
    """
    Διαβάζει τον πίνακα departments από τη βάση.
    Χρησιμοποιείται από το Streamlit app.
    """

    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT
            department_code,
            ministry_department_code,
            department_name,
            school,
            city,
            website,
            active,
            notes
        FROM departments
        ORDER BY school, city, department_name
        """,
        conn
    )

    conn.close()

    return df


def load_admissions(year=None, exam_category=None):
    """
    Διαβάζει δεδομένα εισακτέων από τη βάση.
    Μπορεί προαιρετικά να φιλτράρει ανά έτος και κατηγορία.
    """

    conn = get_connection()

    query = """
        SELECT
            id,
            year,
            exam_category,
            ministry_department_code,
            institution,
            department_name_raw,
            admission_type,
            scientific_fields,
            initial_positions,
            final_positions,
            admitted,
            coverage,
            first_score,
            base_score,
            source_file,
            created_at
        FROM admissions
        WHERE 1 = 1
    """

    params = []

    if year is not None:
        query += " AND year = ?"
        params.append(year)

    if exam_category is not None:
        query += " AND exam_category = ?"
        params.append(exam_category)

    query += """
        ORDER BY year, exam_category, department_name_raw
    """

    df = pd.read_sql_query(query, conn, params=params)

    conn.close()

    return df


def save_admissions_data(df, year, exam_category, source_file):
    """
    Αποθηκεύει δεδομένα εισακτέων στον πίνακα admissions.
    Πριν την εισαγωγή, διαγράφει τυχόν παλιές εγγραφές
    για το ίδιο έτος, την ίδια κατηγορία και το ίδιο αρχείο.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM admissions
        WHERE year = ?
        AND exam_category = ?
        AND source_file = ?
        """,
        (year, exam_category, source_file)
    )

    columns_to_save = [
        "year",
        "exam_category",
        "ministry_department_code",
        "institution",
        "department_name_raw",
        "admission_type",
        "scientific_fields",
        "initial_positions",
        "final_positions",
        "admitted",
        "coverage",
        "first_score",
        "base_score",
        "source_file",
    ]

    df_to_save = df[columns_to_save].copy()

    df_to_save.to_sql(
        "admissions",
        conn,
        if_exists="append",
        index=False
    )

    cursor.execute(
        """
        INSERT INTO imports_log (
            year,
            source_file,
            imported_rows,
            notes
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            year,
            source_file,
            len(df_to_save),
            f"Κατηγορία: {exam_category}"
        )
    )

    conn.commit()
    conn.close()


def save_admissions_dataframe(df, year):
    """
    Αποθηκεύει μαζικά δεδομένα εισακτέων στον πίνακα admissions.

    Πριν την εισαγωγή, διαγράφει όλες τις παλιές εγγραφές
    του συγκεκριμένου έτους, ώστε να μη δημιουργούνται διπλότυπα
    όταν ξανατρέχουμε το import.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM admissions
        WHERE year = ?
        """,
        (year,)
    )

    columns_to_save = [
        "year",
        "exam_category",
        "ministry_department_code",
        "institution",
        "department_name_raw",
        "admission_type",
        "scientific_fields",
        "initial_positions",
        "final_positions",
        "admitted",
        "coverage",
        "first_score",
        "base_score",
        "source_file",
    ]

    df_to_save = df[columns_to_save].copy()

    df_to_save.to_sql(
        "admissions",
        conn,
        if_exists="append",
        index=False
    )

    cursor.execute(
        """
        INSERT INTO imports_log (
            year,
            source_file,
            imported_rows,
            notes
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            year,
            f"bases_{year}.zip",
            len(df_to_save),
            "Μαζική εισαγωγή όλων των κατηγοριών"
        )
    )

    conn.commit()
    conn.close()


def load_admissions_with_departments(year=None, exam_category=None):
    """
    Διαβάζει τα δεδομένα εισακτέων μαζί με τα metadata των Τμημάτων:
    Σχολή, πόλη, ιστοσελίδα και εσωτερικό κωδικό ΔΙΠΑΕ.
    """

    conn = get_connection()

    query = """
        SELECT
            a.id,
            a.year,
            a.exam_category,
            a.ministry_department_code,
            a.institution,
            a.department_name_raw,
            a.admission_type,
            a.scientific_fields,
            a.initial_positions,
            a.final_positions,
            a.admitted,
            a.coverage,
            a.first_score,
            a.base_score,
            a.source_file,
            a.created_at,

            d.department_code,
            d.department_name AS department_name_clean,
            d.school,
            d.city,
            d.website,
            d.active,
            d.notes

        FROM admissions a
        LEFT JOIN departments d
            ON CAST(a.ministry_department_code AS TEXT)
             = CAST(d.ministry_department_code AS TEXT)

        WHERE 1 = 1
    """

    params = []

    if year is not None:
        query += " AND a.year = ?"
        params.append(year)

    if exam_category is not None:
        query += " AND a.exam_category = ?"
        params.append(exam_category)

    query += """
        ORDER BY
            a.year,
            a.exam_category,
            d.school,
            d.city,
            a.department_name_raw
    """

    df = pd.read_sql_query(query, conn, params=params)

    conn.close()

    return df