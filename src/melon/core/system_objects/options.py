from pathlib import Path

from pydantic import AnyHttpUrl
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
	REPOS: AnyHttpUrl = AnyHttpUrl("https://github.com/otaku-melons/melon")
	TEMP_DIR: Path = Path("temp")
	TEMPLATE_REPOS: AnyHttpUrl = AnyHttpUrl("ttps://github.com/otaku-melons/.parser-template")
	USE_CACHE: bool = True
