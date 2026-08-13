import os
import pandas as pd


# ============================================================
# FILE PATHS
# ============================================================

NAUKRI_FILE = "data/cleaned_naukri_applicants.csv"
GIG_FILE = "data/cleaned_gig_workers.csv"
CBNEXUS_FILE = "data/cleaned_cbnexus_contacts.csv"

MATCH_FILE = "reports/entity_matches.csv"
TRANSITIVE_FILE = "reports/entity_transitive_matches.csv"
CANDIDATE_FILE = "reports/entity_candidates.csv"

OUTPUT_FILE = "data/master_entities.csv"


# ============================================================
# HELPERS
# ============================================================

def normalize_text(value):
    """Normalize text for comparison."""

    if pd.isna(value):
        return ""

    return str(value).strip().lower()


def first_valid(series):
    """Return the first non-empty value from a series."""

    for value in series:
        if pd.notna(value) and str(value).strip() != "":
            return value

    return pd.NA


def unique_values(series):
    """
    Return unique non-empty values as a semicolon-separated string.
    """

    values = []

    for value in series:

        if pd.notna(value) and str(value).strip() != "":
            value = str(value).strip()

            if value not in values:
                values.append(value)

    if not values:
        return pd.NA

    return "; ".join(values)


# ============================================================
# UNION-FIND
# ============================================================

class UnionFind:
    """Simple union-find structure for entity clustering."""

    def __init__(self):
        self.parent = {}

    def add(self, item):

        if item not in self.parent:
            self.parent[item] = item

    def find(self, item):

        self.add(item)

        if self.parent[item] != item:
            self.parent[item] = self.find(
                self.parent[item]
            )

        return self.parent[item]

    def union(self, a, b):

        root_a = self.find(a)
        root_b = self.find(b)

        if root_a != root_b:
            self.parent[root_b] = root_a


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    naukri = pd.read_csv(
        NAUKRI_FILE
    )

    gig = pd.read_csv(
        GIG_FILE
    )

    cbnexus = pd.read_csv(
        CBNEXUS_FILE
    )

    matches = pd.read_csv(
        MATCH_FILE
    )

    transitive_matches = pd.read_csv(
        TRANSITIVE_FILE
    )

    candidates = pd.read_csv(
        CANDIDATE_FILE
    )

    return (
        naukri,
        gig,
        cbnexus,
        matches,
        transitive_matches,
        candidates,
    )


# ============================================================
# CREATE SOURCE RECORD IDs
# ============================================================

def add_source_ids(
    naukri,
    gig,
    cbnexus,
):
    """
    Recreate the same stable IDs used by entity_resolution.py.
    """

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


# ============================================================
# SAME-SOURCE NAUKRI DUPLICATE DETECTION
# ============================================================

def add_naukri_duplicate_links(
    uf,
    naukri,
):
    """
    Connect duplicate Naukri records using strong evidence.

    Rules:

    1. Same normalized email + same phone
    2. Same normalized phone + same normalized name
    3. Same normalized phone + compatible abbreviated name

    Name alone is NEVER sufficient.
    """

    records = naukri.to_dict("records")

    for i in range(len(records)):

        for j in range(i + 1, len(records)):

            left = records[i]
            right = records[j]

            left_id = (
                f"naukri:{left['source_record_id']}"
            )

            right_id = (
                f"naukri:{right['source_record_id']}"
            )

            left_email = normalize_text(
                left.get("Email")
            )

            right_email = normalize_text(
                right.get("Email")
            )

            left_phone = normalize_text(
                left.get("Phone")
            )

            right_phone = normalize_text(
                right.get("Phone")
            )

            left_name = normalize_text(
                left.get("Full Name")
            )

            right_name = normalize_text(
                right.get("Full Name")
            )

            # ------------------------------------------------
            # Rule 1
            # Same email + same phone
            # ------------------------------------------------

            if (
                left_email
                and right_email
                and left_phone
                and right_phone
                and left_email == right_email
                and left_phone == right_phone
            ):

                uf.union(
                    left_id,
                    right_id,
                )

                continue

            # ------------------------------------------------
            # Rule 2
            # Same phone + same name
            # ------------------------------------------------

            if (
                left_phone
                and right_phone
                and left_phone == right_phone
                and left_name
                and right_name
                and left_name == right_name
            ):

                uf.union(
                    left_id,
                    right_id,
                )

                continue

            # ------------------------------------------------
            # Rule 3
            # Same phone + compatible abbreviated name
            #
            # Example:
            #
            # R. Verma
            # Rohit Verma
            # ------------------------------------------------

            if (
                left_phone
                and right_phone
                and left_phone == right_phone
                and left_name
                and right_name
            ):

                left_parts = left_name.split()
                right_parts = right_name.split()

                if len(left_parts) == len(right_parts):

                    compatible = True

                    for left_part, right_part in zip(
                        left_parts,
                        right_parts,
                    ):

                        if left_part == right_part:
                            continue

                        # Example:
                        # r + rohit
                        if (
                            len(left_part) == 1
                            and right_part.startswith(left_part)
                        ):
                            continue

                        # Reverse case
                        if (
                            len(right_part) == 1
                            and left_part.startswith(right_part)
                        ):
                            continue

                        compatible = False
                        break

                    if compatible:

                        uf.union(
                            left_id,
                            right_id,
                        )


