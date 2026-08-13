import os
import pandas as pd


NAUKRI_FILE = "data/cleaned_naukri_applicants.csv"
GIG_FILE = "data/cleaned_gig_workers.csv"
CBNEXUS_FILE = "data/cleaned_cbnexus_contacts.csv"

REPORT_DIR = "reports"

MATCH_FILE = os.path.join(
    REPORT_DIR,
    "entity_matches.csv",
)

CANDIDATE_FILE = os.path.join(
    REPORT_DIR,
    "entity_candidates.csv",
)

TRANSITIVE_FILE = os.path.join(
    REPORT_DIR,
    "entity_transitive_matches.csv",
)

SUMMARY_FILE = os.path.join(
    REPORT_DIR,
    "entity_resolution_summary.csv",
)


def load_data():
    """Load cleaned datasets and assign stable source record IDs."""

    naukri = pd.read_csv(NAUKRI_FILE)
    gig = pd.read_csv(GIG_FILE)
    cbnexus = pd.read_csv(CBNEXUS_FILE)

    naukri.insert(
        0,
        "source_record_id",
        [
            f"NAUKRI_{i:03d}"
            for i in range(1, len(naukri) + 1)
        ],
    )

    gig.insert(
        0,
        "source_record_id",
        [
            f"GIG_{i:03d}"
            for i in range(1, len(gig) + 1)
        ],
    )

    cbnexus.insert(
        0,
        "source_record_id",
        [
            f"CBN_{i:03d}"
            for i in range(1, len(cbnexus) + 1)
        ],
    )

    return naukri, gig, cbnexus


def create_naukri_gig_matches(naukri, gig):
    """Match Naukri and Gig Workers using exact email."""

    matches = naukri.merge(
        gig,
        left_on="Email",
        right_on="email_id",
        how="inner",
        suffixes=("_naukri", "_gig"),
    )

    if matches.empty:
        return pd.DataFrame()

    return pd.DataFrame(
        {
            "source_a": "naukri",
            "source_a_id": matches[
                "source_record_id_naukri"
            ].values,
            "source_b": "gig_workers",
            "source_b_id": matches[
                "source_record_id_gig"
            ].values,
            "name_a": matches[
                "Full Name"
            ].values,
            "name_b": matches[
                "worker_name"
            ].values,
            "identifier": matches[
                "Email"
            ].values,
            "match_method": "email",
            "confidence": "HIGH",
        }
    )


def create_naukri_cbnexus_matches(naukri, cbnexus):
    """Match Naukri and CBNexus using normalized phone."""

    matches = naukri.merge(
        cbnexus,
        left_on="Phone",
        right_on="Phone Number",
        how="inner",
        suffixes=("_naukri", "_cbnexus"),
    )

    if matches.empty:
        return pd.DataFrame()

    return pd.DataFrame(
        {
            "source_a": "naukri",
            "source_a_id": matches[
                "source_record_id_naukri"
            ].values,
            "source_b": "cbnexus",
            "source_b_id": matches[
                "source_record_id_cbnexus"
            ].values,
            "name_a": matches[
                "Full Name"
            ].values,
            "name_b": matches[
                "Name"
            ].values,
            "identifier": matches[
                "Phone"
            ].astype(str).values,
            "match_method": "phone",
            "confidence": "HIGH",
        }
    )


def create_gig_cbnexus_candidates(gig, cbnexus):
    """
    Generate Gig-CBNexus candidates using name + city.

    Name + city alone is not sufficient for automatic merging.
    """

    candidates = gig.merge(
        cbnexus,
        left_on=["worker_name", "location"],
        right_on=["Name", "City"],
        how="inner",
        suffixes=("_gig", "_cbnexus"),
    )

    if candidates.empty:
        return pd.DataFrame()

    return pd.DataFrame(
        {
            "source_a": "gig_workers",
            "source_a_id": candidates[
                "source_record_id_gig"
            ].values,
            "source_b": "cbnexus",
            "source_b_id": candidates[
                "source_record_id_cbnexus"
            ].values,
            "name_a": candidates[
                "worker_name"
            ].values,
            "name_b": candidates[
                "Name"
            ].values,
            "identifier": candidates[
                "worker_name"
            ].values,
            "match_method": "name+city",
            "confidence": "CANDIDATE",
        }
    )


