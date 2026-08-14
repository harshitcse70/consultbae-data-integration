# ConsultBae Data Integration & Entity Resolution Pipeline

An end-to-end data integration pipeline that cleans, normalizes, resolves, merges, validates, and stores records from three heterogeneous CSV data sources into a unified master entity dataset and SQLite database.

The project is designed around the core requirement:

> **The same person appearing in multiple source files must become ONE master entity, even when no common ID exists across the files.**

---

##  Problem Statement

The input consists of three different datasets representing overlapping people:

1. Naukri applicants
2. Gig workers
3. CBNexus contacts

The datasets have different schemas and identifiers.

For example:

### Naukri

```text
Full Name
Email
Phone
City
Experience (Years)
Current CTC
Applied Date
Skills
```

### Gig Workers

```text
email_id
worker_name
rate
location
status
skill_tags
```

### CBNexus

```text
Name
Phone Number
City
Verified
Projects Completed
```

There is no single ID shared across all three datasets.

Therefore, a simple database join using an ID is not possible.

The pipeline must determine when records from different sources represent the same real-world person.

---

#  Solution Overview

The project implements a complete ETL + Entity Resolution pipeline:

```text
                 SOURCE CSV FILES
                       │
                       ▼
              ┌──────────────────┐
              │ Data Inspection   │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Data Cleaning     │
              │ & Repair          │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Normalization     │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Entity Resolution │
              └────────┬─────────┘
                       │
             ┌─────────┴──────────┐
             │                    │
             ▼                    ▼
       HIGH-CONFIDENCE       REVIEW CANDIDATES
          MATCHES
             │
             ▼
       ┌───────────────┐
       │ Master Entity │
       │    Build      │
       └───────┬───────┘
               │
               ▼
       ┌───────────────┐
       │ Validation    │
       └───────┬───────┘
               │
               ▼
       ┌───────────────┐
       │ SQLite        │
       │ Database      │
       └───────────────┘
```

The entire pipeline can be executed with:

```bash
python src/run_pipeline.py
```

---

#  Key Features

* Multi-source CSV ingestion
* Source-specific data cleaning
* Malformed row repair
* Empty-row removal
* Embedded-header removal
* Duplicate detection
* Field normalization
* Email-based entity matching
* Phone-based entity matching
* Cross-source entity resolution
* Naukri bridge / transitive matching
* Candidate generation for ambiguous matches
* Master entity construction
* Source record lineage
* Duplicate validation
* Source coverage validation
* SQLite database loading
* Database validation
* One-command pipeline execution
* CSV and report outputs

---

#  Source Datasets

The pipeline currently processes three source datasets.

```text
data/
├── source1_naukri_applicants.csv
├── source2_gig_workers.csv
└── source3_cbnexus_contacts.csv
```

## Naukri Applicants

Contains applicant information including:

* Name
* Email
* Phone
* City
* Experience
* Current CTC
* Applied Date
* Skills

## Gig Workers

Contains:

* Email
* Worker name
* Rate
* Location
* Status
* Skill tags

## CBNexus

Contains:

* Name
* Phone
* City
* Verification status
* Projects completed

---

#  Data Cleaning

Each source requires different cleaning rules because the input structures and quality issues differ.

## Naukri Cleaning

The Naukri pipeline:

* Loads the source CSV
* Removes exact duplicate rows
* Normalizes fields
* Normalizes dates
* Preserves valid records
* Produces a cleaned Naukri dataset

Output:

```text
data/cleaned_naukri_applicants.csv
```

Current result:

```text
Original rows: 42
Exact duplicate rows removed: 0
Final rows: 42
```

---

## Gig Worker Cleaning

The Gig Worker source contained malformed/duplicated information.

The cleaning pipeline handles:

* Empty rows
* Malformed records
* Row repair
* Repair-created duplicates
* Rate normalization
* Rate amount extraction
* Rate period extraction

For example:

```text
1415/hr
```

is normalized into:

```text
rate_amount = 1415
rate_period = hour
```

while:

```text
15k/month
```

becomes:

```text
rate_amount = 15000
rate_period = month
```

Current result:

```text
Original rows: 32
Removed empty rows: 1
Repaired rows: 1
Repair-created duplicates removed: 1
Final rows: 30
```

Output:

```text
data/cleaned_gig_workers.csv
```

---

## CBNexus Cleaning

