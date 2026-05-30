---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T02: Added interactive run selection prompt to log-health command

In interactive mode, if --associate-run not provided, prompt user to select from available runs. Show run IDs, dates, and optionally distance. Handle case where no runs exist (show helpful message). Uses RunRepository.get_runs() to list available runs.

## Inputs

- None specified.

## Expected Output

- `/home/lpintos/.gsd/projects/e51dd9a6b959/worktrees/M001/src/run_intelligence/cli.py`

## Verification

python3 -m run_intelligence log-health --help
