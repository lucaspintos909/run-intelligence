# Deferred Work

## Deferred from: code review of 1-1-project-initialization (2026-05-12)

- CLI commands accept unvalidated raw strings [src/run_intelligence/cli.py:26] — deferred, pre-existing
- purge command dangerously lightweight [src/run_intelligence/cli.py:58] — deferred, pre-existing
- Hardcoded thresholds unstructured and undocumented [src/run_intelligence/config.py:19] — deferred, pre-existing

## Deferred from: code review of 1-1-project-initialization (2026-05-13)

- CLI commands are stub implementations only print messages [src/run_intelligence/cli.py] — deferred, pre-existing (implementación completa en historias posteriores)
- config.py hardcoded constants should be user-configurable [src/run_intelligence/config.py:19-29] — deferred, pre-existing (arquitectura decisions)
- Disclaimer hardcoded English, no i18n infrastructure [src/run_intelligence/config.py:31-35] — deferred, pre-existing (decisión de localización)
- Edge cases: non-existent file/dir paths, invalid date formats, out-of-range severity on CLI commands [src/run_intelligence/cli.py:19-52] — deferred, pre-existing (stubs)
- No asthma-related logic in initial scaffold [src/run_intelligence/] — deferred, Story 1.5 implementa

## Deferred from: code review of 1-2-database-schema (2026-05-18)

- JSON columns lack Pydantic validation at application layer [src/run_intelligence/db/repository.py] — deferred, application layer (pipeline, agents) not built yet in Story 1.2