The CBNexus source contained an embedded header row inside the data.

The pipeline removes the embedded header and normalizes the fields.

Current result:

```text
Original rows: 31
Embedded header rows removed: 1
Final rows: 30
```

Output:

```text
data/cleaned_cbnexus_contacts.csv
```

---

#  Normalization

Normalization is performed before entity resolution.

The objective is to make logically equivalent values comparable.

Examples include:

### Email

```text
ISHA.CHOPRA95@MAILTEST.EXAMPLE.ORG
```

becomes:

```text
isha.chopra95@mailtest.example.org
```

### Names

Names are normalized for comparison by:

* trimming whitespace
* standardizing case
* removing unnecessary formatting differences

### Phone numbers

Phone values are normalized so that formatting differences do not prevent matching.

### Dates

Dates from different input formats are converted into a consistent representation.

### Locations

Location values are normalized for comparison while preserving source information where required.

---

# Entity Resolution

Entity resolution is the core part of the project.

The objective is:

```text
Different source records
        ↓
Same real-world person?
        ↓
ONE master entity
```

The pipeline uses deterministic identifiers whenever possible instead of relying only on names.

---

#  Matching Strategy

The project uses multiple levels of matching.

## Level 1 — Email Matching

Email is treated as a strong identifier.

Example:

```text
Naukri:
isha.chopra95@mailtest.example.org

Gig Worker:
isha.chopra95@mailtest.example.org
```

These records are treated as a HIGH-confidence match.

---

## Level 2 — Phone Matching

Phone numbers are also treated as strong identifiers.

Example:

```text
Naukri:
9000000263

CBNexus:
9000000263
```

These records can be resolved as the same entity.

---

## Level 3 — Naukri Bridge / Transitive Matching

One important challenge is that Gig Workers and CBNexus may not share a direct identifier.

However:

```text
Gig Worker
     │
     │ email
     ▼
  Naukri
     │
     │ phone
     ▼
 CBNexus
```

If the Naukri record connects the Gig Worker and CBNexus records to the same person, the relationship can be propagated.

For example:

```text
Gig Worker
GIG_001
Varun Jain

        │
        │ email
        ▼

Naukri
NAUKRI_018
Varun Jain

        │
        │ phone
        ▼

CBNexus
CBN_011
Varun Jain
```

This allows the three records to become:

```text
ENTITY_0011
Varun Jain
```

This is implemented as a `naukri_bridge` transitive match.

---

#  Candidate Matching

Not every possible match is automatically accepted.

For example, the pipeline may find:

```text
Gig Worker:
Arjun Mehta
Noida

CBNexus:
Arjun Mehta
Noida
```

This is a useful candidate, but if there is no sufficiently strong deterministic identifier, the pipeline does not blindly merge the records.

Instead it marks the relationship as:

```text
match_method = name+city
confidence = CANDIDATE
```

This prevents false-positive merges.

---

#  Current Entity Resolution Results

The current dataset produced:

```text
Naukri-Gig high-confidence matches: 15
Naukri-CBNexus high-confidence matches: 25
Initial Gig-CBNexus candidates: 15
Gig-CBNexus transitive HIGH matches: 9
Remaining candidates requiring review: 6
```

The six unresolved candidates are retained separately for review instead of being force-merged.

This is intentional.

---

#  Master Entity Construction

After entity resolution, the pipeline builds a unified master dataset.

The current result is:

```text
Naukri records: 42
Gig Worker records: 30
CBNexus records: 30

Direct HIGH matches: 40
Transitive HIGH matches: 9
Unresolved candidates: 6

Master entities: 60
```

Output:

```text
data/master_entities.csv
```

---

#  Master Entity Structure

The master entity dataset contains consolidated information from the available sources.

Main fields include:

```text
entity_id
name
email
phone
city
experience_years
current_ctc
applied_date
naukri_skills
gig_rate
gig_rate_amount
gig_rate_period
gig_status
gig_skills
verified
projects_completed
naukri_record_ids
gig_record_ids
cbnexus_record_ids
```

Example:

```text
ENTITY_0011
Varun Jain
varun.jain29@example.com
9000000263
Pune
```

with source lineage:

```text
NAUKRI_018
GIG_001
CBN_011
```

Thus multiple source records represent one master entity.

---

#  Source Lineage

The project preserves the original source IDs associated with each master entity.

Example:

