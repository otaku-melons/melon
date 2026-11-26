from pathlib import Path
from typing import override

from pydantic_settings import (
	BaseSettings,
	DotEnvSettingsSource,
	EnvSettingsSource,
	PydanticBaseSettingsSource,
	SettingsConfigDict,
)

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
	ATOMIC_WRITE: bool = True
	TEMP_DIR: Path = Path("temp")
	USE_CACHE: bool = True

	@override
	@classmethod
	def settings_customise_sources(
		cls,
		settings_cls: type[BaseSettings],
		init_settings: PydanticBaseSettingsSource,
		env_settings: PydanticBaseSettingsSource,
		dotenv_settings: PydanticBaseSettingsSource,
		file_secret_settings: PydanticBaseSettingsSource,
	) -> tuple[PydanticBaseSettingsSource, ...]:

		return (
			init_settings,
			EnvSettingsSource(settings_cls, env_prefix = "MELON_"),
			DotEnvSettingsSource(settings_cls, env_file = ".env", env_prefix = ""),
			file_secret_settings,
		)
