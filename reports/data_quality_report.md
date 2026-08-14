# Data Quality Report

## 1. Overview

Three source datasets were investigated before and after cleaning:

* `source1_naukri_applicants.csv`
* `source2_gig_workers.csv`
* `source3_cbnexus_contacts.csv`

The investigation focused on structural errors, missing records, inconsistent representations, duplicate or identity-conflicting records, and cross-source matching risks.

The cleaning pipeline was then used to remediate the identified issues. Final validation confirmed complete source coverage and no duplicate master-level email, phone, or source IDs.

---

## 2. Data Quality Issues Summary

| Dataset      | Problem Found                           | Evidence                                                                                                   | Action Taken                                              | Result                            |
| ------------ | --------------------------------------- | ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | --------------------------------- |
| Gig Workers  | Completely empty row                    | 1 row contained no values                                                                                  | Removed during ingestion                                  | 1 row removed                     |
| Gig Workers  | Structurally shifted Isha Chopra record | Values appeared in incorrect columns                                                                       | Detected and repaired using field validation              | 1 row repaired                    |
| Gig Workers  | Repair-created duplicate                | Repaired record became identical to an existing valid record                                               | Removed the repaired duplicate                            | 1 duplicate removed               |
| Gig Workers  | Mixed rate formats                      | Values included `1415/hr`, `15k/month`, etc.                                                               | Parsed into numeric amount and rate period                | Normalized                        |
| Gig Workers  | Inconsistent status casing              | `Active`, `ACTIVE`, `active`                                                                               | Converted to canonical lowercase representation           | Normalized                        |
| CBNexus      | Embedded header row                     | 1 data row contained `Name`, `Phone Number`, `City`, etc.                                                  | Detected and removed                                      | 1 row removed                     |
| CBNexus      | Inconsistent verification values        | `Y`, `Yes`, `yes`, `N`, `No`                                                                               | Converted to boolean representation                       | 14 True / 16 False                |
| CBNexus      | Inconsistent phone formats              | 10-digit, `91...`, and `+91-...` representations                                                           | Normalized to a common 10-digit format                    | Normalized                        |
| Naukri       | Duplicate/identity candidates           | Nikhil Chopra had the same phone with two email addresses; `R. Verma` and `Rohit Verma` shared phone/email | Deferred to entity resolution instead of deleting records | Preserved for identity resolution |
| Cross-source | Different phone representations         | Naukri and CBNexus used different phone formats                                                            | Normalized before comparison                              | 25 phone matches found            |
| Cross-source | Identity ambiguity                      | Name alone is not sufficiently reliable for merging                                                        | Automatic merging requires stronger identifiers           | Name-only merges avoided          |

---

## 3. Naukri Applicants

### 3.1 Phone and Identity Duplication

The investigation identified two types of potential identity duplicates.

#### Nikhil Chopra

Two Naukri records have:

* Same name: `Nikhil Chopra`
* Same phone: `9000000103`
* Same city: `NOIDA`
* Same skills: `Pandas, SQL, n8n`
* Different email addresses:

  * `alt.nikhil.chopra70@example.com`
  * `nikhil.chopra70@example.com`

These records were not blindly deleted because the alternate email may represent useful information about the same person.

#### R. Verma / Rohit Verma

Two records share:

* Same email: `rohit.verma13@mailtest.example.org`
* Same phone: `9000000294`
* Same city: `Bangalore`
* Same skills: `Python, React, MongoDB`

Their names are represented differently:

* `R. Verma`
* `Rohit Verma`

This is an identity-resolution case rather than an exact duplicate row.

### 3.2 Exact Duplicate Check

The Naukri cleaner found:

* Original rows: 42
* Exact duplicate rows removed: 0
* Final rows: 42

Therefore, no exact duplicate Naukri rows were deleted during source-level cleaning.

Potential identity duplicates were intentionally left for the entity-resolution stage.

### 3.3 Normalization

The Naukri cleaning process normalizes:

* Names
* Email addresses
* Phone numbers
* City names
* Application dates

This ensures consistent representations before cross-source matching.

---

## 4. Gig Workers

### 4.1 Completely Empty Row

One row contained no values across the dataset.

**Action taken:** The row was identified as an empty record and removed during ingestion.

**Result:**

* Original rows: 32
* Empty rows removed: 1

### 4.2 Structurally Shifted Isha Chopra Record

The investigation identified one malformed record where fields were shifted into incorrect columns.

The observed values were:

* `react, javascript, mysql` in `email_id`
* `ISHA.CHOPRA95@MAILTEST.EXAMPLE.ORG` in `worker_name`
* `Isha Chopra` in `rate`
* `1406/hr` in `location`
* `Pune` in `status`
* `active` in `skill_tags`

This explains why `Pune` appeared as a status value.

**Action taken:** The pipeline detected the structural anomaly using field validation and repaired the row before normalization.