def create_transitive_matches(
    naukri,
    gig,
    cbnexus,
    candidates,
):
    """
    Promote Gig-CBNexus candidates to HIGH confidence
    when both records are connected to the same Naukri
    record through strong identifiers.

    Naukri --email--> Gig
    Naukri --phone--> CBNexus

    Therefore:

    Gig <--> CBNexus
    """

    if candidates.empty:
        return pd.DataFrame()

    # Naukri -> Gig using email
    naukri_gig = naukri.merge(
        gig,
        left_on="Email",
        right_on="email_id",
        how="inner",
        suffixes=("_naukri", "_gig"),
    )

    # Naukri -> CBNexus using phone
    naukri_cbnexus = naukri.merge(
        cbnexus,
        left_on="Phone",
        right_on="Phone Number",
        how="inner",
        suffixes=("_naukri", "_cbnexus"),
    )

    if naukri_gig.empty or naukri_cbnexus.empty:
        return pd.DataFrame()

    # Join both relationships through Naukri
    bridge = naukri_gig.merge(
        naukri_cbnexus,
        on="source_record_id_naukri",
        how="inner",
        suffixes=("_gig", "_cbnexus"),
    )

    if bridge.empty:
        return pd.DataFrame()

    bridge_pairs = bridge[
        [
            "source_record_id_gig",
            "source_record_id_cbnexus",
        ]
    ].drop_duplicates()

    # Only promote pairs already present as candidates
    promoted = candidates.merge(
        bridge_pairs,
        left_on=[
            "source_a_id",
            "source_b_id",
        ],
        right_on=[
            "source_record_id_gig",
            "source_record_id_cbnexus",
        ],
        how="inner",
    )

    if promoted.empty:
        return pd.DataFrame()

    return pd.DataFrame(
        {
            "source_a": "gig_workers",
            "source_a_id": promoted[
                "source_a_id"
            ].values,
            "source_b": "cbnexus",
            "source_b_id": promoted[
                "source_b_id"
            ].values,
            "name_a": promoted[
                "name_a"
            ].values,
            "name_b": promoted[
                "name_b"
            ].values,
            "identifier": promoted[
                "identifier"
            ].values,
            "match_method": "naukri_bridge",
            "confidence": "HIGH",
        }
    )


def remove_promoted_candidates(
    candidates,
    transitive_matches,
):
    """Remove candidates that were promoted to HIGH confidence."""

    if candidates.empty:
        return candidates.copy()

    if transitive_matches.empty:
        return candidates.copy()

    promoted_pairs = transitive_matches[
        [
            "source_a_id",
            "source_b_id",
        ]
    ].drop_duplicates()

    remaining = candidates.merge(
        promoted_pairs,
        on=[
            "source_a_id",
            "source_b_id",
        ],
        how="left",
        indicator=True,
    )

    remaining = remaining[
        remaining["_merge"] == "left_only"
    ].drop(
        columns="_merge"
    )

    return remaining


def create_summary(
    naukri,
    gig,
    cbnexus,
    direct_matches,
    initial_candidates,
    transitive_matches,
    remaining_candidates,
):
    """Create an auditable entity-resolution summary."""

    summary = pd.DataFrame(
        [
            {
                "metric": "Naukri records",
                "count": len(naukri),
            },
            {
                "metric": "Gig Worker records",
                "count": len(gig),
            },
            {
                "metric": "CBNexus records",
                "count": len(cbnexus),
            },
            {
                "metric": "Direct high-confidence matches",
                "count": len(direct_matches),
            },
            {
                "metric": "Initial Gig-CBNexus candidates",
                "count": len(initial_candidates),
            },
            {
                "metric": "Transitive high-confidence matches",
                "count": len(transitive_matches),
            },
            {
                "metric": "Remaining candidates requiring review",
                "count": len(remaining_candidates),
            },
        ]
    )

    return summary


