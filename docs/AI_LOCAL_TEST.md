# Local AI Project Test

This branch uses a separate local SQLite database. It does not change the AWS school-test system or its data.

## Branches

- `codex/real-project-test`: normal product testing with the existing local database.
- `codex/ai-project-test`: synthetic 10-student AI learning-profile test.
- `master`: the last GitHub/AWS baseline unless intentionally updated later.

## Prepare the 10-student dataset

From PowerShell at the repository root:

```powershell
.\scripts\prepare-ai-project-test.ps1
```

The script creates:

- `backend/db.ai-project-test.sqlite3`: isolated local AI database; ignored by Git.
- `outputs/ai_project/ai_student_learning_profile_10.json`: readable AI test dataset.

The admin login is `ai_admin` / `ai-test-2026`.

All ten parent test accounts use password `ai-test-2026`. Usernames are `ai_parent_01` through `ai_parent_10`.

## Run the AI test system locally

```powershell
.\scripts\run-ai-project-local.ps1
```

Then open `http://127.0.0.1:8000/adminLogin`.

## Return to real-project testing

Switch to `codex/real-project-test` and start Django normally without setting `CSAA_DB_PATH`. The system will use `backend/db.sqlite3` as before.

## JSON scope

The export contains synthetic student profiles, courses, attendance, absences, makeup status, teacher comments, summary metrics, and an `ai_input` block. It contains no production student information and should remain the only dataset shared with student contributors.
