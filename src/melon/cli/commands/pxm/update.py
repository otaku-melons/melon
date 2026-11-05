from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ...base import BaseCommandProcessor
from ...base.templates import T_ForceModeRequired, T_SingleParserRequired

if TYPE_CHECKING:
	from packaging.version import Version

	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ....core.base.parser.components.manifest import ParserManifest
	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(T_ForceModeRequired, T_SingleParserRequired):
	"""Required by command processor parameters."""

	pass

class CommandProcessor(BaseCommandProcessor[Parameters]):
	"""Command processor."""

	@override
	def _build_model(self, model: "CommandModel") -> "CommandModel":
		"""
		Build commands model.

		Args:
			model (CommandModel): Commands model.

		Returns:
			CommandModel: Commands model.
		"""

		self._add_parser_position()
		self._add_force_mode_flag()

		return model

	@override
	def _export_description(self) -> str:
		"""
		Export command description.

		Returns:
			str: Description.
		"""

		return "Update parser."

	@override
	def _parse_parameters(self, entity: "CommandEntity", prepared_data: "PreparedData") -> Parameters:
		"""
		Parse command parameters.

		Args:
			entity (CommandEntity): Command entity.
			prepared_data (PreparedData): Prepared from templates data.

		Returns:
			PARAMS: Command parameters.
		"""

		return Parameters(
			required_parser =  prepared_data.required_parsers[0],
			force_mode = prepared_data.force_mode,
		)

	@override
	def _process(self, parameters: Parameters) -> bool | None:
		"""
		Process command.

		Args:
			parameters (Parameters): Required by command parameters.

		Returns:
			bool | None: `False` if processing failed.
		"""

		repository_url: str = self.system_objects.manager.repositories.get(parameters.required_parser.name, exception = True)
		manifest: ParserManifest = parameters.required_parser.load_manifest()
		original_version: Version | None = manifest.version

		self.printer.emit(f"Repository: [i]{repository_url}[/i].")
		if original_version: self.printer.emit(f"Current version: [b]{original_version}[/b].")

		is_updated: bool = parameters.required_parser.update(force_mode = parameters.force_mode)

		if is_updated:
			manifest.update()
			self.printer.emit("Updated.")
			version: Version | None = manifest.version
			if original_version: self.printer.emit(f"Installed version: [b]{version}[/b].")

		else:
			self.printer.emit("No changes.")
