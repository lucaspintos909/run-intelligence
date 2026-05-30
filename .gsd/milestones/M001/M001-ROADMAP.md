# M001: Health Logging

**Vision:** Enable users to log health data interactively via CLI and associate it with runs for cross-referencing with objective run metrics

## Success Criteria

- Interactive health logging flow works end-to-end (prompt → validate → persist)
- Health log entries can be associated with existing runs
- Health log data is queryable via CLI (list, view)
- Error handling works for invalid inputs and missing runs
- Unit tests pass for core logic
- Integration tests verify CLI → DB flow

## Slices

- [ ] **S01: Interactive Health Logging CLI** `risk:high` `depends:[]`
  > After this: User can run `python -m run_intelligence --log-health` and input peak flow, sleep quality, RPE, asthma symptoms (0-3), SABA use, and notes interactively

- [ ] **S02: Run Association** `risk:medium` `depends:[S01]`
  > After this: User can associate a health log entry with an existing run via `--associate-run <id>`

- [ ] **S03: Health Log Query Commands** `risk:low` `depends:[S02]`
  > After this: User can list and view health log entries via CLI

## Boundary Map

"### S01 → S02\n\nProduces:\n- HealthLogService with create_health_log() method\n\nConsumes:\n- HealthLog model (db/models.py)\n\n### S02 → S03\n\nProduces:\n- Health log with run_id association\n\nConsumes:\n- RunService for run validation"
