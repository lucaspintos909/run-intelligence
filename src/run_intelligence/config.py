"""Configuration module using Pydantic BaseSettings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    LLM_API_KEY: str
    LLM_MODEL: str = "gpt-4"
    LLM_ENDPOINT: str = "https://api.openai.com/v1"
    DATA_DIR: str = "data"
    DB_PATH: str = "data/run_intelligence.db"
    PROFILES_DIR: str = "profiles"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


BIE_TEMP_THRESHOLD: float = 25.0
BIE_HUMIDITY_HIGH: float = 70.0
BIE_AQI_HIGH: float = 100.0

HR_REST_MIN: int = 40
HR_REST_MAX: int = 100
HR_MAX_AGE_PREDICTED: int = 220

HYPOTHESIS_DRIFT_THRESHOLD: float = 0.15
HYPOTHESIS_HRV_LOW: int = 30
HYPOTHESIS_CADENCE_VARIANCE_MAX: float = 0.1

WELLNESS_DISCLAIMER = (
    "This application provides general fitness tracking information only. "
    "It is not a medical device and should not be used for medical diagnosis. "
    "Always consult with a healthcare professional before making changes to your fitness routine, "
    "asthma management, or if you experience any concerning symptoms."
)

FIT_PARSING = {
    "gps_drift_mps": 50.0,
    "max_records": 10000,
    "max_duration_seconds": 7200,
}

HR_LIMITS = {
    "rest_min": HR_REST_MIN,
    "rest_max": HR_REST_MAX,
    "age_predicted_max": HR_MAX_AGE_PREDICTED,
    "artifact_threshold_bpm": 220,
    "gps_drift_mps": 50.0,
}

HR_ZONES = {
    "z1": (50, 60),
    "z2": (60, 70),
    "z3": (70, 80),
    "z4": (80, 90),
    "z5": (90, 100),
}

DEFAULT_AGE = 30

ELEVATION_NOISE_FILTER_METERS = 2.0

ASTHMA_METRICS = {
    "hr_pace_drift": {
        "min_hr_range_bpm": 20.0,
    },
    "hr_variability": {
        "min_hr_range_bpm": 10.0,
    },
}

HR_ZONE_ANOMALY_THRESHOLD: float = 0.40

CADENCE_CHANGE_THRESHOLD_PCT: float = 0.20

LOW_CONFIDENCE_THRESHOLD: float = 0.5

# Confidence deduction weights per data quality issue
CONFIDENCE_DEDUCTION_THRESHOLD_EXCEEDED: float = 0.15
CONFIDENCE_DEDUCTION_SPIKE: float = 0.10
CONFIDENCE_DEDUCTION_GPS_DRIFT: float = 0.10
CONFIDENCE_DEDUCTION_CADENCE_INCONSISTENCY: float = 0.05

# HR spike detection: max - avg must exceed this to flag as spike
HR_SPIKE_THRESHOLD_BPM: float = 30.0

# GPS drift pace-consistency: speed within this factor of expected pace is not drift
GPS_DRIFT_PACE_FACTOR: float = 3.0

# Cadence pace-adjustment parameters
CADENCE_PACE_BASELINE_SPK: float = 300.0  # 5:00/km reference pace in sec/km
CADENCE_PACE_FACTOR_MIN: float = 0.5
CADENCE_PACE_FACTOR_MAX: float = 2.0
CADENCE_PACE_MARGIN: float = 1.5  # allow 50% margin for pace-explained