# ============================================================
# BUILD ENTITY CONNECTIONS
# ============================================================

def build_entity_clusters(
    matches,
    transitive_matches,
    naukri,
):
    """
    Build connected components from:

    1. Direct HIGH-confidence matches
    2. Transitive HIGH-confidence matches
    3. Strong same-source Naukri duplicate relationships
    """

    uf = UnionFind()

    # --------------------------------------------------------
    # Direct HIGH-confidence matches
    # --------------------------------------------------------

    for _, row in matches.iterrows():

        source_a = (
            f"{row['source_a']}:{row['source_a_id']}"
        )

        source_b = (
            f"{row['source_b']}:{row['source_b_id']}"
        )

        uf.union(
            source_a,
            source_b,
        )

    # --------------------------------------------------------
    # Transitive HIGH-confidence matches
    # --------------------------------------------------------

    for _, row in transitive_matches.iterrows():

        source_a = (
            f"{row['source_a']}:{row['source_a_id']}"
        )

        source_b = (
            f"{row['source_b']}:{row['source_b_id']}"
        )

        uf.union(
            source_a,
            source_b,
        )

    # --------------------------------------------------------
    # Same-source Naukri duplicate consolidation
    # --------------------------------------------------------

    add_naukri_duplicate_links(
        uf,
        naukri,
    )

    # --------------------------------------------------------
    # Create clusters
    # --------------------------------------------------------

    clusters = {}

    for item in uf.parent:

        root = uf.find(item)

        if root not in clusters:
            clusters[root] = []

        clusters[root].append(item)

    return clusters


# ============================================================
# SOURCE LOOKUPS
# ============================================================

def create_lookups(
    naukri,
    gig,
    cbnexus,
):

    naukri_lookup = (
        naukri
        .set_index("source_record_id")
        .to_dict("index")
    )

    gig_lookup = (
        gig
        .set_index("source_record_id")
        .to_dict("index")
    )

    cbnexus_lookup = (
        cbnexus
        .set_index("source_record_id")
        .to_dict("index")
    )

    return (
        naukri_lookup,
        gig_lookup,
        cbnexus_lookup,
    )


# ============================================================
# BUILD MASTER RECORD
# ============================================================

