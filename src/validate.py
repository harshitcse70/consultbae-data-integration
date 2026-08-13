import re
import pandas as pd


VALID_STATUSES = {"active", "inactive", "paused"}


def is_valid_email(value):
    """Return True when value looks like a valid email address."""
    if pd.isna(value):
        return False

    value = str(value).strip()
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return bool(re.fullmatch(pattern, value))


def is_valid_phone(value):
    """Return True when value is a valid 10-digit phone number."""
    if pd.isna(value):
        return False

    value = str(value).strip()

    return bool(re.fullmatch(r"\d{10}", value))


def is_valid_rate(value):
    """Return True for supported Gig Worker rate formats."""
    if pd.isna(value):
        return False

    value = str(value).strip().lower()

    hourly = r"^\d+(?:\.\d+)?/hr$"
    monthly = r"^\d+(?:\.\d+)?k/month$"

    return bool(
        re.fullmatch(hourly, value)
        or re.fullmatch(monthly, value)
    )


def is_valid_status(value):
    """Return True for known Gig Worker statuses."""
    if pd.isna(value):
        return False

    value = str(value).strip().lower()

    return value in VALID_STATUSES


def is_empty_row(row):
    """Return True when every field in the row is missing."""
    return row.isna().all()


def is_cbnexus_header_row(row):
    """Detect the embedded CBNexus header row."""
    return (
        str(row["Name"]).strip().lower() == "name"
        and str(row["Phone Number"]).strip().lower() == "phone number"
        and str(row["City"]).strip().lower() == "city"
    )


def looks_like_name(value):
    """Return True when a value resembles a person's name."""
    if pd.isna(value):
        return False

    value = str(value).strip()

    return bool(
        re.fullmatch(
            r"[A-Za-z]+(?:\s+[A-Za-z]+)+",
            value,
        )
    )


def looks_like_skills(value):
    """Return True when a value looks like a comma-separated skill list."""
    if pd.isna(value):
        return False

    value = str(value).strip()

    return "," in value


def looks_like_city(value):
    """Return True when a value looks like a city name."""
    if pd.isna(value):
        return False

    value = str(value).strip()

    return bool(
        re.fullmatch(
            r"[A-Za-z]+(?:\s+[A-Za-z]+)*",
            value,
        )
    )


def detect_shifted_gig_row(row):
    """
    Detect a Gig Worker row whose values have shifted columns.
    """

    return (
        looks_like_skills(row["email_id"])
        and is_valid_email(row["worker_name"])
        and looks_like_name(row["rate"])
        and is_valid_rate(row["location"])
        and looks_like_city(row["status"])
        and is_valid_status(row["skill_tags"])
    )


def repair_shifted_gig_row(row):
    """
    Repair a Gig Worker row when its values are shifted.

    Returns a corrected dictionary.
    Returns None when the row does not match
    the shifted-row pattern.
    """

    if not detect_shifted_gig_row(row):
        return None

    return {
        "email_id": row["worker_name"],
        "worker_name": row["rate"],
        "rate": row["location"],
        "location": row["status"],
        "status": row["skill_tags"],
        "skill_tags": row["email_id"],
    }


def validate_gig_row(row):
    """
    Validate important fields in a Gig Worker row.
    """

    return {
        "valid_email": is_valid_email(row["email_id"]),
        "valid_rate": is_valid_rate(row["rate"]),
        "valid_status": is_valid_status(row["status"]),
    }


if __name__ == "__main__":
    gig = pd.read_csv(
        "data/source2_gig_workers.csv"
    )

    print("=" * 60)
    print("GIG WORKER VALIDATION")
    print("=" * 60)

    for index, row in gig.iterrows():

        if is_empty_row(row):
            print(f"\nRow {index}:")
            print("Detected: EMPTY ROW")
            continue

        result = validate_gig_row(row)

        if not all(result.values()):
            print(f"\nRow {index}:")
            print(row.to_dict())
            print(result)

            if detect_shifted_gig_row(row):
                print("Detected: SHIFTED GIG WORKER ROW")

                repaired_row = repair_shifted_gig_row(row)

                print("Repaired row:")
                print(repaired_row)