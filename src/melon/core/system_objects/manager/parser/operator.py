import importlib
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from dublib.functions.data import dictionary
from dublib.functions.decorators import run_before_method
from dublib.functions.filesystem import json

from .....core import exceptions
from ....base.parser.components.manifest import ParserManifest
from ....base.parser.components.settings import ParserSettings
from .enums import ExportResult, ExportStrategy
from .extensions import ExtensionsOperator
from .linter import CheckResult, Linter

if TYPE_CHECKING:
	from packaging.specifiers import SpecifierSet
	from packaging.version import Version

	from ....base.source_operator import BaseSourceOperator
	from . import Parsers

@dataclass(frozen = True)
class DependencyError:
	"""Dependency error."""

	parser_name: str

	required_name: str
	required_version: "SpecifierSet | None"

	is_installed: bool
	installed_version: "Version | None"

	@property
	def installed_literal(self) -> str:
		"""Installed literal."""

		if self.installed_version:
			return f"{self.required_name}=={self.installed_version}"

		return self.required_name

	@property
	def required_literal(self) -> str:
		"""Required literal."""

		if self.required_version:
			return f"{self.required_name}{self.required_version}"

		return self.required_name

class ParserOperator:
	"""Parser operator."""

	def __init__(self, parsers: "Parsers", name: str):
		"""
		Parser operator.

		Args:
			parsers (Parsers): Parsers manager.
			name (str): Parser name.
		"""

		self.__parsers_manager: Parsers = parsers
		self.__name: str = name

		self.__extensions_operator: ExtensionsOperator = ExtensionsOperator(self, self.__parsers_manager.manager)
		self.__linter: Linter = Linter()

	def check_dependencies(self) -> DependencyError | None:
		"""
		Check is parser dependencies satisfied.

		Returns:
			DependencyError | None: Dependency error or `None` if all satisfied.
		"""

		manifest: ParserManifest = self.load_manifest()
		platform_version: Version = self.__parsers_manager.manager.system_objects.platform_version

		if manifest.platform and platform_version not in manifest.platform:
			return DependencyError(
				parser_name = manifest.parser_name,
				required_name = "melon",
				required_version = manifest.platform,
				is_installed = True,
				installed_version = platform_version,
			)

		if not manifest.parent:
			return

		if not self.__parsers_manager.is_installed(manifest.parent, raise_error = False):
			return DependencyError(
				parser_name = manifest.parser_name,
				required_name = manifest.parent,
				required_version = manifest.parent_version,
				is_installed = False,
				installed_version = None,
			)

		if not manifest.parent_version:
			return

		parent_operator: ParserOperator = self.__parsers_manager.get_operator(manifest.parent)
		parent_manifest: ParserManifest = parent_operator.load_manifest()

		if not parent_manifest.version:
			return DependencyError(
				parser_name = manifest.parser_name,
				required_name = manifest.parent,
				required_version = manifest.parent_version,
				is_installed = True,
				installed_version = None,
			)

		if parent_manifest.version not in manifest.parent_version:
			return DependencyError(
				parser_name = manifest.parser_name,
				required_name = manifest.parent,
				required_version = manifest.parent_version,
				is_installed = True,
				installed_version = parent_manifest.version,
			)

	@run_before_method("_require_installation")
	def export_settings(self, strategy: ExportStrategy = ExportStrategy.Skip) -> ExportResult:
		"""
		Экспортирует настройки парсера.

		:param strategy: Стратегия экспорта настроек при конфликте файлов.
		:type strategy: ExportStrategy
		:return: Результат экспорта настроек.
		:rtype: ExportResult
		"""

		BaseConfig: dict = ParserSettings.get_base_settings(self.__parsers_manager.manager.system_objects, self.__name)
		PresetFile = self.path / "settings.json"
		StorageFile = self.__parsers_manager.manager.system_objects.options.CONFIGS_DIR / f"{self.__name}.json"

		if PresetFile.exists():
			Buffer: dict = json.read(PresetFile)
			Config = dictionary.deep_merge(BaseConfig, Buffer, uniqueness = self.__parsers_manager.manager.system_objects.options.JSON_ATOMIC_WRITE)
		else:
			return ExportResult.Missing

		if StorageFile.exists():

			match strategy:
				case ExportStrategy.Skip:
					return ExportResult.AlreadyExists

				case ExportStrategy.Overwrite:
					json.write(StorageFile, Config, atomic = self.__parsers_manager.manager.system_objects.options.JSON_ATOMIC_WRITE)
					return ExportResult.Overwtitten

				case ExportStrategy.Merge:
					CurrentConfig: dict = json.read(StorageFile)
					Config = dictionary.deep_merge(Config, CurrentConfig, uniqueness = self.__parsers_manager.manager.system_objects.options.JSON_ATOMIC_WRITE)
					json.write(StorageFile, Config, atomic = self.__parsers_manager.manager.system_objects.options.JSON_ATOMIC_WRITE)
					return ExportResult.Merged

		json.write(StorageFile, Config, atomic = self.__parsers_manager.manager.system_objects.options.JSON_ATOMIC_WRITE)

		return ExportResult.Installed

	def install(self):
		"""
		Install parser.

		Raises:
			exceptions.parsers.ParserAlreadyExistsError: Parser already installed.
		"""

		if self.is_installed:
			raise exceptions.parsers.ParserAlreadyExistsError(self.__name, is_installed = True)

		self.path.mkdir(exist_ok = True)

		self.__parsers_manager.manager.packager.clone(
			directory = self.path,
			remote = self.__parsers_manager.manager.repositories.get(self.__name, exception = True),
		)

		self.install_requirements()

	def install_requirements(self):
		"""Устанавливает зависимости, если существует файл _requirements.txt_."""

		RequirementsFile = self.path / "requirements.txt"
		if RequirementsFile.exists():
			self.__parsers_manager.manager.packager.install_requirements(RequirementsFile)

	@run_before_method("_require_installation")
	def launch(self) -> "BaseSourceOperator":
		"""
		Инициализирует оператор источника.

		:return: Оператор источника.
		:rtype: BaseSourceOperator
		:raises FileNotFoundError: Точка вохода в парсер не найдена.
		"""

		ParserMain = self.path / "__init__.py"

		if not ParserMain.exists():
			raise FileNotFoundError(ParserMain)

		Module = importlib.import_module(f"parsers.{self.__name}")
		ParserManifest = self.load_manifest()

		return Module.SourceOperator(self.__parsers_manager.manager.system_objects, ParserManifest)

	@run_before_method("_require_installation")
	def lint(self) -> tuple[CheckResult, ...]:
		"""
		Run parser linting.

		:return: Checks result.
		:rtype: tuple[CheckResult, ...]
		"""

		return self.__linter.check(self)

	@run_before_method("_require_installation")
	def load_manifest(self) -> ParserManifest:
		"""
		Загружает манифест парсера.

		:return: Манифест парсера.
		:rtype: ParserManifest
		:raises FileNotFoundError: Файл манифеста не найден.
		"""

		ManifestFile = self.path / "manifest.json"

		if not ManifestFile.exists():
			raise FileNotFoundError(ManifestFile)

		return ParserManifest(self.__parsers_manager.manager.system_objects, self.__name)

	@run_before_method("_require_installation")
	def uninstall(self, clear: bool = False):
		"""
		Удаляет парсер.

		:param clear: Указывает, нужно ли удалить временные данные и настройки парсера.
		:type clear: bool
		"""

		ElementToRemove: list[Path] = [self.path]

		if clear:
			ElementToRemove += [
				self.__parsers_manager.manager.system_objects.options.CONFIGS_DIR / f"{self.__name}.json",
				self.__parsers_manager.manager.system_objects.options.TEMP_DIR / self.__name,
			]

		for Element in ElementToRemove:
			if Element.exists():
				if Element.is_dir(): shutil.rmtree(Element)
				else: Element.unlink()

	@run_before_method("_require_installation")
	def update(self, requirements: bool = True, force_mode: bool = False) -> bool:
		"""
		Обновляет парсер.

		:param requirements: Указывает, нужно ли установить зависимости после обновления.
		:type requirements: bool
		:param force_mode: Указывает, перезаписывать ли изменения в репозитории.
		:type force_mode: bool
		:return: Возвращает `True`, если состояние каталога парсера изменилось.
		:rtype: bool
		"""

		if not force_mode and self.__parsers_manager.manager.packager.has_changes(self.path):
			raise exceptions.parsers.RepositoryError("Local changes detected.")

		IsStateChanged: bool = self.__parsers_manager.manager.packager.pull(
			repository = self.path,
			remote = self.__parsers_manager.manager.repositories.get(self.__name, exception = True),
			force_mode = force_mode,
		)

		if IsStateChanged and requirements: self.install_requirements()

		return IsStateChanged

	def _require_installation(self):
		"""
		Проверяет, установлен ли парсер. Служит для использования в декораторе `run_before_method()`.

		:raises ParserNotFoundError: Парсер не установлен.
		"""

		self.__parsers_manager.is_installed(self.__name)

	@property
	def extensions(self) -> ExtensionsOperator:
		"""Extensions operator."""

		return self.__extensions_operator

	@property
	def is_installed(self) -> bool:
		"""Состояние: установлен ли парсер."""

		return self.__parsers_manager.is_installed(self.__name, raise_error = False)

	@property
	def name(self) -> str:
		"""Имя парсера."""

		return self.__name

	@property
	def path(self) -> Path:
		"""Путь к директории парсера."""

		return self.__parsers_manager.root / self.__name

	@property
	def repository(self) -> str | None:
		"""URL удалённого репозитория."""

		return self.__parsers_manager.manager.repositories.get(self.__name)

	@property
	def requirements_path(self) -> Path:
		"""Путь к файлу зависимостей если."""

		return self.path / "requirements.txt"

	@property
	def temp_directory(self) -> Path:
		"""Parser temp directory path."""

		return self.__parsers_manager.manager.system_objects.temper.get_parser_temp_directory(self.__name)
