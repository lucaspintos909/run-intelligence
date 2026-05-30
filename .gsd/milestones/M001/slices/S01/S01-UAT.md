# S01: Interactive Health Logging CLI — UAT

**Milestone:** M001
**Written:** 2026-05-30T18:17:17.076Z

# S01: Interactive Health Logging CLI — UAT

**Milestone:** M001
**Written:** 2026-05-30

## UAT Type

- **UAT mode:** live-runtime
- **Why this mode is sufficient:** This slice adds a CLI command that can be tested by running the command and verifying prompts appear and data gets persisted.

## Preconditions

- Database is accessible (requires LLM_API_KEY environment variable for DB session)
- Python dependencies installed

## Smoke Test

```bash
python3 -m run_intelligence log-health --help
```

Expected: Help text showing all options (--date, --peak-flow, --sleep-quality, --post-run-rpe, --asthma-symptoms, --saba-use, --notes, --verbose)

## Test Cases

### 1. Non-interactive mode with all arguments

1. Run: `python3 -m run_intelligence log-health --date 2026-05-30 --peak-flow 450 --sleep-quality 4 --post-run-rpe 6 --asthma-symptoms 2 --saba-use false --notes "Good day"`
2. **Expected:** Output "Logged: 2026-05-30 (peak_flow=450, sleep=4, rpe=6, symptoms=2, saba=no)" or similar success message

### 2. Interactive mode detection

1. Run: `python3 -m run_intelligence log-health` (no arguments)
2. **Expected:** Prompts appear for each field in order: Date, Peak flow, Sleep quality, Post-run RPE, Asthma symptoms, Rescue inhaler used, Additional notes

### 3. Input validation in interactive mode

1. Run interactive mode and enter invalid values (e.g., sleep quality = 10)
2. **Expected:** Validation error message with guidance (e.g., "Value must be between 1 and 5")

### 4. Verbose mode

1. Run: `python3 -m run_intelligence log-health --peak-flow 420 --verbose`
2. **Expected:** Detailed output showing saved field values and entry ID

### 5. Default values

1. Run interactive mode and press Enter (accept defaults) for date
2. **Expected:** Date defaults to today's date

## Edge Cases

### Empty input for optional fields

1. Run interactive mode and press Enter for all optional fields
2. **Expected:** Entry created with only required/default values, no errors

### Invalid date format

1. Run: `python3 -m run_intelligence log-health --date invalid-date`
2. **Expected:** Error message "Invalid date format: invalid-date. Use YYYY-MM-DD."

## Failure Signals

- Error messages go to stderr (not stdout)
- Exit code 1 = database error
- Exit code 2 = invalid arguments
- Missing prompts = interactive mode detection broken

## Not Proven By This UAT

- Database persistence verification (would need to query DB after creation)
- Run association (S02 feature)
- Query/list commands (S03 feature)
- Full error recovery in all edge cases

## Notes for Tester

- Requires LLM_API_KEY environment variable for database connection
- Interactive mode uses typer.prompt() which works in terminal but may not work in all IDE test runners
- Boolean saba_use uses typer.confirm() for yes/no prompting
