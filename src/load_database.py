import csv
import sqlite3
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MASTER_FILE = BASE_DIR / "data" / "master_entities.csv"
DATABASE_FILE = BASE_DIR / "data" / "consultbae.db"


# ============================================================
# DATABASE SCHEMA
# ============================================================

CREATE_ENTITIES_TABLE = """
CREATE TABLE IF NOT EXISTS entities (
    entity_id TEXT PRIMARY KEY,
    name TEXT,
    email TEXT UNIQUE,
    phone TEXT UNIQUE,
    city TEXT,
    experience_years REAL,
    current_ctc REAL,
    applied_date TEXT,
    naukri_skills TEXT,
    gig_rate TEXT,
    gig_rate_amount REAL,
    gig_rate_period TEXT,
    gig_status TEXT,
    gig_skills TEXT,
    verified INTEGER,
    projects_completed INTEGER
);
"""


CREATE_ENTITY_SOURCES_TABLE = """
CREATE TABLE IF NOT EXISTS entity_sources (
    entity_id TEXT NOT NULL,
    source TEXT NOT NULL,
    source_record_id TEXT NOT NULL,

    PRIMARY KEY (
        entity_id,
        source,
        source_record_id
    ),

    FOREIGN KEY (entity_id)
        REFERENCES entities(entity_id)
);
"""


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_value(value):
    """
    Convert CSV values representing missing data into None.
    """

    if value is None:
        return None

    value = value.strip()

    if value == "":
        return None

    if value.lower() in {
        "nan",
        "none",
        "nat",
        "<na>"
    }:
        return None

    return value


def to_float(value):
    """
    Safely convert a value to float.
    """

    value = clean_value(value)

    if value is None:
        return None

    try:
        return float(value)
    except ValueError:
        return None


def to_int(value):
    """
    Safely convert a value to integer.
    """

    value = clean_value(value)

    if value is None:
        return None

    try:
        return int(float(value))
    except ValueError:
        return None


def to_bool_int(value):
    """
    Convert boolean-like values to SQLite INTEGER.
    """

    value = clean_value(value)

    if value is None:
        return None

    value = value.lower()

    if value in {"true", "1", "yes"}:
        return 1

    if value in {"false", "0", "no"}:
        return 0

    return None


# ============================================================
# READ MASTER CSV
# ============================================================