```text
Master Entity:
ENTITY_0011

Naukri:
NAUKRI_018

Gig Worker:
GIG_001

CBNexus:
CBN_011
```

This is important because it provides traceability.

Instead of losing the original source records after merging, the system can answer:

> "Which source records contributed to this master entity?"

---

#  SQLite Database

The final master data is loaded into SQLite.

Database:

```text
data/consultbae.db
```

The database contains the unified master entities and source lineage information.

The database currently contains:

```text
Entities inserted: 60
Source lineage records: 100
```

---

#  Database Validation

Before the database is considered valid, the pipeline checks:

* Number of inserted entities
* Duplicate emails
* Duplicate phones
* Source lineage
* Database consistency

Current result:

```text
Entities inserted: 60
Source lineage records: 100
Duplicate emails: 0
Duplicate phones: 0

DATABASE VALIDATION: PASSED
```

---

#  Final Validation

The project performs a final validation of the master dataset.

Checks include:

### Source coverage

```text
Naukri:   42 / 42
Gig:      30 / 30
CBNexus:  30 / 30
```

### Duplicate checks

```text
Duplicate emails: 0
Duplicate phones: 0
```

### Source ID checks

```text
Duplicate Naukri IDs: 0
Duplicate Gig IDs: 0
Duplicate CBNexus IDs: 0
```

Final result:

```text
FINAL VALIDATION: PASSED
```

---

#  Project Structure

```text
consultbae-assignment/
│
├── data/
│   ├── source1_naukri_applicants.csv
│   ├── source2_gig_workers.csv
│   ├── source3_cbnexus_contacts.csv
│   │
│   ├── cleaned_naukri_applicants.csv
│   ├── cleaned_gig_workers.csv
│   ├── cleaned_cbnexus_contacts.csv
│   ├── master_entities.csv
│   └── consultbae.db
│
├── reports/
│   ├── entity_matches.csv
│   ├── entity_candidates.csv
│   ├── entity_transitive_matches.csv
│   └── entity_resolution_summary.csv
│
├── src/
│   ├── clean_data.py
│   ├── clean_naukri.py
│   ├── clean_cbnexus.py
│   ├── normalize.py
│   ├── entity_resolution.py
│   ├── build_master.py
│   ├── final_validation.py
│   ├── load_database.py
│   ├── run_pipeline.py
│   ├── inspect_data.py
│   ├── investigate_issues.py
│   ├── test_normalization.py
│   └── validate.py
│
├── README.md
├── requirements.txt
└── .gitignore
```

---

#  Description of Important Scripts

## `clean_data.py`

Cleans and repairs the Gig Worker source.

---

## `clean_naukri.py`

Cleans the Naukri applicant source.

---

## `clean_cbnexus.py`

Cleans the CBNexus source and removes embedded header records.

---

## `normalize.py`

Contains shared field normalization utilities.

---

## `entity_resolution.py`

Performs:

* Email matching
* Phone matching
* Candidate generation
* Naukri bridge matching
* Match classification
* Entity resolution reports

---

## `build_master.py`

Builds the unified master entity dataset.

Output:

```text
data/master_entities.csv
```

---

## `final_validation.py`

Validates:

* Source coverage
* Duplicate emails
* Duplicate phones
* Duplicate source IDs

---

## `load_database.py`

Loads the master entities and source lineage into SQLite.

Output:

```text
data/consultbae.db
```

---

## `run_pipeline.py`

The pipeline orchestrator.

It runs all major stages in sequence:

```text
Clean Naukri
     ↓
Clean Gig Workers
     ↓
Clean CBNexus
     ↓
Entity Resolution
     ↓
Build Master
     ↓
Final Validation
     ↓
Load SQLite
```

If a step fails, the pipeline stops instead of continuing with potentially invalid data.

---

# 19. Running the Project

## Step 1 — Clone the repository

```bash
git clone <repository-url>
cd consultbae-assignment
```

---

## Step 2 — Create a virtual environment

Windows:

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

---

## Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

Current dependencies:

```text
numpy==2.4.6
pandas==3.0.5
python-dateutil==2.9.0.post0
six==1.17.0
tzdata==2026.3
```

SQLite is provided by Python's standard library and does not need to be installed separately.

---

#  Run the Complete Pipeline

The recommended way to run the project is:

```bash
python src/run_pipeline.py
```

This executes the entire workflow automatically.

Successful execution ends with:

