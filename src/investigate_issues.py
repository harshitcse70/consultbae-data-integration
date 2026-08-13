import pandas as pd


DATA_FILES = {
    "naukri": "data/source1_naukri_applicants.csv",
    "gig": "data/source2_gig_workers.csv",
    "cbnexus": "data/source3_cbnexus_contacts.csv",
}


def load_data():
    """Load all source datasets."""
    naukri = pd.read_csv(DATA_FILES["naukri"])
    gig = pd.read_csv(DATA_FILES["gig"])
    cbnexus = pd.read_csv(DATA_FILES["cbnexus"])

    return naukri, gig, cbnexus


def print_section(title):
    """Print a consistent section heading."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def normalize_phone(phone):
    """Normalize Indian phone numbers for comparison."""
    if pd.isna(phone):
        return None

    phone = str(phone).strip()
    phone = phone.replace("+", "")
    phone = phone.replace("-", "")
    phone = phone.replace(" ", "")

    if phone.startswith("91") and len(phone) == 12:
        phone = phone[2:]

    return phone


def investigate_gig(gig):
    print_section("GIG WORKERS - ROWS WITH MISSING VALUES")

    missing_rows = gig[gig.isnull().any(axis=1)]
    print(missing_rows.to_string(index=False))

    print_section("GIG WORKERS - RATE VALUES")
    print(gig["rate"].to_string(index=False))

    print_section("GIG WORKERS - STATUS VALUES")
    print(gig["status"].value_counts(dropna=False))

    print_section("GIG WORKERS - SUSPICIOUS RATE ROW")
    suspicious_rate = gig[gig["rate"] == "Isha Chopra"]
    print(suspicious_rate.to_string(index=True))


def investigate_cbnexus(cbnexus):
    print_section("CBNEXUS - VERIFIED VALUES")
    print(cbnexus["Verified"].value_counts(dropna=False))

    print_section("CBNEXUS - PROJECT VALUES")
    print(cbnexus["Projects Completed"].to_string(index=False))

    print_section("CBNEXUS - EMBEDDED HEADER ROW")

    header_rows = cbnexus[
        (cbnexus["Name"] == "Name")
        | (cbnexus["Phone Number"] == "Phone Number")
    ]

    print(header_rows.to_string(index=False))


def investigate_naukri(naukri):
    print_section("NAUKRI - DUPLICATE PHONE NUMBERS")

    duplicate_phones = naukri[
        naukri["Phone"].duplicated(keep=False)
    ].sort_values("Phone")

    print(
        duplicate_phones[
            ["Full Name", "Email", "Phone", "City", "Skills"]
        ].to_string(index=False)
    )

    print_section("NAUKRI - NAME VARIATIONS")
    print(naukri["Full Name"].value_counts().to_string())

    print_section("NAUKRI - EMAIL VALUES")
    print(naukri["Email"].to_string(index=False))


def investigate_phone_matches(naukri, cbnexus):
    naukri = naukri.copy()
    cbnexus = cbnexus.copy()

    naukri["normalized_phone"] = naukri["Phone"].apply(
        normalize_phone
    )

    cbnexus["normalized_phone"] = cbnexus["Phone Number"].apply(
        normalize_phone
    )

    print_section("NAUKRI ↔ CBNEXUS - NORMALIZED PHONE MATCHES")

    phone_matches = naukri.merge(
        cbnexus,
        on="normalized_phone",
        how="inner",
    )

    print(
        phone_matches[
            [
                "Full Name",
                "Email",
                "Name",
                "Phone Number",
                "normalized_phone",
            ]
        ].to_string(index=False)
    )

    print("\nNumber of phone matches:", len(phone_matches))

    return naukri, cbnexus, phone_matches


def investigate_email_matches(naukri, gig):
    print_section("NAUKRI ↔ GIG WORKERS - EMAIL MATCHES")

    email_matches = naukri.merge(
        gig,
        left_on="Email",
        right_on="email_id",
        how="inner",
    )

    print(
        email_matches[
            ["Full Name", "Email", "worker_name", "email_id"]
        ].to_string(index=False)
    )

    print("\nNumber of email matches:", len(email_matches))

    print_section(
        "NAUKRI ↔ GIG - EMAIL MATCHES WITH NAME DIFFERENCES"
    )

    email_matches["naukri_name_norm"] = (
        email_matches["Full Name"]
        .str.strip()
        .str.lower()
    )

    email_matches["gig_name_norm"] = (
        email_matches["worker_name"]
        .str.strip()
        .str.lower()
    )

    different_names = email_matches[
        email_matches["naukri_name_norm"]
        != email_matches["gig_name_norm"]
    ]

    print(
        different_names[
            ["Full Name", "worker_name", "Email"]
        ].to_string(index=False)
    )

    print("\nName differences:", len(different_names))

    return email_matches


def main():
    naukri, gig, cbnexus = load_data()

    investigate_gig(gig)
    investigate_cbnexus(cbnexus)
    investigate_naukri(naukri)

    naukri, cbnexus, phone_matches = investigate_phone_matches(
        naukri,
        cbnexus,
    )

    email_matches = investigate_email_matches(
        naukri,
        gig,
    )


if __name__ == "__main__":
    main()