import importlib
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from dublib.functions.data import dictionary
from dublib.functions.decorators import run_before_method
from dublib.functions.filesystem import json

from .....core import exceptions
from ....base.parsers.components.manifest import ParserManifest
from ....base.parsers.components.settings import ParserSettings
from .enums import ExportResults, ExportStrategies
from .extensions import ExtensionsOperator
from .linter import CheckResult, Linter

if TYPE_CHECKING:
	from ....base.source_operator import BaseSourceOperator
	from . import Parsers

class ParserOperator:
	"""Оператор парсера."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def extensions(self) -> ExtensionsOperator:
		"""Extensions operator."""

		return self.__extensions_operator

	@property
	def is_installed(self) -> bool:
		"""Состояние: установлен ли парсер."""

		return self.__Parsers.is_installed(self.__Name, exception = False)

	@property
	def name(self) -> str:
		"""Имя парсера."""

		return self.__Name

	@property
	def path(self) -> Path:
		"""Путь к директории парсера."""

		return self.__Parsers.root / self.__Name

	@property
	def repository(self) -> str | None:
		"""URL удалённого репозитория."""

		return self.__Parsers.manager.repositories.get(self.__Name)

	@property
	def requirements_path(self) -> Path:
		"""Путь к файлу зависимостей если."""

		return self.path / "requirements.txt"

	@property
	def temp_directory(self) -> Path:
		"""Parser temp directory path."""

		return self.__Parsers.manager.system_objects.temper.get_parser_temp_directory(self.__Name)

	#==========================================================================================#
	# >>>>> НАСЛЕДУЕМЫЕ ВАЛИДАТОРЫ <<<<< #
	#==========================================================================================#

	def _RequireInstallation(self):
		"""
		Проверяет, установлен ли парсер. Служит для использования в декораторе `run_before_method()`.

		:raises ParserNotFound: Парсер не установлен.
		"""

		self.__Parsers.is_installed(self.__Name)

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, parsers: "Parsers", name: str):
		"""
		Менеджер парсеров.

		:param parsers: Менеджер парсеров.
		:type parsers: Parsers
		:param name: Имя парсера.
		:type name: str
		"""

		self.__Parsers = parsers
		self.__Name = name

		self.__extensions_operator: ExtensionsOperator = ExtensionsOperator(self, self.__Parsers.manager)
		self.__linter: Linter = Linter()
		
	@run_before_method("_RequireInstallation")
	def export_settings(self, strategy: ExportStrategies = ExportStrategies.Skip) -> ExportResults:
		"""
		Экспортирует настройки парсера.

		:param strategy: Стратегия экспорта настроек при конфликте файлов.
		:type strategy: ExportStrategies
		:return: Результат экспорта настроек.
		:rtype: ExportResults
		"""

		BaseConfig: dict = ParserSettings.get_base_settings(self.__Parsers.manager.system_objects, self.__Name)
		PresetFile = self.path / "settings.json"
		StorageFile = self.__Parsers.manager.system_objects.options.CONFIGS_DIR.value / f"{self.__Name}.json"

		if PresetFile.exists():
			Buffer: dict = json.read(PresetFile)
			Config = dictionary.deep_merge(BaseConfig, Buffer, uniqueness = True)
		else:
			return ExportResults.Missing

		if StorageFile.exists():
			
			match strategy:
				case ExportStrategies.Skip:
					return ExportResults.AlreadyExists

				case ExportStrategies.Overwrite:
					json.write(StorageFile, Config)
					return ExportResults.Overwtitten

				case ExportStrategies.Merge:
					CurrentConfig: dict = json.read(StorageFile)
					Config = dictionary.deep_merge(Config, CurrentConfig, uniqueness = True)
					json.write(StorageFile, Config)
					return ExportResults.Merged

		json.write(StorageFile, Config)

		return ExportResults.Installed

	def install(self):
		"""
		Устанавливает парсер.

		:raises ParserAlreadyExists: Парсер уже установлен.
		:raises RepositoryError: Репозиторий не найден.
		"""

		if self.is_installed:
			raise exceptions.parsers.ParserAlreadyExists(self.__Name)

		self.path.mkdir(exist_ok = True)

		self.__Parsers.manager.packager.clone(
			directory = self.path,
			remote = self.__Parsers.manager.repositories.get(self.__Name, exception = True)
		)

		self.install_requirements()

	def install_requirements(self):
		"""Устанавливает зависимости, если существует файл _requirements.txt_."""

		RequirementsFile = self.path / "requirements.txt"
		if RequirementsFile.exists():
			self.__Parsers.manager.packager.install_requirements(RequirementsFile)

	@run_before_method("_RequireInstallation")
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

		Module = importlib.import_module(f"parsers.{self.__Name}")
		ParserManifest = self.load_manifest()

		return Module.SourceOperator(self.__Parsers.manager.system_objects, ParserManifest)

	@run_before_method("_RequireInstallation")
	def lint(self) -> tuple[CheckResult, ...]:
		"""
		Run parser linting.

		:return: Checks result.
		:rtype: tuple[CheckResult, ...]
		"""
		
		return self.__linter.check(self)

	@run_before_method("_RequireInstallation")
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
		
		return ParserManifest(self.__Parsers.manager.system_objects, self.__Name)

	@run_before_method("_RequireInstallation")
	def uninstall(self, clear: bool = False):
		"""
		Удаляет парсер.

		:param clear: Указывает, нужно ли удалить временные данные и настройки парсера.
		:type clear: bool
		"""
		
		ElementToRemove: list[Path] = [self.path]

		if clear:
			ElementToRemove += [
				self.__Parsers.manager.system_objects.options.CONFIGS_DIR.value / f"{self.__Name}.json",
				self.__Parsers.manager.system_objects.options.TEMP_DIR.value / self.__Name
			]

		for Element in ElementToRemove:
			if Element.exists():
				if Element.is_dir(): shutil.rmtree(Element)
				else: Element.unlink()

	@run_before_method("_RequireInstallation")
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

		if not force_mode and self.__Parsers.manager.packager.has_changes(self.path):
			raise exceptions.parsers.RepositoryError("Local changes detected.")

		IsStateChanged: bool = self.__Parsers.manager.packager.pull(
			repository = self.path,
			remote = self.__Parsers.manager.repositories.get(self.__Name, exception = True),
			force_mode = force_mode
		)

		if IsStateChanged and requirements: self.install_requirements()

		return IsStateChanged
