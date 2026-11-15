from typing import TYPE_CHECKING

from dublib.functions.data import dictionary
from dublib.functions.filesystem import json

from .enums import ExportResult, ExportStrategy

if TYPE_CHECKING:
	from pathlib import Path

	from .. import SystemObjects

def export_package_settings(
	system_objects: "SystemObjects",
	package_name: str,
	base_settings: dict,
	strategy: ExportStrategy = ExportStrategy.Skip,
	) -> ExportResult:
	"""
	Export package settings.

	Args:
		system_objects (SystemObjects): System objects collection.
		package_name (str): Package name.
		base_settings (dict): Base settings
		strategy (ExportStrategy): Settings export strategy.

	Returns:
		ExportResult: Export result.
	"""

	if not base_settings:
		return ExportResult.Missing

	is_atomic_write: bool = system_objects.options.JSON_ATOMIC_WRITE

	# Create only if default directory.
	if system_objects.options.CONFIGS_DIR.as_posix() == "configs":
		system_objects.options.CONFIGS_DIR.mkdir(exist_ok = True)

	if "_" in package_name:
		parser_name, extension_name = package_name.split("_", maxsplit = 1)
		storage_path: Path = system_objects.options.CONFIGS_DIR / parser_name / f"{extension_name}.json"
	else:
		storage_path: Path = system_objects.options.CONFIGS_DIR / package_name / f"{package_name}.json"

	if storage_path.exists():

		match strategy:
			case ExportStrategy.Skip:
				return ExportResult.AlreadyExists

			case ExportStrategy.Overwrite:
				json.write(storage_path, base_settings, atomic = is_atomic_write)
				return ExportResult.Overwtitten

			case ExportStrategy.Merge:
				CurrentConfig: dict = json.read(storage_path)
				Config = dictionary.deep_merge(base_settings, CurrentConfig, uniqueness = True)
				json.write(storage_path, Config, atomic = is_atomic_write)
				return ExportResult.Merged

	json.write(storage_path, base_settings, atomic = is_atomic_write)

	return ExportResult.Exported
