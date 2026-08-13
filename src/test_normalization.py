import pandas as pd

from normalize import (
    normalize_name,
    normalize_email,
    normalize_phone,
    normalize_city,
    normalize_status,
    normalize_verified,
    normalize_rate,
)


def test_naukri_normalization():
    df = pd.read_csv("data/source1_naukri_applicants.csv")

    df["name_normalized"] = df["Full Name"].apply(normalize_name)
    df["email_normalized"] = df["Email"].apply(normalize_email)
    df["phone_normalized"] = df["Phone"].apply(normalize_phone)
    df["city_normalized"] = df["City"].apply(normalize_city)

    print("\n" + "=" * 60)
    print("NAUKRI NORMALIZATION")
    print("=" * 60)

    print(
        df[
            [
                "Full Name",
                "name_normalized",
                "Phone",
                "phone_normalized",
            ]
        ].head(10).to_string(index=False)
    )


def test_gig_normalization():
    df = pd.read_csv("data/source2_gig_workers.csv")

    df["name_normalized"] = df["worker_name"].apply(normalize_name)
    df["email_normalized"] = df["email_id"].apply(normalize_email)
    df["city_normalized"] = df["location"].apply(normalize_city)
    df["status_normalized"] = df["status"].apply(normalize_status)

    # Normalize rate into amount and period
    df[["rate_amount", "rate_period"]] = pd.DataFrame(
        df["rate"].apply(normalize_rate).tolist(),
        index=df.index,
    )

    print("\n" + "=" * 60)
    print("GIG WORKER NORMALIZATION")
    print("=" * 60)

    print(
        df[
            [
                "worker_name",
                "name_normalized",
                "status",
                "status_normalized",
            ]
        ].head(10).to_string(index=False)
    )

    print("\n" + "=" * 60)
    print("GIG WORKER RATE NORMALIZATION")
    print("=" * 60)

    print(
        df[
            [
                "rate",
                "rate_amount",
                "rate_period",
            ]
        ].to_string(index=False)
    )


def test_cbnexus_normalization():
    df = pd.read_csv("data/source3_cbnexus_contacts.csv")

    df["name_normalized"] = df["Name"].apply(normalize_name)
    df["phone_normalized"] = df["Phone Number"].apply(normalize_phone)
    df["city_normalized"] = df["City"].apply(normalize_city)
    df["verified_normalized"] = df["Verified"].apply(
        normalize_verified
    )

    print("\n" + "=" * 60)
    print("CBNEXUS NORMALIZATION")
    print("=" * 60)

    print(
        df[
            [
                "Name",
                "name_normalized",
                "Phone Number",
                "phone_normalized",
                "Verified",
                "verified_normalized",
            ]
        ].head(15).to_string(index=False)
    )


if __name__ == "__main__":
    test_naukri_normalization()
    test_gig_normalization()
    test_cbnexus_normalization()