```text
PIPELINE COMPLETED SUCCESSFULLY
```

---

#  Generated Outputs

After successful execution, the following files are produced.

## Cleaned datasets

```text
data/cleaned_naukri_applicants.csv
data/cleaned_gig_workers.csv
data/cleaned_cbnexus_contacts.csv
```

## Master dataset

```text
data/master_entities.csv
```

## SQLite database

```text
data/consultbae.db
```

## Entity resolution reports

```text
reports/entity_matches.csv
reports/entity_candidates.csv
reports/entity_transitive_matches.csv
reports/entity_resolution_summary.csv
```

---

#  Reports

## `entity_matches.csv`

Contains high-confidence direct entity matches.

Example:

```text
source_a       source_b
naukri         gig_workers
```

with:

```text
match_method = email
confidence = HIGH
```

or:

```text
match_method = phone
confidence = HIGH
```

---

## `entity_candidates.csv`

Contains unresolved matches that require review.

Example:

```text
match_method = name+city
confidence = CANDIDATE
```

---

## `entity_transitive_matches.csv`

Contains matches established through the Naukri bridge.

Example:

```text
gig_workers → naukri → cbnexus
```

with:

```text
match_method = naukri_bridge
confidence = HIGH
```

---

## `entity_resolution_summary.csv`

Contains summary information about the entity-resolution process.

---

#  Example Data Flow

Suppose the same person appears as:

### Naukri

```text
Name:
Varun Jain

Email:
varun.jain29@example.com

Phone:
9000000263
```

### Gig Workers

```text
Worker:
Varun Jain

Email:
varun.jain29@example.com

Location:
Pune
```

### CBNexus

```text
Name:
Varun Jain

Phone:
9000000263

City:
Pune
```

The system resolves these records into:

```text
ENTITY_0011
```

instead of creating three separate people.

---

#  Why Deterministic Matching Is Preferred

Entity resolution can create false positives if matching is based only on names.

For example:

```text
Arjun Mehta
```

could represent multiple people.

Therefore the pipeline prioritizes stronger identifiers:

```text
Email
  ↓
Phone
  ↓
Cross-source bridge
  ↓
Name + City candidate
```

Ambiguous records are not automatically merged.

This approach prioritizes data integrity over aggressive matching.

---

#  Handling Ambiguous Records

The current dataset contains six unresolved candidates.

These are retained as candidates instead of being automatically merged.

This means the system follows:

```text
HIGH confidence
     ↓
Automatically merge

CANDIDATE
     ↓
Keep for human review
```

This reduces the risk of incorrect entity consolidation.

---

#  Data Quality Philosophy

The pipeline follows several principles:

### 1. Normalize before matching

Equivalent values should be transformed into a comparable representation before entity resolution.

### 2. Prefer deterministic identifiers

Email and phone are stronger than names alone.

### 3. Do not force ambiguous matches

Uncertain records should remain candidates.

### 4. Preserve lineage

Original source IDs should remain traceable.

### 5. Validate after transformation

The final master dataset and database must be validated before being considered successful.

---

#  Current Validation Results

The current dataset successfully produces:

```text
Source records:

Naukri       42
Gig Workers  30
CBNexus      30
----------------
Total        102
```

After entity resolution:

```text
Master entities: 60
```

Matching results:

```text
Direct HIGH matches:       40
Transitive HIGH matches:    9
Unresolved candidates:      6
```

Validation:

```text
Duplicate emails:           0
Duplicate phones:           0
Duplicate Naukri IDs:       0
Duplicate Gig IDs:          0
Duplicate CBNexus IDs:      0
```

Database:

```text
Entities:                   60
Source lineage records:    100
```

Final status:

```text
FINAL VALIDATION: PASSED
DATABASE VALIDATION: PASSED
PIPELINE COMPLETED SUCCESSFULLY
```

---

#  Database Design

The SQLite database provides a persistent representation of the unified dataset.

Conceptually:

```text
                ┌──────────────────────┐
                │       entities       │
                ├──────────────────────┤
                │ entity_id             │
                │ name                  │
                │ email                 │
                │ phone                 │
                │ city                  │
                │ ...                   │
                └──────────┬───────────┘
                           │
                           │ entity_id
                           │
                ┌──────────▼───────────┐
                │    entity_sources    │
                ├──────────────────────┤
                │ entity_id             │
                │ source                │
                │ source_record_id      │
                └──────────────────────┘
```

