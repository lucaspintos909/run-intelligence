---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T01: Implemented list-health-logs and view-health-log CLI commands

Add two new CLI commands to cli.py: (1) list-health-logs with --limit option that calls HealthLogRepository.get_entries(limit) and prints formatted list, (2) view-health-log with --id option that calls HealthLogRepository.get_entry(id) and prints entry details. Follow existing CLI patterns: exit code 2 for validation errors (invalid ID), exit code 1 for database errors, use sys.stdout.write() and sys.stderr.write() with [ERROR] prefixes.

## Inputs

- `/home/lpintos/.gsd/projects/e51dd9a6b959/worktrees/M001/src/run_intelligence/cli.py`
- `/home/lpintos/.gsd/projects/e51dd9a6b959/worktrees/M001/src/run_intelligence/db/repository.py`

## Expected Output

- `/home/lpintos/.gsd/projects/e51dd9a6b959/worktrees/M001/src/run_intelligence/cli.py`

## Verification

python3 -m run_intelligence list-health-logs --help && python3 -m run_intelligence view-health-log --help
