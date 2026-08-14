# Task 2 — n8n AI Skill Tagging Automation

## Overview

This task implements a no-code/low-code automation using **n8n** to automatically classify people's professional skill profiles into predefined categories using an LLM and write the classification back to the connected data table.

The automation was built as part of the ConsultBae take-home assignment.

The workflow demonstrates:

- Working with a database/data table in n8n
- Processing multiple records
- Using an LLM through n8n's AI Agent node
- Applying a structured classification prompt
- Updating the original record with the AI-generated category
- Using a loop to process records individually
- Building the solution without a custom Python/JavaScript implementation

---

## Task Requirement

The assignment required building **one working automation** using a no-code/low-code automation platform such as:

- n8n
- Make
- Zapier

One of the suggested approaches was:

> Use an LLM step to automatically tag each person's skill category and write the result back.

This implementation follows that approach using **n8n + Google Gemini**.

---

# Automation Objective

The objective is to take a person's existing professional skill information, send it to an LLM for classification, and store the resulting category back against the same person.

### High-level flow

```text
Manual Workflow Trigger
        |
        v
   Get row(s)
        |
        v
 Loop Over Items
        |
        v
    AI Agent
        |
        v
 Google Gemini
        |
        v
   Update row(s)
        |
        +------------------+
        |                  |
        +---- Loop Back ---+
```

The workflow processes each person individually.

---

# Data Source

The workflow uses the n8n Data Table:

```text
consultbae_people
```

The table contains professional profile information such as:

* `entity_id`
* `name`
* `naukri_skills`
* `gig_skills`
* `skill_category`
* `id`
* `createdAt`
* `updatedAt`

Example record:

```text
entity_id: ENTITY_0014
name: Arjun Mishra
naukri_skills: React, Docker, JavaScript
gig_skills: react, docker, javascript
skill_category: null
```

After processing:

```text
entity_id: ENTITY_0014
name: Arjun Mishra
naukri_skills: React, Docker, JavaScript
gig_skills: react, docker, javascript
skill_category: web dev
```

The existing `entity_id` is used to identify the record that needs to be updated.

---

# Workflow Components

## 1. Manual Trigger

### Node

```text
When clicking 'Execute workflow'
```

### Purpose

This node starts the workflow manually during development and testing.

A manual trigger was selected because the primary requirement was to demonstrate a working automation rather than deploy it as a scheduled production process.

---

# 2. Get Row(s)

### Node

```text
Get row(s)
```

### Data Table

```text
consultbae_people
```

### Purpose

This node retrieves the people records that need to be classified.

The workflow can retrieve multiple records from the data table.

Example input:

```text
ENTITY_0014
Arjun Mishra
React, Docker, JavaScript
```

The retrieved records are passed to the next stage.

---

# 3. Loop Over Items

### Node

```text
Loop Over Items
```

### Purpose

The records are processed individually rather than sending the entire dataset to the LLM in a single request.

Conceptually:

```text
Record 1 → AI classification → Update
Record 2 → AI classification → Update
Record 3 → AI classification → Update
...
```

This makes the workflow suitable for record-level processing.

The output of the `Get row(s)` node is connected to the input of the loop.

The loop's processing path connects to the AI Agent and then to the Update Row node.

After an item is updated, the workflow loops back and processes the next record.

---

# 4. AI Agent

### Node

```text
AI Agent
```

### Purpose

The AI Agent is responsible for classifying the person's professional skill profile.

The workflow uses a predefined prompt that instructs the LLM to select exactly one category.

The classification categories used are:

```text
1. automation-heavy
2. web dev
3. data
```

The prompt is designed to restrict the model's response to one of these categories.

---

# 5. Google Gemini Chat Model

### Node

```text
Google Gemini Chat Model
```

The Gemini model is connected to the AI Agent through n8n's AI model connection.

The model receives the person's professional skill information through the AI Agent and returns a classification.

Example:

```text
React, Docker, JavaScript
```

may result in:

```text
web dev
```

Another profile containing automation-oriented technologies may result in:

```text
automation-heavy
```

---

# 6. Update Row(s)

### Node

```text
Update row(s)
```

### Data Table

```text
consultbae_people
```

### Purpose

The AI-generated classification is written back into the original data table.

The workflow matches the record using:

```text
entity_id
```

For example:

```text
entity_id = ENTITY_0014
```

The `skill_category` field is then updated with the AI result.

Example:

### Before

```text
ENTITY_0014 | Arjun Mishra | React, Docker, JavaScript | null
```

### After

```text
ENTITY_0014 | Arjun Mishra | React, Docker, JavaScript | web dev
```

This creates a complete automation loop from reading the record to updating the same record.

---

# Complete Workflow

The final workflow can be represented as:

```text
┌─────────────────────────────────────┐
│ Manual Workflow Trigger             │
│ "When clicking Execute workflow"    │
└─────────────────┬───────────────────┘
                  │
                  v
┌─────────────────────────────────────┐
│ Get row(s)                           │
│ Data Table: consultbae_people       │
└─────────────────┬───────────────────┘
                  │
                  v
┌─────────────────────────────────────┐
│ Loop Over Items                      │
│ Process one person at a time        │
└─────────────────┬───────────────────┘
                  │
                  v
┌─────────────────────────────────────┐
│ AI Agent                             │
│ Skill profile classification         │
└─────────────────┬───────────────────┘
                  │
                  │ AI Model
                  v
┌─────────────────────────────────────┐
│ Google Gemini Chat Model             │
│ Returns one category                 │
└─────────────────┬───────────────────┘
                  │
                  v
┌─────────────────────────────────────┐
│ Update row(s)                        │
│ Match using entity_id                │
│ Update skill_category                │
└─────────────────┬───────────────────┘
                  │
                  └───────────────┐
                                  │
                                  v
                         Next item in loop
```

