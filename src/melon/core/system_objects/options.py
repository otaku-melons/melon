from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

class Options(BaseSettings):
	"""Melon environment options."""

	model_config = SettingsConfigDict(
		case_sensitive = True,
		env_file = ".env",
		env_prefix = "MELON_",
		frozen = True,
	)

	CONFIGS_DIR: Path = Path("configs")
	DEBUG: bool = False
	DEFAULT_OUTPUT_DIR: Path = Path("output")
	JSON_ATOMIC_WRITE: bool = True
	TEMP_DIR: Path = Path("temp")
	USE_CACHE: bool = True
