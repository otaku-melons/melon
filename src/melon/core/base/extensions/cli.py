from typing import TYPE_CHECKING

from dublib.cli.terminalyzer import ModelsGroup, Terminalyzer
from dublib.cli.terminalyzer.helper import Helper

if TYPE_CHECKING:
	from ....core.system_objects.printer import Portals, Printer
	from ..source_operator import BaseSourceOperator
	from . import BaseExtension
	from .options import BaseExtensionOptions

class BaseExtensionCLI[E: "BaseExtension[BaseSourceOperator, BaseExtensionOptions]"]:
	"""Base extension CLI operator."""

	#==========================================================================================#
	# >>>>> PROPERTIES <<<<< #
	#==========================================================================================#

	@property
	def extension(self) -> E:
		"""Extension."""

		return self._extension

	@property
	def is_provided(self) -> bool:
		"""Состояние: предоставляется ли CLI для расширения."""

		return bool(self._group.models)

	@property
	def portals(self) -> "Portals":
		"""Порталы вывода парсера."""

		return self._extension.source_operator.portals

	@property
	def printer(self) -> "Printer":
		"""Оператор вывода."""

		return self._extension.source_operator.portals.printer

	#==========================================================================================#
	# >>>>> OVERRIDABLE METHODS <<<<< #
	#==========================================================================================#

	def _command_not_found(self):
		"""Called if no command model matches for parameters."""

		pass

	def _build_models_group(self, group: ModelsGroup):
		"""
		Fill group by commands models.

		:param group: Commands models group.
		:type group: ModelsGroup
		"""

		pass

	#==========================================================================================#
	# >>>>> PUBLIC METHODS <<<<< #
	#==========================================================================================#

	def __init__(self, extension: E):
		"""
		Base extension CLI operator.

		:param extension: Extension..
		:type extension: BaseExtension
		"""

		self._extension: E = extension

		self._group: ModelsGroup = ModelsGroup()
		self._terminalyzer: Terminalyzer = Terminalyzer()
		self._helper: Helper = Helper()

		self._build_models_group(self._group)
		self._terminalyzer.set_models_groups(self._group)

	def help(self, command_name: str):
		"""
		Print command info.

		:param command_name: Command name.
		:type command_name: str
		"""

		model = self._terminalyzer.find_model(command_name)

		if model is None:
			self._command_not_found()
			return

		self.printer.emit(self._helper.generate_model_info(model))

	def list(self):
		"""Print list of available commands."""

		self.printer.emit(self._helper.generate_group_list(self._group))

	def run(self, parameters: str):
		"""
		Execute command.

		:param parameters: Command parameters. Starts from command identificator.
		:type parameters: str
		"""

		entity = self._terminalyzer.parse_parameters(parameters)
		
		if entity is None:
			self._command_not_found()
			return
