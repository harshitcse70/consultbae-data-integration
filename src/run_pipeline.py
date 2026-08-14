import subprocess
import sys
from pathlib import Path


# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"


# ============================================================
# PIPELINE STEPS
# ============================================================

STEPS = [
    (
        "Clean Naukri applicants",
        "clean_naukri.py"
    ),
    (
        "Clean Gig Workers",
        "clean_data.py"
    ),
    (
        "Clean CBNexus contacts",
        "clean_cbnexus.py"
    ),
    (
        "Resolve entities",
        "entity_resolution.py"
    ),
    (
        "Build master entities",
        "build_master.py"
    ),
    (
        "Validate master entities",
        "final_validation.py"
    ),
    (
        "Load SQLite database",
        "load_database.py"
    ),
]


# ============================================================
# RUN ONE STEP
# ============================================================

def run_step(description, script):

    print()
    print("=" * 70)
    print(f"STEP: {description}")
    print("=" * 70)

    script_path = SRC_DIR / script

    if not script_path.exists():
        raise FileNotFoundError(
            f"Required script not found: {script_path}"
        )

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=BASE_DIR
    )

    if result.returncode != 0:

        print()
        print("=" * 70)
        print(f"PIPELINE FAILED: {description}")
        print("=" * 70)

        raise SystemExit(result.returncode)

    print()
    print(f"✓ {description} completed successfully")


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print()
    print("=" * 70)
    print("CONSULTBAE DATA INTEGRATION PIPELINE")
    print("=" * 70)

    print()
    print(f"Project directory:")
    print(BASE_DIR)

    print()
    print(f"Python executable:")
    print(sys.executable)

    # --------------------------------------------------------
    # Run every pipeline stage
    # --------------------------------------------------------

    for description, script in STEPS:

        run_step(
            description,
            script
        )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 70)

    print()
    print("Final outputs:")

    outputs = [
        BASE_DIR / "data" / "cleaned_naukri_applicants.csv",
        BASE_DIR / "data" / "cleaned_gig_workers.csv",
        BASE_DIR / "data" / "cleaned_cbnexus_contacts.csv",
        BASE_DIR / "data" / "master_entities.csv",
        BASE_DIR / "data" / "consultbae.db",
        BASE_DIR / "reports" / "entity_matches.csv",
        BASE_DIR / "reports" / "entity_candidates.csv",
        BASE_DIR / "reports" / "entity_transitive_matches.csv",
        BASE_DIR / "reports" / "entity_resolution_summary.csv",
    ]

    print()

    for output in outputs:

        if output.exists():

            print(f"✓ {output.relative_to(BASE_DIR)}")

        else:

            print(f"✗ MISSING: {output.relative_to(BASE_DIR)}")

    print()
    print("=" * 70)
    print("END OF PIPELINE")
    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()