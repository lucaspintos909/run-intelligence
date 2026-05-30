---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T01: Added --associate-run CLI option with validation for linking health entries to runs

Add --associate-run option to log_health command in cli.py. Update interactive_mode detection to include associate_run parameter. Validate run exists via RunRepository.get_run() before creating entry. Pass run_id to create_entry() - repository already supports this.

## Inputs

- None specified.

## Expected Output

- `/home/lpintos/.gsd/projects/e51dd9a6b959/worktrees/M001/src/run_intelligence/cli.py`

## Verification

python3 -m run_intelligence log-health --help
