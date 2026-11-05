from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, override

from dublib.validators import ValidableType

from ....utils.cutter import Cutter
from ...base.templates import BaseParameters
from ..melon._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(BaseParameters):
	"""Required by command processor parameters."""

	image: Path
	templates: Path
	output: Path | None
	is_dry: bool

class CommandProcessor(CommandProcessorTemplate[Parameters]):
	"""Command processor."""

	#==========================================================================================#
	# >>>>> PRIVATE METHODS <<<<< #
	#==========================================================================================#

	def __get_templates(self, parameters: Parameters, cutter: Cutter) -> tuple[Path, ...]:
		"""
		Получает шаблоны.

		:param parameters: Required by command processor parameters.
		:type parameters: Parameters
		:param cutter: Инструмент для вырезания рекламы из слайдов манги.
		:type cutter: Cutter
		:return: Последовательность путей к шаблонам.
		:rtype: tuple[Path, ...]
		"""

		templates: tuple[Path, ...] = (parameters.templates, )

		if parameters.templates.is_dir():
			templates = cutter.get_templates_from_directory(parameters.templates)

		self.printer.emit(f"Templates loaded: {len(templates)}.")

		return templates

	#==========================================================================================#
	# >>>>> OVERRIDABLE METHODS <<<<< #
	#==========================================================================================#

	@override
	def _build_model(self, model: "CommandModel") -> "CommandModel":
		"""
		Build commands model.

		Args:
			model (CommandModel): Commands model.

		Returns:
			CommandModel: Commands model.
		"""

		position = model.create_position("IMAGE", "Path to image.", important = True)
		position.set_argument(ValidableType.ExistingFilePath)

		position = model.create_position("TEMPLATES", "Templates source.", important = True)
		position.add_key("--dir", value_type = ValidableType.ExistingDirPath, description = "Path to templates images directory.")
		position.set_argument(value_type = ValidableType.ExistingFilePath, description = "Path to template image.")

		position = model.create_position("OUTPUT", "Output image path.")
		position.set_argument(ValidableType.Path)

		model.base.add_flag("-d", description = "Dry run for only matches checking.")

		return model

	@override
	def _export_description(self) -> str:
		"""
		Export command description.

		Returns:
			str: Description.
		"""

		return "Cut full-width templates from image."

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
			image = entity.get_position_value("IMAGE", expected_type = Path, important = True),
			templates = entity.get_position_value("TEMPLATES", expected_type = Path, important = True),
			output = entity.get_position_value("OUTPUT", expected_type = Path, important = False),
			is_dry = entity.check_flag("-d"),
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

		cutter = Cutter(self.system_objects)
		templates: tuple[Path, ...] = self.__get_templates(parameters, cutter)

		if not templates:
			return True

		if parameters.is_dry:
			matches: int = cutter.calculate_templates_matches(parameters.image, templates)
			self.printer.emit(f"Matches found: {matches}.")
			return True

		cut_templates_count: int = cutter.clean_image(parameters.image, templates, parameters.output)

		if cut_templates_count:
			self.printer.emit(f"Cut {cut_templates_count} templates from image.")

			if parameters.output: self.printer.emit(f"Image path: [i]{parameters.output}[/]")
			else: self.printer.emit("Original image overwritten.")

		else:
			self.printer.emit("No templates matches for image.")
