import pandas as pd

from normalize import (
    normalize_name,
    normalize_email,
    normalize_phone,
    normalize_city,
    normalize_date,
)


INPUT_FILE = "data/source1_naukri_applicants.csv"
OUTPUT_FILE = "data/cleaned_naukri_applicants.csv"


def clean_naukri():
    """Clean and normalize the Naukri applicant dataset."""

    df = pd.read_csv(INPUT_FILE)

    original_rows = len(df)

    # Identify exact duplicate rows before removing them.
    duplicate_mask = df.duplicated(keep="first")

    duplicate_rows = df[duplicate_mask].copy()

    exact_duplicates_removed = len(duplicate_rows)

    # Remove only exact duplicate rows.
    # Potential identity duplicates are handled later
    # during entity resolution.
    df = df[~duplicate_mask].copy()

    # Normalize names.
    df["Full Name"] = df["Full Name"].apply(
        normalize_name
    )

    # Normalize email addresses.
    df["Email"] = df["Email"].apply(
        normalize_email
    )

    # Normalize phone numbers.
    df["Phone"] = df["Phone"].apply(
        normalize_phone
    )

    # Normalize city names.
    df["City"] = df["City"].apply(
        normalize_city
    )

    # Normalize application dates.
    df["Applied Date"] = df["Applied Date"].apply(
        normalize_date
    )

    # Save cleaned dataset.
    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # Print cleaning summary.
    print("=" * 60)
    print("NAUKRI CLEANING SUMMARY")
    print("=" * 60)

    print(f"Original rows: {original_rows}")

    print(
        "Exact duplicate rows removed: "
        f"{exact_duplicates_removed}"
    )

    print(f"Final rows: {len(df)}")

    print("\nExact duplicate rows removed:")

    if duplicate_rows.empty:
        print("None")
    else:
        print(
            duplicate_rows.to_string(
                index=False
            )
        )

    print("\nCleaned file saved to:")
    print(OUTPUT_FILE)

    return df


if __name__ == "__main__":
    clean_naukri()