def read_master_csv():

    if not MASTER_FILE.exists():
        raise FileNotFoundError(
            f"Master file not found:\n{MASTER_FILE}"
        )

    with open(
        MASTER_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        rows = list(reader)

    if not rows:
        raise ValueError(
            "master_entities.csv contains no records."
        )

    return rows


# ============================================================
# MAIN DATABASE LOADER
# ============================================================

def load_database():

    print("=" * 60)
    print("LOADING MASTER DATA INTO SQLITE")
    print("=" * 60)

    # --------------------------------------------------------
    # Read master data
    # --------------------------------------------------------

    rows = read_master_csv()

    print(f"Master records found: {len(rows)}")

    # --------------------------------------------------------
    # Connect to SQLite
    # --------------------------------------------------------

    connection = sqlite3.connect(DATABASE_FILE)

    cursor = connection.cursor()

    # Enable foreign keys
    cursor.execute(
        "PRAGMA foreign_keys = ON"
    )

    # --------------------------------------------------------
    # Create tables
    # --------------------------------------------------------

    cursor.execute(
        CREATE_ENTITIES_TABLE
    )

    cursor.execute(
        CREATE_ENTITY_SOURCES_TABLE
    )

    # --------------------------------------------------------
    # Clear old data
    #
    # Allows the script to be safely re-run.
    # --------------------------------------------------------

    cursor.execute(
        "DELETE FROM entity_sources"
    )

    cursor.execute(
        "DELETE FROM entities"
    )

    # --------------------------------------------------------
    # Insert entities
    # --------------------------------------------------------

    insert_entity = """
    INSERT INTO entities (
        entity_id,
        name,
        email,
        phone,
        city,
        experience_years,
        current_ctc,
        applied_date,
        naukri_skills,
        gig_rate,
        gig_rate_amount,
        gig_rate_period,
        gig_status,
        gig_skills,
        verified,
        projects_completed
    )
    VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?
    )
    """

    entity_count = 0

    for row in rows:

        values = (
            clean_value(row.get("entity_id")),
            clean_value(row.get("name")),
            clean_value(row.get("email")),
            clean_value(row.get("phone")),
            clean_value(row.get("city")),
            to_float(row.get("experience_years")),
            to_float(row.get("current_ctc")),
            clean_value(row.get("applied_date")),
            clean_value(row.get("naukri_skills")),
            clean_value(row.get("gig_rate")),
            to_float(row.get("gig_rate_amount")),
            clean_value(row.get("gig_rate_period")),
            clean_value(row.get("gig_status")),
            clean_value(row.get("gig_skills")),
            to_bool_int(row.get("verified")),
            to_int(row.get("projects_completed")),
        )

        cursor.execute(
            insert_entity,
            values
        )

        entity_count += 1

    # --------------------------------------------------------
    # Insert source lineage
    # --------------------------------------------------------

    lineage_count = 0

    insert_lineage = """
    INSERT INTO entity_sources (
        entity_id,
        source,
        source_record_id
    )
    VALUES (?, ?, ?)
    """

    for row in rows:

        entity_id = clean_value(
            row.get("entity_id")
        )

        # ----------------------------------------------
        # Naukri
        # ----------------------------------------------

        naukri_ids = clean_value(
            row.get("naukri_record_ids")
        )

        if naukri_ids:

            for record_id in naukri_ids.split(","):

                record_id = record_id.strip()

                if record_id:

                    cursor.execute(
                        insert_lineage,
                        (
                            entity_id,
                            "naukri",
                            record_id
                        )
                    )

                    lineage_count += 1

        # ----------------------------------------------
        # Gig Workers
        # ----------------------------------------------

        gig_ids = clean_value(
            row.get("gig_record_ids")
        )

        if gig_ids:

            for record_id in gig_ids.split(","):

                record_id = record_id.strip()

                if record_id:

                    cursor.execute(
                        insert_lineage,
                        (
                            entity_id,
                            "gig_workers",
                            record_id
                        )
                    )

                    lineage_count += 1

        # ----------------------------------------------
        # CBNexus
        # ----------------------------------------------

        cbnexus_ids = clean_value(
            row.get("cbnexus_record_ids")
        )

        if cbnexus_ids:

            for record_id in cbnexus_ids.split(","):

                record_id = record_id.strip()

                if record_id:

                    cursor.execute(
                        insert_lineage,
                        (
                            entity_id,
                            "cbnexus",
                            record_id
                        )
                    )

                    lineage_count += 1

    # --------------------------------------------------------
    # Commit
    # --------------------------------------------------------

    connection.commit()

    # ========================================================
    # VALIDATION
    # ========================================================

    print()
    print("DATABASE VALIDATION")
    print("-" * 60)

    database_entities = cursor.execute(
        """
        SELECT COUNT(*)
        FROM entities
        """
    ).fetchone()[0]

    database_lineage = cursor.execute(
        """
        SELECT COUNT(*)
        FROM entity_sources
        """
    ).fetchone()[0]

    print(
        f"Entities inserted: {database_entities}"
    )

    print(
        f"Source lineage records: {database_lineage}"
    )

    # --------------------------------------------------------
    # Duplicate email check
    # --------------------------------------------------------

    duplicate_emails = cursor.execute(
        """
        SELECT email, COUNT(*)
        FROM entities
        WHERE email IS NOT NULL
        GROUP BY email
        HAVING COUNT(*) > 1
        """
    ).fetchall()

    # --------------------------------------------------------
    # Duplicate phone check
    # --------------------------------------------------------

    duplicate_phones = cursor.execute(
        """
        SELECT phone, COUNT(*)
        FROM entities
        WHERE phone IS NOT NULL
        GROUP BY phone
        HAVING COUNT(*) > 1
        """
    ).fetchall()

    print(
        f"Duplicate emails: {len(duplicate_emails)}"
    )

    print(
        f"Duplicate phones: {len(duplicate_phones)}"
    )

    # --------------------------------------------------------
    # Entity count validation
    # --------------------------------------------------------

    if database_entities != len(rows):

        connection.close()

        raise RuntimeError(
            "Database entity count does not match "
            "master_entities.csv."
        )

    # --------------------------------------------------------
    # Duplicate validation
    # --------------------------------------------------------

    if duplicate_emails:

        connection.close()

        raise RuntimeError(
            "Duplicate emails detected in database."
        )

    if duplicate_phones:

        connection.close()

        raise RuntimeError(
            "Duplicate phones detected in database."
        )

    # ========================================================
    # SUCCESS
    # ========================================================

    print()
    print(
        "DATABASE VALIDATION: PASSED"
    )

    print()
    print(
        "Database saved to:"
    )

    print(
        DATABASE_FILE
    )

    # ========================================================
    # DATABASE PREVIEW
    # ========================================================

    print()
    print("=" * 60)
    print("DATABASE PREVIEW")
    print("=" * 60)

    preview = cursor.execute(
        """
        SELECT
            entity_id,
            name,
            email,
            phone,
            city
        FROM entities
        LIMIT 10
        """
    ).fetchall()

    for record in preview:

        print(record)

    # --------------------------------------------------------
    # Close connection
    # --------------------------------------------------------

    connection.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    load_database()