The repaired record subsequently became an exact duplicate of an existing valid record.

**Action taken:** The repaired duplicate was removed rather than retaining two identical records.

**Result:**

* Shifted rows repaired: 1
* Repair-created duplicates removed: 1

### 4.3 Mixed Rate Formats

The `rate` field contains different representations, including:

* `1415/hr`
* `1231/hr`
* `15k/month`
* `72k/month`

**Action taken:** Rate values are parsed into:

* `rate_amount`
* `rate_period`

This preserves the difference between hourly and monthly compensation instead of treating the values as the same type.

### 4.4 Inconsistent Status Representation

The raw data contains:

* `Active`
* `ACTIVE`
* `active`
* `Inactive`
* `paused`

The malformed Isha Chopra record also produced `Pune` in the status column.

**Action taken:** The malformed record was repaired first, then status values were normalized to a canonical representation.

### 4.5 Final Gig Worker Result

The cleaning process produced:

* Original rows: 32
* Empty rows removed: 1
* Shifted rows repaired: 1
* Repair-created duplicates removed: 1
* Final rows: 30

---

## 5. CBNexus Contacts

### 5.1 Embedded Header Row

The dataset contained one data row containing the column headers themselves:

* `Name`
* `Phone Number`
* `City`
* `Verified`
* `Projects Completed`

**Action taken:** The row was detected by matching the expected header values and removed.

**Result:**

* Original rows: 31
* Embedded header rows removed: 1
* Final rows: 30

### 5.2 Inconsistent Verification Values

The raw `Verified` field contained:

* `Y`
* `Yes`
* `yes`
* `N`
* `No`

The embedded header row also contained `Verified` as a value.

**Action taken:** Verification values were normalized into boolean values.

**Result after cleaning:**

* `True`: 14
* `False`: 16

### 5.3 Inconsistent Phone Representations

CBNexus phone numbers appeared in multiple formats, including:

* 10-digit numbers
* Numbers beginning with `91`
* Numbers using the `+91-` prefix

**Action taken:** Phone numbers were normalized to a common 10-digit representation.

This allowed reliable comparison with Naukri records.

---

## 6. Cross-Source Identity Resolution

Data quality was not limited to formatting problems. The three sources also contained records representing the same people using different representations.

### 6.1 Phone-Based Matching

After phone normalization, Naukri and CBNexus produced:

**25 phone matches**

Examples included differences such as:

* `9000000254`
* `919000000138`
* `+91-9000000227`

These were converted to a common representation before matching.

### 6.2 Email-Based Matching

Naukri and Gig Workers produced:

**11 exact email matches**

The investigation found:

**0 name differences among these email matches.**

This provides stronger evidence that the matching records represent the same people.

### 6.3 Name-Only Matching

Name alone was not treated as sufficient evidence for automatic entity merging.

This is important because identical names can refer to different people, while abbreviated names such as `R. Verma` can refer to the same person as `Rohit Verma`.

The entity-resolution strategy therefore prioritizes:

1. Exact normalized email
2. Exact normalized phone
3. Strong combinations such as phone + normalized name
4. Email + normalized name

Name-only matches are not automatically merged.

---

## 7. Before and After Summary

| Dataset     | Raw Rows | Rows Removed | Rows Repaired | Final Rows |
| ----------- | -------: | -----------: | ------------: | ---------: |
| Naukri      |       42 |            0 |             0 |         42 |
| Gig Workers |       32 |            2 |             1 |         30 |
| CBNexus     |       31 |            1 |             0 |         30 |
| **Total**   |  **105** |        **3** |         **1** |    **102** |

The Gig Worker total includes one empty row and one repair-created duplicate being removed. The shifted Isha Chopra row was repaired before the duplicate was identified.

---

## 8. Final Master Validation

After cleaning and entity resolution, the final master dataset was validated.

### Master Entities

**60**

### Source Coverage

* Naukri: **42 / 42**
* Gig Workers: **30 / 30**
* CBNexus: **30 / 30**

### Duplicate Checks

* Duplicate emails: **0**
* Duplicate phones: **0**
* Duplicate Naukri IDs: **0**
* Duplicate Gig IDs: **0**
* Duplicate CBNexus IDs: **0**

### Validation Result

**FINAL VALIDATION: PASSED**

The final master dataset therefore retains complete source coverage while satisfying the duplicate and source-ID validation checks.

---

## 9. Key Data-Quality Decisions

The cleaning process deliberately separates **data cleaning** from **entity resolution**.

Formatting problems such as whitespace, casing, phone representation, malformed rows, and embedded headers were corrected during source cleaning.

Potential identity duplicates were not automatically deleted merely because records looked similar. Strong identifiers such as normalized email and phone were used to support entity resolution.

This approach reduces the risk of false merges while preserving potentially useful source information.

