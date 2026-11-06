import sys
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from dublib.cli.terminalyzer import CommandModel

from ...core import exceptions
from ...utils.timer import Timer
from .structs import PreparedData, ProcessorOptions, _InternalStorage

if TYPE_CHECKING:
	from dublib.cli.terminalyzer.commands.group import ModelsGroup
	from dublib.cli.terminalyzer.parser.entities import CommandEntity

	from ...core.base.source_operator import BaseSourceOperator
	from ...core.system_objects import SystemObjects
	from ...core.system_objects.manager.parser import ParserOperator
	from ...core.system_objects.manager.parser.operator import DependencyError
	from ...core.system_objects.printer import Printer
	from .templates import BaseParameters

class BaseCommandProcessor[PARAMS: "BaseParameters"](ABC):
	"""Base command processor."""

	def __init__(self, system_objects: "SystemObjects", group: "ModelsGroup"):
		"""
		Base command processor.

		Args:
			system_objects (SystemObjects): System objects collection.
			group (ModelsGroup): Commands models group.
		"""

		self._system_objects: SystemObjects = system_objects

		self._internal_storage: _InternalStorage = _InternalStorage()
		self._options: ProcessorOptions = self._export_options()
		self._timer: Timer | None = None

		self._model: CommandModel = group.create_model(
			name = self.__class__.__module__.split(".")[-1].split("_")[-1],
			description = self._export_description(),
		)
		self._model = self._build_model(self._model)

		self._mirror: str | None = None

		self._post_init()

	def process(self, entity: "CommandEntity"):
		"""
		Process command entity.

		Args:
			entity (CommandEntity): Command entity.
		"""

		self._start_timer()

		prepared_data = self._prepare_parameters(entity)
		parameters = self._parse_parameters(entity, prepared_data)

		if self._process_safely(parameters) is False:
			sys.exit(1)

		self._end_timer()

	@property
	def model(self) -> CommandModel:
		"""Command model."""

		return self._model

	@property
	def options(self) -> ProcessorOptions:
		"""Processor options."""

		return self._options

	@property
	def printer(self) -> "Printer":
		"""Output operator."""

		return self._system_objects.printer

	@property
	def system_objects(self) -> "SystemObjects":
		"""System objects collection."""

		return self._system_objects

	def _add_force_mode_flag(self):
		"""Add force mode flag to command model."""

		self.model.base.add_flag(
			name = "-f",
			aliases = ("--force",),
			description = "Enable force mode.")

		self._internal_storage.is_force_mode = True

	def _add_json_output_flag(self):
		"""Add JSON output flag to command model."""

		self._model.base.add_flag(
			name = "-j",
			aliases = ("--json",),
			description = "Prints output as JSON-string.",
		)

		self._internal_storage.is_json_output = True

	def _add_parser_position(self, key: str | None = None, description: str | None = None, multiple: bool = False, important: bool = True):
		"""
		Add parser position `PARSER` or `PARSERS` to command model.

		Args:
			key (str | None): Key name. If missing argument will be used.
			description (str | None): Position description.
			multiple (bool): Condition: is multiple parsers selection allowed.
			important (bool): Condition: is position important.
		"""

		if multiple:
			self._internal_storage.is_multiple_parsers_allowed = True

			position = self.model.create_position(
				name = "PARSERS",
				description = description or "One or more parsers names separated by comma. By default all.",
				important = important,
			)

		else:
			position = self.model.create_position(
				name = "PARSER",
				description = description or "Parser name.",
				important = important,
			)

		position.add_key(key) if key else position.set_argument()

	@abstractmethod
	def _build_model(self, model: "CommandModel") -> "CommandModel":
		"""
		Build commands model.

		Args:
			model (CommandModel): Commands model.

		Returns:
			CommandModel: Commands model.
		"""

		return model

	def _check_required_parsers(self, parsers_names: tuple[str, ...]):
		"""
		Check is required parsers available.

		Args:
			parsers_names (tuple[str, ...]): Required parsers names.

		Raises:
			exceptions.parsers.ParserNotFoundError: Parser not found.
		"""

		if not parsers_names:
			return

		installed_parsers: tuple[str, ...] = tuple(self.system_objects.manager.parsers.installed)
		parsers_in_repositories: tuple[str, ...] = self.system_objects.manager.repositories.available_parsers

		for parser in parsers_names:

			if parser in installed_parsers:

				if parser not in parsers_in_repositories:
					self.printer.warning(f"Repository not found for parser [b]{parser}[/b].")

				continue

			if parser in parsers_in_repositories:
				continue

			raise exceptions.parsers.ParserNotFoundError(parser)

	@abstractmethod
	def _export_description(self) -> str:
		"""
		Export command description.

		Returns:
			str: Description.
		"""

		return ""

	# OVERRIDABLE
	def _export_options(self) -> ProcessorOptions:
		"""
		Export processor options.

		Returns:
			ProcessorOptions: Processor options.
		"""

		return ProcessorOptions()

	def _get_parsers_query(self, entity: "CommandEntity") -> tuple[str, ...]:
		"""
		Get required parsers names. Parsed from `PARSER` or `PARSERS` position.

		Args:
			entity (CommandEntity): Command entity.

		Returns:
			tuple[str, ...]: Required parsers names.
		"""

		position_name: str = "PARSERS" if self._internal_storage.is_multiple_parsers_allowed else "PARSER"
		query_value: str | None = entity.get_position_value(position_name, expected_type = str)

		if not query_value:
			return ()

		return tuple(element.strip() for element in query_value.split(","))

	def _end_timer(self):
		"""Emit timer result if enabled."""

		if self._timer is not None and not self._internal_storage.is_json_output:
			self.printer.emit(f"Done in {self._timer.ends()}.")

	def _launch_source_operator(self, parser_operator: "ParserOperator") -> "BaseSourceOperator":
		"""
		Launch source operator.
		Automatically enable mirror if available and cache result.

		Args:
			parser_operator (ParserOperator): Parser operator.

		Returns:
			BaseSourceOperator: Source operator.
		"""

		parser_name: str = parser_operator.name

		if parser_name not in self._internal_storage.source_operators:
			source_operator = parser_operator.launch()
			if self._internal_storage.mirror: source_operator.set_mirror(self._internal_storage.mirror)
			self._internal_storage.source_operators[parser_name] = source_operator
			return source_operator

		return self._internal_storage.source_operators[parser_name]

	def _load_required_parsers_operators(self, data: "CommandEntity") -> tuple["ParserOperator", ...]:
		"""
		Load required parsers operators.

		Args:
			data (CommandEntity): Command entity.

		Returns:
			tuple[ParserOperator, ...]: Parsers operators.

		Raises:
			exceptions.cli.MultipleParsersDeniedForCommandError: Multiple parser denied for command.
		"""

		parsers_names: tuple[str, ...] = self._get_parsers_query(data)

		if not parsers_names:
			return ()

		if not parsers_names:
			if self.system_objects.options.DEBUG:
				self.printer.debug("Parsers not selected. All installed will be loaded.")

			parsers_names = tuple(self.system_objects.manager.parsers.installed)

		if not self._internal_storage.is_multiple_parsers_allowed and len(parsers_names) > 1:
			raise exceptions.cli.MultipleParsersDeniedForCommandError(data.model.name)

		self._check_required_parsers(parsers_names)

		parsers_operators: tuple[ParserOperator, ...] = tuple(
			self.system_objects.manager.parsers.get_operator(Name, require_installation = self.options.require_installed_parsers)
			for Name in parsers_names
		)

		if self.options.check_parsers_dependencies:
			for parser_operator in parsers_operators:
				dependency_error: DependencyError | None = parser_operator.check_dependencies()

				if dependency_error:
					self.printer.templates.manager.dependency_error(dependency_error, critical = True)

		return parsers_operators

	@abstractmethod
	def _parse_parameters(self, entity: "CommandEntity", prepared_data: PreparedData) -> PARAMS:
		"""
		Parse command parameters.

		Args:
			entity (CommandEntity): Command entity.
			prepared_data (PreparedData): Prepared from templates data.

		Returns:
			PARAMS: Command parameters.
		"""

		pass

	# OVERRIDABLE
	def _post_init(self):
		"""Execute after instance initialization."""

		pass

	def _prepare_parameters(self, entity: "CommandEntity") -> PreparedData:
		"""
		Prepare common data from templates for command.

		Args:
			entity (CommandEntity): Command entity.

		Returns:
			PreparedData: Prepared data.
		"""

		if self._internal_storage.is_mirror_available:
			self._internal_storage.mirror = entity.get_key_value("--mirror", expected_type = str, not_found_error = False)

		return PreparedData(
			required_parsers = self._load_required_parsers_operators(entity),
			force_mode = entity.check_flag("-f", missing_error = False),
			is_json_output = entity.check_flag("-j", missing_error = False),
		)

	@abstractmethod
	def _process(self, parameters: PARAMS) -> bool | None:
		"""
		Process command.

		Args:
			parameters (Parameters): Required by command parameters.

		Returns:
			bool | None: `False` if processing failed.
		"""

		return True

	def _process_safely(self, parameters: PARAMS) -> bool | None:
		"""
		Wrap `_process()` method and catch common exteptions.

		Args:
			parameters (Parameters): Required by command parameters..

		Returns:
			bool | None: `False` if processing failed.
		"""

		try:
			return self._process(parameters)

		except exceptions.extensions.ExtensionNotFoundError as exception:
			self.printer.error(f"Extension [bold]{exception}[/bold] not found.")

		except exceptions.parsers.ParserAlreadyExistsError as exception:
			if exception.is_installed:
				self.printer.error(f"Parser [b]{exception.parser_name}[/b] already exists.")
			else:
				self.printer.error(f"Parser [b]{exception.parser_name}[/b] found in repositories.")

		except exceptions.parsers.ParserNotFoundError as exception:
			self.printer.error(f"Parser [b]{exception}[/b] not found.")

		except exceptions.parsers.RepositoryError as exception:
			self.printer.error(f"Repository [b]{exception}[/b] not found.")

		return False

	def _start_timer(self):
		"""Start timer if enabled."""

		if self.options.use_timer:
			self._timer = Timer(start = True)
