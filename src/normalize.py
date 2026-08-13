import re
import pandas as pd


def normalize_name(value):
    """Normalize a person's name for matching."""
    if pd.isna(value):
        return None

    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)

    return value.title()


def normalize_email(value):
    """Normalize an email address for matching."""
    if pd.isna(value):
        return None

    value = str(value).strip().lower()

    return value


def normalize_phone(value):
    """Normalize an Indian phone number to 10 digits."""
    if pd.isna(value):
        return None

    value = str(value).strip()

    # Remove common formatting characters
    value = re.sub(r"[\s+\-()]", "", value)

    # Remove country code 91
    if value.startswith("91") and len(value) == 12:
        value = value[2:]

    # Keep only valid 10-digit numbers
    if re.fullmatch(r"\d{10}", value):
        return value

    return None


def normalize_city(value):
    """Normalize city names."""
    if pd.isna(value):
        return None

    value = str(value).strip()

    return value.title()


def normalize_status(value):
    """Normalize Gig Worker status values."""
    if pd.isna(value):
        return None

    value = str(value).strip().lower()

    valid_statuses = {
        "active",
        "inactive",
        "paused",
    }

    if value in valid_statuses:
        return value

    return None


def normalize_verified(value):
    """Convert CBNexus verification values to boolean."""
    if pd.isna(value):
        return None

    value = str(value).strip().lower()

    if value in {"y", "yes", "true"}:
        return True

    if value in {"n", "no", "false"}:
        return False

    return None
def normalize_rate(value):
    """
    Parse Gig Worker rate into amount and period.

    Examples:
        1415/hr    -> (1415, "hour")
        15k/month  -> (15000, "month")
    """
    if pd.isna(value):
        return None, None

    value = str(value).strip().lower()

    hourly_match = re.fullmatch(r"(\d+(?:\.\d+)?)/hr", value)

    if hourly_match:
        amount = float(hourly_match.group(1))
        return amount, "hour"

    monthly_match = re.fullmatch(r"(\d+(?:\.\d+)?)k/month", value)

    if monthly_match:
        amount = float(monthly_match.group(1)) * 1000
        return amount, "month"

    return None, None
if __name__ == "__main__":
    print(normalize_name("  SAHIL MALHOTRA  "))
    print(normalize_email(" TANVI.GUPTA31@EXAMPLE.COM "))
    print(normalize_phone("+91-9000000131"))
    print(normalize_city(" pune "))
    print(normalize_status("ACTIVE"))
    print(normalize_verified("Yes"))

    print(normalize_rate("1415/hr"))
    print(normalize_rate("15k/month"))
def normalize_date(value):
    """Convert supported date formats to YYYY-MM-DD."""

    if pd.isna(value):
        return None

    value = str(value).strip()

    formats = [
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d %b %Y",
        "%d %B %Y",
    ]

    for date_format in formats:
        parsed_date = pd.to_datetime(
            value,
            format=date_format,
            errors="coerce",
        )

        if not pd.isna(parsed_date):
            return parsed_date.strftime("%Y-%m-%d")

    return None
print(normalize_date("24-07-2026"))
print(normalize_date("2026-08-08"))
print(normalize_date("7 Jul 2026"))