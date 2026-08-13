# Data Quality Report

## Overview

The assignment contains three source datasets with overlapping people and inconsistent data.

Before transforming the data, the source files were inspected to identify missing values, malformed records, inconsistent representations, duplicates, and potential identity-matching issues.

## Findings

### 1. Empty row in Gig Workers

The Gig Workers dataset contains one completely empty row.

**Handling:** The row will be removed during ingestion.

### 2. Shifted columns in Gig Workers

The Isha Chopra record contains values shifted into the wrong columns.

The observed row contains:

- `react, javascript, mysql` in `email_id`
- `ISHA.CHOPRA95@MAILTEST.EXAMPLE.ORG` in `worker_name`
- `Isha Chopra` in `rate`
- `1406/hr` in `location`
- `Pune` in `status`
- `active` in `skill_tags`

The values form a valid record when restored to their expected columns.

**Handling:** The pipeline will detect and repair this malformed row using field validation rather than relying on its row number.

### 3. Mixed rate formats in Gig Workers

The `rate` field contains both hourly and monthly representations, such as `1415/hr` and `15k/month`.

**Handling:** The value will be parsed into a numeric amount and a rate period.

### 4. Inconsistent status casing

The Gig Workers dataset contains values such as `Active`, `ACTIVE`, and `active`.

**Handling:** Status values will be normalized to a canonical lowercase representation.

### 5. Invalid status value

`Pune` appears as a value in the `status` column. This is evidence of the shifted Isha Chopra record.

**Handling:** The malformed row will be repaired before status normalization.

### 6. Embedded header row in CBNexus

The CBNexus dataset contains the column headers as an actual data row.

**Handling:** The embedded header row will be detected and removed.

### 7. Inconsistent verification values

The CBNexus `Verified` field contains `Y`, `Yes`, `yes`, `N`, and `No`.

**Handling:** These values will be normalized into boolean values.

### 8. Inconsistent phone representations

Phone numbers appear in multiple formats, including:

- 10-digit numbers
- 12-digit numbers beginning with `91`
- numbers formatted with `+91-`

**Handling:** Phone numbers will be normalized to a common 10-digit representation for matching.

### 9. Duplicate records in Naukri

The Naukri dataset contains an exact duplicate for Rohit Verma.

**Handling:** Exact duplicate records will be removed.

### 10. Alternate email for Nikhil Chopra

Two Naukri records have the same name, phone, city, and skills but different email addresses.

**Handling:** They will be treated as one person while preserving the alternate email information.

### 11. Name-only matching is unsafe

The datasets contain people with identical names but different identifying information.

For example, multiple Arjun Mehta records have different phone numbers and/or email addresses.

**Handling:** Name alone will not be used as sufficient evidence for automatic merging.

### 12. Ambiguous cross-source records

Some CBNexus records have corresponding names in Gig Workers but no common strong identifier such as email or phone.

**Handling:** These records will not be automatically merged based only on name and city.

## Matching Strategy

The initial entity-resolution strategy will prioritize strong identifiers:

1. Exact normalized email
2. Exact normalized phone
3. Strong combinations such as phone + normalized name
4. Email + normalized name

Name-only matches will not automatically merge records.

The strategy intentionally favors avoiding false merges over aggressively combining uncertain records.
## Data Quality Summary

The investigation identified:
- 1 completely empty Gig Worker row
- 1 shifted Gig Worker record
- Mixed hourly/monthly rate formats
- Inconsistent status casing
- 1 embedded CBNexus header row
- Inconsistent verification representations
- Multiple phone-number formats
- Duplicate Naukri records
- Potential same-name false matches across sources

The cleaning and entity-resolution rules described above will be implemented in the ETL pipeline and validated against the source data before loading the unified database.

