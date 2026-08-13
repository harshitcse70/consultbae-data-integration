import pandas as pd
from pathlib import Path


MASTER_FILE = Path("data/master_entities.csv")

EXPECTED_NAUKRI = 42
EXPECTED_GIG = 30
EXPECTED_CBNEXUS = 30


def get_ids(df, column):
    """
    Extract individual IDs from semicolon-separated ID fields.
    """
    return (
        df[column]
        .dropna()
        .astype(str)
        .str.split(";")
        .explode()
        .str.strip()
    )


def main():

    if not MASTER_FILE.exists():
        raise FileNotFoundError(
            f"Master file not found: {MASTER_FILE}"
        )

    df = pd.read_csv(MASTER_FILE)

    naukri_ids = get_ids(df, "naukri_record_ids")
    gig_ids = get_ids(df, "gig_record_ids")
    cbnexus_ids = get_ids(df, "cbnexus_record_ids")

    duplicate_emails = (
        df["email"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.lower()
        .duplicated()
        .sum()
    )

    duplicate_phones = (
        df["phone"]
        .dropna()
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .duplicated()
        .sum()
    )

    print("=" * 60)
    print("FINAL MASTER VALIDATION")
    print("=" * 60)

    print(f"Master entities: {len(df)}")

    print()
    print("SOURCE COVERAGE")
    print(f"Naukri:   {naukri_ids.nunique()} / {EXPECTED_NAUKRI}")
    print(f"Gig:      {gig_ids.nunique()} / {EXPECTED_GIG}")
    print(f"CBNexus:  {cbnexus_ids.nunique()} / {EXPECTED_CBNEXUS}")

    print()
    print("DUPLICATE CHECKS")
    print(f"Duplicate emails: {duplicate_emails}")
    print(f"Duplicate phones: {duplicate_phones}")

    print()
    print("ID DUPLICATE CHECKS")
    print(
        f"Duplicate Naukri IDs: "
        f"{naukri_ids.duplicated().sum()}"
    )
    print(
        f"Duplicate Gig IDs: "
        f"{gig_ids.duplicated().sum()}"
    )
    print(
        f"Duplicate CBNexus IDs: "
        f"{cbnexus_ids.duplicated().sum()}"
    )

    validation_passed = (
        len(df) == 60
        and naukri_ids.nunique() == EXPECTED_NAUKRI
        and gig_ids.nunique() == EXPECTED_GIG
        and cbnexus_ids.nunique() == EXPECTED_CBNEXUS
        and duplicate_emails == 0
        and duplicate_phones == 0
        and naukri_ids.duplicated().sum() == 0
        and gig_ids.duplicated().sum() == 0
        and cbnexus_ids.duplicated().sum() == 0
    )

    print()
    print("=" * 60)

    if validation_passed:
        print("FINAL VALIDATION: PASSED")
    else:
        print("FINAL VALIDATION: FAILED")

    print("=" * 60)

    if not validation_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()