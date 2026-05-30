# S02: Run Association — UAT

**Milestone:** M001
**Written:** 2026-05-30T18:28:21.441Z

# S02: Run Association — UAT

**Milestone:** M001
**Written:** 2026-05-30

## UAT Type
- **UAT mode:** live-runtime
- **Why this mode is sufficient:** CLI integration requires actual command execution to verify user-facing behavior

## Preconditions
- Python environment with run_intelligence installed
- LLM_API_KEY set (can use mock value for testing)

## Smoke Test
```bash
python3 -m run_intelligence log-health --help | grep associate-run
```
**Expected:** `--associate-run` option appears in help output

## Test Cases

### 1. Associate with valid run ID
1. Run: `python3 -m run_intelligence log-health --date 2026-01-15 --peak-flow 450 --associate-run 1`
2. **Expected:** Exit code 0, health entry created with run_id=1

### 2. Associate with invalid run ID
1. Run: `python3 -m run_intelligence log-health --date 2026-01-15 --peak-flow 450 --associate-run 99999`
2. **Expected:** Exit code 2, error message "Run with ID 99999 not found"

### 3. Create without association
1. Run: `python3 -m run_intelligence log-health --date 2026-01-15 --peak-flow 450`
2. **Expected:** Exit code 0, health entry created with run_id=None

## Edge Cases
- **No runs available:** Interactive mode shows "No runs available" message
- **Run ID validation:** Only accepts existing run IDs (verified via database)

## Failure Signals
- Exit code 1: Database or write error
- Exit code 2: Invalid arguments (including invalid run ID)
- Missing --associate-run option in help: Implementation incomplete

## Not Proven By This UAT
- Query/display of health entries with run associations (S03)
- Cross-referencing health data with run metrics (future feature)

## Notes for Tester
- Use `LLM_API_KEY=mock` to bypass LLM configuration requirement
- Interactive mode activates only when no arguments are provided to log-health
