import pandas as pd

from normalize import (
    normalize_name,
    normalize_phone,
    normalize_city,
    normalize_verified,
    normalize_projects,
)


INPUT_FILE = "data/source3_cbnexus_contacts.csv"
OUTPUT_FILE = "data/cleaned_cbnexus_contacts.csv"


def clean_cbnexus():
    """Clean and normalize the CBNexus contact dataset."""

    df = pd.read_csv(INPUT_FILE)

    original_rows = len(df)

    # Detect the embedded header row before removing it.
    header_mask = df.apply(
        lambda row: (
            str(row["Name"]).strip().lower() == "name"
            and str(row["Phone Number"]).strip().lower()
            == "phone number"
            and str(row["City"]).strip().lower() == "city"
        ),
        axis=1,
    )

    header_rows_removed = int(header_mask.sum())

    # Remove embedded header rows.
    df = df[~header_mask].copy()

    # Normalize fields.
    df["Name"] = df["Name"].apply(
        normalize_name
    )

    df["Phone Number"] = df["Phone Number"].apply(
        normalize_phone
    )

    df["City"] = df["City"].apply(
        normalize_city
    )

    df["Verified"] = df["Verified"].apply(
        normalize_verified
    )

    df["Projects Completed"] = df[
        "Projects Completed"
    ].apply(
        normalize_projects
    )

    # Save cleaned dataset.
    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # Cleaning summary.
    print("=" * 60)
    print("CBNEXUS CLEANING SUMMARY")
    print("=" * 60)

    print(f"Original rows: {original_rows}")
    print(
        "Embedded header rows removed: "
        f"{header_rows_removed}"
    )
    print(f"Final rows: {len(df)}")

    print("\nVerified value counts:")
    print(
        df["Verified"]
        .value_counts(dropna=False)
        .to_string()
    )

    print("\nProjects Completed values:")
    print(
        df["Projects Completed"]
        .to_string(index=False)
    )

    print("\nCleaned file saved to:")
    print(OUTPUT_FILE)

    return df


if __name__ == "__main__":
    clean_cbnexus()
    