# pipeline/fcmax.py
from typing import Optional


def fcmax_tanaka(age: int) -> int:
    """Tanaka (2001, JACC): 208 - 0.7 × age. More accurate than Fox for adults 30-60."""
    return round(208 - 0.7 * age)


def p95_hr(hr_values: list[int]) -> int:
    """95th percentile HR — robust FCmax estimator from submaximal efforts."""
    if not hr_values:
        return 0
    sorted_hr = sorted(hr_values)
    idx = int(len(sorted_hr) * 0.95)
    return sorted_hr[idx]


def get_active_fcmax(profile: dict) -> tuple[int, str]:
    """
    Priority chain:
    1. fcmax_manual (HIGH) — from protocol test
    2. fcmax_observed (MEDIUM) — only if > estimated
    3. fcmax_estimated (LOW) — Tanaka formula
    """
    if profile.get('fcmax_manual'):
        return profile['fcmax_manual'], 'HIGH'
    observed = profile.get('fcmax_observed')
    estimated = profile.get('fcmax_estimated', 0)
    if observed and observed > estimated:
        return observed, 'MEDIUM'
    return estimated, 'LOW'


def should_update_fcmax_observed(hr_values: list[int], current_observed: Optional[int]) -> bool:
    """Return True if p95 of current session exceeds known fcmax_observed."""
    session_p95 = p95_hr(hr_values)
    if current_observed is None:
        return session_p95 > 0
    return session_p95 > current_observed