---

# Example Classification

## Example 1

### Input

```text
Name:
Arjun Mishra

Skills:
React, Docker, JavaScript
```

### AI output

```text
web dev
```

### Database result

```text
skill_category = web dev
```

---

## Example 2

The workflow was also tested with profiles containing automation-oriented skills.

The AI returned:

```text
automation-heavy
```

The result was then passed to the Update Row node.

---

# Why Use an LLM?

Traditional rule-based classification would require manually maintaining a large collection of conditions such as:

```text
IF React → web dev
IF JavaScript → web dev
IF Selenium → automation-heavy
IF Python + SQL → data
...
```

That approach becomes increasingly difficult to maintain as the number of skills grows.

Using an LLM allows the workflow to interpret combinations of skills and classify the overall professional profile.

The classification rules are still controlled through the prompt and the predefined categories.

---

# No-Code / Low-Code Implementation

A key requirement of this task was that the solution should demonstrate practical experience with a no-code/low-code automation platform.

The main workflow logic was implemented through n8n nodes:

```text
Manual Trigger
       ↓
Get Row(s)
       ↓
Loop Over Items
       ↓
AI Agent
       ↓
Google Gemini
       ↓
Update Row(s)
```

No standalone Python or JavaScript program was created to perform the automation.

The logic is represented visually inside n8n.

---

# Error / Quota Handling During Testing

The workflow was successfully tested with individual records and smaller executions.

During a larger execution, Google Gemini's free-tier request quota was reached.

The n8n execution reported a `429 Too Many Requests` / quota-related response from the Gemini API.

This is an external model-provider limitation rather than a workflow logic failure.

The important workflow components were therefore validated independently:

1. Data was successfully retrieved.
2. Records were successfully passed through the loop.
3. The AI Agent successfully classified records.
4. Gemini successfully returned classifications during available quota.
5. The Update Row node successfully wrote classifications back to the data table.
6. The complete workflow structure was verified in n8n.

For a production implementation, this would be addressed using appropriate API quotas, batching/rate limiting, retry policies, or a production LLM plan.

---

# Testing

The workflow was tested by executing it directly from the n8n editor.

A successful execution demonstrated the following path:

```text
Data Table
    ↓
Get Row(s)
    ↓
Loop Over Items
    ↓
AI Agent
    ↓
Gemini Classification
    ↓
Update Row
    ↓
Updated Data Table
```

Example successful database update:

```text
ENTITY_0014
Arjun Mishra
React, Docker, JavaScript
web dev
```

This confirms that the AI-generated result was not only produced but also persisted back to the source data.

---

# Repository Structure

Task 2 is stored inside the main ConsultBae assignment repository.

```text
consultbae-assignment/
│
├── data/
├── reports/
├── src/
│
├── task2/
│   ├── README.md
│   │
│   ├── workflow/
│   │   └── n8n-skill-tagging.json
│   │
│   └── screenshots/
│       ├── workflow.png
│       ├── ai-classification.png
│       └── updated-data.png
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

# Workflow Export

The complete n8n workflow is included in:

```text
task2/workflow/n8n-skill-tagging.json
```

This allows the workflow structure to be inspected and imported into another n8n environment.

Credentials and API keys should not be committed to the repository.

When importing the workflow into another environment, the required credentials must be configured separately in n8n.

---

# Screenshots

The `screenshots` directory contains evidence of the working automation.

### Workflow

```text
task2/screenshots/workflow.png
```

Shows the complete n8n workflow and node connections.

### AI Classification

```text
task2/screenshots/ai-classification.png
```

Shows an AI Agent classification result.

### Updated Data

```text
task2/screenshots/updated-data.png
```

Shows the classification written back to the `consultbae_people` data table.

---

# Key Learning / Takeaways

This task provided hands-on experience with:

* n8n workflow design
* No-code/low-code automation
* n8n Data Tables
* Record-level processing
* Looping through multiple items
* AI Agent nodes
* LLM integration
* Prompt-based classification
* Connecting an LLM to an automation workflow
* Updating source data from AI output
* Debugging workflow executions
* Handling API quota limitations
* Exporting and version-controlling n8n workflows

---

# Possible Production Improvements

If this automation were moved from a take-home demonstration to production, I would consider:

### 1. Trigger-based execution

Replace the manual trigger with a production trigger such as:

```text
Webhook
Email
Google Drive
Scheduled Trigger
```

depending on how new records enter the system.

### 2. Rate limiting

Limit the number of LLM requests sent within a given period to avoid provider rate limits.

### 3. Retry handling

Add controlled retries for temporary API failures such as:

```text
429 Too Many Requests
5xx API errors
```

### 4. Structured output

Enforce a strict output schema so that the AI can only return one of the supported categories.

For example:

```json
{
  "skill_category": "web dev"
}
```

### 5. Logging

Record:

* entity ID
* classification result
* execution timestamp
* success/failure status
* error message when applicable

### 6. Production credentials

Use properly managed credentials rather than exposing API keys in workflow files.

### 7. Monitoring

Monitor:

* workflow failures
* LLM latency
* API quota
* classification failures
* records processed
* records updated

---

# Conclusion

This implementation demonstrates a complete no-code/low-code AI automation using n8n.

The workflow reads professional skill profiles from the `consultbae_people` data table, processes each person individually, uses an AI Agent backed by Google Gemini to classify the profile into a predefined skill category, and writes the result back to the same record.

The resulting automation is:

```text
Read Data
   ↓
Process Each Person
   ↓
AI Skill Classification
   ↓
Write Result Back
```

The exported n8n workflow is included in the repository so the automation can be reviewed and reproduced independently.