This separates the unified entity from its source-system records.

---

#  Example SQLite Queries

Connect to the database using Python:

```python
import sqlite3

connection = sqlite3.connect("data/consultbae.db")

cursor = connection.cursor()

cursor.execute("""
    SELECT entity_id, name, email, phone
    FROM entities
    LIMIT 10
""")

for row in cursor.fetchall():
    print(row)

connection.close()
```

---

## Find a specific person

```sql
SELECT *
FROM entities
WHERE name = 'Varun Jain';
```

---

## Find source lineage

```sql
SELECT *
FROM entity_sources
WHERE entity_id = 'ENTITY_0011';
```

---

## Count entities

```sql
SELECT COUNT(*)
FROM entities;
```

---

## Count source records by source

```sql
SELECT source, COUNT(*)
FROM entity_sources
GROUP BY source;
```

---

#  Assumptions

The current implementation assumes:

1. Email addresses are reliable when present.
2. Phone numbers are reliable when present.
3. Names are useful for candidate generation but are not always sufficient for automatic matching.
4. Naukri can act as a bridge between Gig Worker and CBNexus records when strong identifiers connect the records.
5. Ambiguous name/city matches should not automatically be treated as the same person.
6. The input schemas correspond to the currently supported source formats.

---

#  Limitations

The current implementation is primarily deterministic.

It does not attempt unrestricted fuzzy matching across all fields.

For example, records such as:

```text
Rohit Verma
R. Verma
```

may require additional review unless another strong identifier confirms the relationship.

Similarly:

```text
Arjun Mehta + Noida
```

is not automatically enough to guarantee that two records represent the same person.

This is intentional because false-positive merges can be more damaging than leaving an ambiguous candidate unresolved.

---

#  Extensibility

The project can be extended to support:

* Additional CSV sources
* New source-specific cleaners
* Fuzzy name matching
* Address matching
* Skill similarity
* Confidence scoring
* Human review workflows
* PostgreSQL/MySQL
* Scheduled ingestion
* REST APIs
* Incremental updates
* Data quality dashboards
* Automated monitoring
* Duplicate resolution workflows

A new source can be integrated by adding:

```text
source-specific cleaner
        ↓
normalization
        ↓
matching rules
        ↓
master entity integration
        ↓
lineage
```

---

#  Error Handling

The pipeline is designed to stop if a major processing stage fails.

The orchestrator:

```text
run_pipeline.py
```

executes each stage independently.

If one stage returns an error:

```text
Stage failed
    ↓
Pipeline stops
    ↓
Invalid downstream output is not processed
```

This makes failures easier to diagnose.

---

# Reproducibility

The project includes:

```text
requirements.txt
```

with pinned dependency versions.

The recommended execution flow is:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python src/run_pipeline.py
```

This allows the project to be reproduced in another environment.

---

#  Assignment Requirement Mapping

The core assignment requirement is:

> Design one clean database and write a script or pipeline that ingests all 3 files into it. The same person appearing in multiple files must become ONE record.

The implementation satisfies this through:

```text
Requirement
     │
     ├── Three source files
     │       ↓
     │   Cleaning
     │
     ├── No common ID
     │       ↓
     │   Entity resolution
     │
     ├── Same person across files
     │       ↓
     │   Email / Phone / Bridge matching
     │
     ├── One master record
     │       ↓
     │   master_entities.csv
     │
     └── Clean database
             ↓
         consultbae.db
```

---

#  Final Result

The project converts three heterogeneous datasets:

```text
Naukri
Gig Workers
CBNexus
```

into a unified entity model:

```text
                   3 SOURCE SYSTEMS
                         │
                         ▼
                 ENTITY RESOLUTION
                         │
                         ▼
                  MASTER ENTITIES
                         │
                         ▼
                    SQLite DB
```

Current dataset result:

```text
102 source rows
       ↓
60 master entities
       ↓
SQLite database
```

with:

```text
0 duplicate emails
0 duplicate phones
0 duplicate source IDs
100 source lineage records
```

and successful validation.

---

#  Quick Start

For an evaluator, the complete process is:

```bash
git clone -----

cd consultbae-assignment

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

python src/run_pipeline.py
```

After successful execution:

```text
data/master_entities.csv
```

contains the unified master dataset.

And:

```text
data/consultbae.db
```

contains the final SQLite database.

---
