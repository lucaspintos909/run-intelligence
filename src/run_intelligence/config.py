"""Configuration module using Pydantic BaseSettings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    LLM_API_KEY: str
    LLM_MODEL: str = "gpt-4"
    LLM_ENDPOINT: str = "https://api.openai.com/v1"
    DATA_DIR: str = "data"
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
