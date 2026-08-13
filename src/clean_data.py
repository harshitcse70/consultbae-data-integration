import pandas as pd

from normalize import (
    normalize_name,
    normalize_email,
    normalize_city,
    normalize_status,
    normalize_rate,
)

from validate import (
    is_empty_row,
    detect_shifted_gig_row,
    repair_shifted_gig_row,
)


INPUT_FILE = "data/source2_gig_workers.csv"
OUTPUT_FILE = "data/cleaned_gig_workers.csv"


def clean_gig_workers():
    """Clean and normalize the Gig Workers dataset."""

    df = pd.read_csv(INPUT_FILE)

    cleaned_rows = []
    removed_rows = []
    repaired_rows = []

    for index, row in df.iterrows():

        # Remove completely empty rows.
        if is_empty_row(row):
            removed_rows.append(index)
            continue

        was_repaired = False

        # Repair structurally shifted rows.
        if detect_shifted_gig_row(row):
            repaired_row = repair_shifted_gig_row(row)

            if repaired_row is not None:
                row = pd.Series(repaired_row)
                was_repaired = True
                repaired_rows.append(index)

        # Normalize fields.
        row["worker_name"] = normalize_name(row["worker_name"])
        row["email_id"] = normalize_email(row["email_id"])
        row["location"] = normalize_city(row["location"])
        row["status"] = normalize_status(row["status"])

        rate_amount, rate_period = normalize_rate(row["rate"])

        row["rate_amount"] = rate_amount
        row["rate_period"] = rate_period

        cleaned_rows.append(
            {
                "source_index": index,
                "was_repaired": was_repaired,
                "email_id": row["email_id"],
                "worker_name": row["worker_name"],
                "rate": row["rate"],
                "location": row["location"],
                "status": row["status"],
                "skill_tags": row["skill_tags"],
                "rate_amount": row["rate_amount"],
                "rate_period": row["rate_period"],
            }
        )

    cleaned_df = pd.DataFrame(cleaned_rows)

    # Identify repaired records that became exact duplicates
    # of an existing valid record after repair.
    data_columns = [
        "email_id",
        "worker_name",
        "rate",
        "location",
        "status",
        "skill_tags",
        "rate_amount",
        "rate_period",
    ]

    duplicate_mask = cleaned_df.duplicated(
        subset=data_columns,
        keep=False,
    )

    duplicate_groups = cleaned_df[duplicate_mask]

    repaired_duplicate_indexes = []

    for _, group in duplicate_groups.groupby(data_columns):
        repaired_records = group[group["was_repaired"]]

        if len(repaired_records) > 0 and len(group) > 1:
            repaired_duplicate_indexes.extend(
                repaired_records.index.tolist()
            )

    if repaired_duplicate_indexes:
        cleaned_df = cleaned_df.drop(
            repaired_duplicate_indexes
        )

    repaired_duplicates_removed = len(
        repaired_duplicate_indexes
    )

    # Remove internal processing columns before saving.
    cleaned_df = cleaned_df.drop(
        columns=["source_index", "was_repaired"]
    )

    cleaned_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("=" * 60)
    print("GIG WORKERS CLEANING SUMMARY")
    print("=" * 60)

    print(f"Original rows: {len(df)}")
    print(f"Removed empty rows: {len(removed_rows)}")
    print(f"Repaired rows: {len(repaired_rows)}")
    print(
        "Repair-created duplicates removed: "
        f"{repaired_duplicates_removed}"
    )
    print(f"Final rows: {len(cleaned_df)}")

    print("\nRemoved row indexes:")
    print(removed_rows)

    print("\nRepaired row indexes:")
    print(repaired_rows)

    print("\nCleaned file saved to:")
    print(OUTPUT_FILE)

    return cleaned_df


if __name__ == "__main__":
    clean_gig_workers()