def build_master_record(
    entity_id,
    members,
    naukri_lookup,
    gig_lookup,
    cbnexus_lookup,
):
    """Combine all source records belonging to one entity."""

    naukri_records = []
    gig_records = []
    cbnexus_records = []

    for member in members:

        source, record_id = member.split(":", 1)

        if source == "naukri":

            if record_id in naukri_lookup:

                naukri_records.append(
                    naukri_lookup[record_id]
                )

        elif source == "gig_workers":

            if record_id in gig_lookup:

                gig_records.append(
                    gig_lookup[record_id]
                )

        elif source == "cbnexus":

            if record_id in cbnexus_lookup:

                cbnexus_records.append(
                    cbnexus_lookup[record_id]
                )

    # --------------------------------------------------------
    # Convert source records to DataFrames
    # --------------------------------------------------------

    naukri_df = pd.DataFrame(
        naukri_records
    )

    gig_df = pd.DataFrame(
        gig_records
    )

    cbnexus_df = pd.DataFrame(
        cbnexus_records
    )

    # --------------------------------------------------------
    # Basic identity fields
    # --------------------------------------------------------

    names = []

    if not naukri_df.empty:

        names.extend(
            naukri_df["Full Name"].tolist()
        )

    if not gig_df.empty:

        names.extend(
            gig_df["worker_name"].tolist()
        )

    if not cbnexus_df.empty:

        names.extend(
            cbnexus_df["Name"].tolist()
        )

    # --------------------------------------------------------
    # Emails
    # --------------------------------------------------------

    emails = []

    if not naukri_df.empty:

        emails.extend(
            naukri_df["Email"].tolist()
        )

    if not gig_df.empty:

        emails.extend(
            gig_df["email_id"].tolist()
        )

    # --------------------------------------------------------
    # Phones
    # --------------------------------------------------------

    phones = []

    if not naukri_df.empty:

        phones.extend(
            naukri_df["Phone"].tolist()
        )

    if not cbnexus_df.empty:

        phones.extend(
            cbnexus_df["Phone Number"].tolist()
        )

    # --------------------------------------------------------
    # Cities
    # --------------------------------------------------------

    cities = []

    if not naukri_df.empty:

        cities.extend(
            naukri_df["City"].tolist()
        )

    if not gig_df.empty:

        cities.extend(
            gig_df["location"].tolist()
        )

    if not cbnexus_df.empty:

        cities.extend(
            cbnexus_df["City"].tolist()
        )

    # --------------------------------------------------------
    # Naukri attributes
    # --------------------------------------------------------

    experience = pd.NA
    current_ctc = pd.NA
    applied_date = pd.NA
    naukri_skills = pd.NA

    if not naukri_df.empty:

        experience = first_valid(
            naukri_df["Experience (Years)"]
        )

        current_ctc = first_valid(
            naukri_df["Current CTC"]
        )

        applied_date = first_valid(
            naukri_df["Applied Date"]
        )

        naukri_skills = unique_values(
            naukri_df["Skills"]
        )

    # --------------------------------------------------------
    # Gig attributes
    # --------------------------------------------------------

    gig_rate = pd.NA
    gig_rate_amount = pd.NA
    gig_rate_period = pd.NA
    gig_status = pd.NA
    gig_skills = pd.NA

    if not gig_df.empty:

        gig_rate = first_valid(
            gig_df["rate"]
        )

        gig_rate_amount = first_valid(
            gig_df["rate_amount"]
        )

        gig_rate_period = first_valid(
            gig_df["rate_period"]
        )

        gig_status = first_valid(
            gig_df["status"]
        )

        gig_skills = unique_values(
            gig_df["skill_tags"]
        )

    # --------------------------------------------------------
    # CBNexus attributes
    # --------------------------------------------------------

    verified = pd.NA
    projects_completed = pd.NA

    if not cbnexus_df.empty:

        verified = first_valid(
            cbnexus_df["Verified"]
        )

        projects_completed = first_valid(
            cbnexus_df["Projects Completed"]
        )

    # --------------------------------------------------------
    # Return master record
    # --------------------------------------------------------

    return {

        "entity_id": entity_id,

        "name": unique_values(
            pd.Series(names)
        ),

        "email": unique_values(
            pd.Series(emails)
        ),

        "phone": unique_values(
            pd.Series(phones)
        ),

        "city": unique_values(
            pd.Series(cities)
        ),

        "experience_years": experience,

        "current_ctc": current_ctc,

        "applied_date": applied_date,

        "naukri_skills": naukri_skills,

        "gig_rate": gig_rate,

        "gig_rate_amount": gig_rate_amount,

        "gig_rate_period": gig_rate_period,

        "gig_status": gig_status,

        "gig_skills": gig_skills,

        "verified": verified,

        "projects_completed": projects_completed,

        "naukri_record_ids": unique_values(
            pd.Series(
                [
                    member.split(":", 1)[1]
                    for member in members
                    if member.startswith("naukri:")
                ]
            )
        ),

        "gig_record_ids": unique_values(
            pd.Series(
                [
                    member.split(":", 1)[1]
                    for member in members
                    if member.startswith("gig_workers:")
                ]
            )
        ),

        "cbnexus_record_ids": unique_values(
            pd.Series(
                [
                    member.split(":", 1)[1]
                    for member in members
                    if member.startswith("cbnexus:")
                ]
            )
        ),
    }


# ============================================================
# BUILD MASTER TABLE
# ============================================================

def build_master_table(
    naukri,
    gig,
    cbnexus,
    matches,
    transitive_matches,
):
    """Create the final resolved entity table."""

    clusters = build_entity_clusters(
        matches,
        transitive_matches,
        naukri,
    )

    (
        naukri_lookup,
        gig_lookup,
        cbnexus_lookup,
    ) = create_lookups(
        naukri,
        gig,
        cbnexus,
    )

    records = []

    # --------------------------------------------------------
    # Sort clusters for deterministic entity IDs
    # --------------------------------------------------------

    sorted_clusters = sorted(
        clusters.values(),
        key=lambda members: sorted(members)[0],
    )

    for index, members in enumerate(
        sorted_clusters,
        start=1,
    ):

        entity_id = (
            f"ENTITY_{index:04d}"
        )

        record = build_master_record(
            entity_id,
            members,
            naukri_lookup,
            gig_lookup,
            cbnexus_lookup,
        )

        records.append(record)

    return pd.DataFrame(records)