def main():

    os.makedirs(
        REPORT_DIR,
        exist_ok=True,
    )

    # --------------------------------------------------
    # Load cleaned data
    # --------------------------------------------------

    naukri, gig, cbnexus = load_data()

    # --------------------------------------------------
    # Direct high-confidence matches
    # --------------------------------------------------

    naukri_gig = create_naukri_gig_matches(
        naukri,
        gig,
    )

    naukri_cbnexus = create_naukri_cbnexus_matches(
        naukri,
        cbnexus,
    )

    direct_matches = pd.concat(
        [
            naukri_gig,
            naukri_cbnexus,
        ],
        ignore_index=True,
    )

    # --------------------------------------------------
    # Initial Gig-CBNexus candidates
    # --------------------------------------------------

    initial_candidates = create_gig_cbnexus_candidates(
        gig,
        cbnexus,
    )

    # --------------------------------------------------
    # Transitive matches through Naukri
    # --------------------------------------------------

    transitive_matches = create_transitive_matches(
        naukri,
        gig,
        cbnexus,
        initial_candidates,
    )

    # --------------------------------------------------
    # Remove promoted candidates from review list
    # --------------------------------------------------

    remaining_candidates = remove_promoted_candidates(
        initial_candidates,
        transitive_matches,
    )

    # --------------------------------------------------
    # Create summary
    # --------------------------------------------------

    summary = create_summary(
        naukri,
        gig,
        cbnexus,
        direct_matches,
        initial_candidates,
        transitive_matches,
        remaining_candidates,
    )

    # --------------------------------------------------
    # Save reports
    # --------------------------------------------------

    direct_matches.to_csv(
        MATCH_FILE,
        index=False,
    )

    remaining_candidates.to_csv(
        CANDIDATE_FILE,
        index=False,
    )

    transitive_matches.to_csv(
        TRANSITIVE_FILE,
        index=False,
    )

    summary.to_csv(
        SUMMARY_FILE,
        index=False,
    )

    # --------------------------------------------------
    # Print summary
    # --------------------------------------------------

    print("=" * 60)
    print("ENTITY RESOLUTION SUMMARY")
    print("=" * 60)

    print(
        "Naukri-Gig high-confidence matches:",
        len(naukri_gig),
    )

    print(
        "Naukri-CBNexus high-confidence matches:",
        len(naukri_cbnexus),
    )

    print(
        "Initial Gig-CBNexus candidates:",
        len(initial_candidates),
    )

    print(
        "Gig-CBNexus transitive HIGH matches:",
        len(transitive_matches),
    )

    print(
        "Remaining candidates requiring review:",
        len(remaining_candidates),
    )

    print("\nReports saved:")

    print(
        f"- {MATCH_FILE}"
    )

    print(
        f"- {CANDIDATE_FILE}"
    )

    print(
        f"- {TRANSITIVE_FILE}"
    )

    print(
        f"- {SUMMARY_FILE}"
    )

    # --------------------------------------------------
    # Direct matches
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("HIGH-CONFIDENCE DIRECT MATCHES")
    print("=" * 60)

    if direct_matches.empty:
        print("No direct matches found.")
    else:
        print(
            direct_matches.to_string(
                index=False
            )
        )

    # --------------------------------------------------
    # Transitive matches
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("TRANSITIVE HIGH-CONFIDENCE MATCHES")
    print("=" * 60)

    if transitive_matches.empty:
        print("No transitive matches found.")
    else:
        print(
            transitive_matches.to_string(
                index=False
            )
        )

    # --------------------------------------------------
    # Remaining candidates
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("CANDIDATES REQUIRING REVIEW")
    print("=" * 60)

    if remaining_candidates.empty:
        print("No unresolved candidates.")
    else:
        print(
            remaining_candidates.to_string(
                index=False
            )
        )


if __name__ == "__main__":
    main()