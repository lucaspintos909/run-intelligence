# S03: Health Log Query Commands — UAT

**Milestone:** M001
**Written:** 2026-05-30T18:36:00.278Z

# S03: Health Log Query Commands — UAT

**Milestone:** M001
**Written:** 2026-05-30

## UAT Type

- UAT mode: **live-runtime**
- Why this mode is sufficient: The CLI commands have direct database access and can be tested with real commands; tests already verify core functionality

## Preconditions

- Database initialized with health log entries (can be empty for edge case tests)
- Run from the run-intelligence project directory

## Smoke Test

```bash
python3 -m run_intelligence --help | grep -E "list-health-logs|view-health-log"
```

Expected: Both commands appear in main help output

## Test Cases

### 1. List Health Logs Command

1. Run `python3 -m run_intelligence list-health-logs`
2. **Expected:** Returns exit code 0, displays formatted list of health log entries (or "No health log entries found" if empty)

### 2. List Health Logs with Limit

1. Run `python3 -m run_intelligence list-health-logs --limit 5`
2. **Expected:** Returns exit code 0, shows at most 5 entries

### 3. View Health Log by ID

1. Run `python3 -m run_intelligence view-health-log --id 1` (use valid ID from list)
2. **Expected:** Returns exit code 0, displays detailed view of that entry

### 4. View Health Log with Invalid ID

1. Run `python3 -m run_intelligence view-health-log --id 99999`
2. **Expected:** Returns exit code 2, displays error message with [ERROR] prefix

### 5. View Health Log Missing Required Option

1. Run `python3 -m run_intelligence view-health-log` (no --id)
2. **Expected:** Returns exit code 2, shows "required" error message

### 6. Help Commands

1. Run `python3 -m run_intelligence list-health-logs --help`
2. Run `python3 -m run_intelligence view-health-log --help`
3. **Expected:** Both return exit code 0 with proper usage information

## Edge Cases

### Empty Database

- Run `python3 -m run_intelligence list-health-logs`
- **Expected:** "No health log entries found" message, exit code 0

### Invalid ID Type

- Run `python3 -m run_intelligence view-health-log --id abc`
- **Expected:** Exit code 2, validation error message

## Failure Signals

- Exit code 1 indicates database error
- Exit code 2 indicates validation error
- Missing commands in `--help` output indicates implementation issue
- [ERROR] prefix missing from error messages indicates pattern deviation

## Not Proven By This UAT

- Integration with run association features (covered by S02)
- Performance under large datasets (not a current concern)

## Notes for Tester

- Use actual database for testing or mock as needed
- The --limit default is 50 entries
- Error messages use [ERROR] prefix for consistency with other CLI commands