# ============================================================
# ADD UNMATCHED NAUKRI
# ============================================================

def add_unmatched_naukri(
    master,
    naukri,
):
    """
    Add Naukri records that were not connected to another
    source through a HIGH-confidence relationship.
    """

    existing_ids = set()

    for value in master[
        "naukri_record_ids"
    ].dropna():

        for record_id in str(value).split(";"):

            existing_ids.add(
                record_id.strip()
            )

    rows = []

    for _, row in naukri.iterrows():

        record_id = row[
            "source_record_id"
        ]

        if record_id in existing_ids:
            continue

        rows.append(
            {
                "entity_id": None,

                "name": row["Full Name"],

                "email": row["Email"],

                "phone": row["Phone"],

                "city": row["City"],

                "experience_years": row[
                    "Experience (Years)"
                ],

                "current_ctc": row[
                    "Current CTC"
                ],

                "applied_date": row[
                    "Applied Date"
                ],

                "naukri_skills": row[
                    "Skills"
                ],

                "gig_rate": pd.NA,

                "gig_rate_amount": pd.NA,

                "gig_rate_period": pd.NA,

                "gig_status": pd.NA,

                "gig_skills": pd.NA,

                "verified": pd.NA,

                "projects_completed": pd.NA,

                "naukri_record_ids": record_id,

                "gig_record_ids": pd.NA,

                "cbnexus_record_ids": pd.NA,
            }
        )

    if rows:

        start = len(master) + 1

        for i, row in enumerate(rows):

            row["entity_id"] = (
                f"ENTITY_{start + i:04d}"
            )

        master = pd.concat(
            [
                master,
                pd.DataFrame(rows),
            ],
            ignore_index=True,
        )

    return master


# ============================================================
# ADD UNMATCHED GIG WORKERS
# ============================================================

def add_unmatched_gig(
    master,
    gig,
):
    """Add Gig Worker records not already resolved."""

    existing_ids = set()

    for value in master[
        "gig_record_ids"
    ].dropna():

        for record_id in str(value).split(";"):

            existing_ids.add(
                record_id.strip()
            )

    rows = []

    for _, row in gig.iterrows():

        record_id = row[
            "source_record_id"
        ]

        if record_id in existing_ids:
            continue

        rows.append(
            {
                "entity_id": None,

                "name": row[
                    "worker_name"
                ],

                "email": row[
                    "email_id"
                ],

                "phone": pd.NA,

                "city": row[
                    "location"
                ],

                "experience_years": pd.NA,

                "current_ctc": pd.NA,

                "applied_date": pd.NA,

                "naukri_skills": pd.NA,

                "gig_rate": row[
                    "rate"
                ],

                "gig_rate_amount": row[
                    "rate_amount"
                ],

                "gig_rate_period": row[
                    "rate_period"
                ],

                "gig_status": row[
                    "status"
                ],

                "gig_skills": row[
                    "skill_tags"
                ],

                "verified": pd.NA,

                "projects_completed": pd.NA,

                "naukri_record_ids": pd.NA,

                "gig_record_ids": record_id,

                "cbnexus_record_ids": pd.NA,
            }
        )

    if rows:

        start = len(master) + 1

        for i, row in enumerate(rows):

            row["entity_id"] = (
                f"ENTITY_{start + i:04d}"
            )

        master = pd.concat(
            [
                master,
                pd.DataFrame(rows),
            ],
            ignore_index=True,
        )

    return master


# ============================================================
# ADD UNMATCHED CBNEXUS
# ============================================================

def add_unmatched_cbnexus(
    master,
    cbnexus,
):
    """Add CBNexus records not already resolved."""

    existing_ids = set()

    for value in master[
        "cbnexus_record_ids"
    ].dropna():

        for record_id in str(value).split(";"):

            existing_ids.add(
                record_id.strip()
            )

    rows = []

    for _, row in cbnexus.iterrows():

        record_id = row[
            "source_record_id"
        ]

        if record_id in existing_ids:
            continue

        rows.append(
            {
                "entity_id": None,

                "name": row["Name"],

                "email": pd.NA,

                "phone": row[
                    "Phone Number"
                ],

                "city": row["City"],

                "experience_years": pd.NA,

                "current_ctc": pd.NA,

                "applied_date": pd.NA,

                "naukri_skills": pd.NA,

                "gig_rate": pd.NA,

                "gig_rate_amount": pd.NA,

                "gig_rate_period": pd.NA,

                "gig_status": pd.NA,

                "gig_skills": pd.NA,

                "verified": row[
                    "Verified"
                ],

                "projects_completed": row[
                    "Projects Completed"
                ],

                "naukri_record_ids": pd.NA,

                "gig_record_ids": pd.NA,

                "cbnexus_record_ids": record_id,
            }
        )

    if rows:

        start = len(master) + 1

        for i, row in enumerate(rows):

            row["entity_id"] = (
                f"ENTITY_{start + i:04d}"
            )

        master = pd.concat(
            [
                master,
                pd.DataFrame(rows),
            ],
            ignore_index=True,
        )

    return master


# ============================================================
# MASTER VALIDATION
# ============================================================

def validate_master(master):
    """
    Validate the final master table for duplicate strong
    identifiers.
    """

    print("\n" + "=" * 60)
    print("MASTER VALIDATION")
    print("=" * 60)

    # --------------------------------------------------------
    # Duplicate emails
    # --------------------------------------------------------

    email_values = []

    for value in master["email"].dropna():

        for email in str(value).split(";"):

            email = normalize_text(email)

            if email:
                email_values.append(email)

    duplicate_emails = {
        email
        for email in email_values
        if email_values.count(email) > 1
    }

    print(
        "Duplicate normalized emails:",
        len(duplicate_emails),
    )

    if duplicate_emails:

        for email in sorted(duplicate_emails):
            print(" -", email)

    # --------------------------------------------------------
    # Duplicate phones
    # --------------------------------------------------------

    phone_values = []

    for value in master["phone"].dropna():

        for phone in str(value).split(";"):

            phone = normalize_text(phone)

            if phone:
                phone_values.append(phone)

    duplicate_phones = {
        phone
        for phone in phone_values
        if phone_values.count(phone) > 1
    }

    print(
        "Duplicate normalized phones:",
        len(duplicate_phones),
    )

    if duplicate_phones:

        for phone in sorted(duplicate_phones):
            print(" -", phone)

    # --------------------------------------------------------
    # Validation result
    # --------------------------------------------------------

    if not duplicate_emails and not duplicate_phones:

        print("Master validation: PASSED")

    else:

        print(
            "Master validation: REVIEW REQUIRED"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    os.makedirs(
        "data",
        exist_ok=True,
    )

    os.makedirs(
        "reports",
        exist_ok=True,
    )

    (
        naukri,
        gig,
        cbnexus,
        matches,
        transitive_matches,
        candidates,
    ) = load_data()

    # --------------------------------------------------------
    # Add same source IDs used during entity resolution
    # --------------------------------------------------------

    (
        naukri,
        gig,
        cbnexus,
    ) = add_source_ids(
        naukri,
        gig,
        cbnexus,
    )

    # --------------------------------------------------------
    # Build resolved entities
    # --------------------------------------------------------

    master = build_master_table(
        naukri,
        gig,
        cbnexus,
        matches,
        transitive_matches,
    )

    # --------------------------------------------------------
    # Add records with no HIGH-confidence relationship
    # --------------------------------------------------------

    master = add_unmatched_naukri(
        master,
        naukri,
    )

    master = add_unmatched_gig(
        master,
        gig,
    )

    master = add_unmatched_cbnexus(
        master,
        cbnexus,
    )

    # --------------------------------------------------------
    # Save master entity table
    # --------------------------------------------------------

    master.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # --------------------------------------------------------
    # Validate master
    # --------------------------------------------------------

    validate_master(
        master
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("=" * 60)
    print("MASTER ENTITY BUILD SUMMARY")
    print("=" * 60)

    print(
        "Naukri records:",
        len(naukri),
    )

    print(
        "Gig Worker records:",
        len(gig),
    )

    print(
        "CBNexus records:",
        len(cbnexus),
    )

    print(
        "Direct HIGH matches:",
        len(matches),
    )

    print(
        "Transitive HIGH matches:",
        len(transitive_matches),
    )

    print(
        "Unresolved candidates:",
        len(candidates),
    )

    print(
        "Master entities:",
        len(master),
    )

    print(
        "\nMaster file saved to:"
    )

    print(
        OUTPUT_FILE
    )

    # --------------------------------------------------------
    # Preview
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("MASTER ENTITY PREVIEW")
    print("=" * 60)

    print(
        master.head(20).to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()