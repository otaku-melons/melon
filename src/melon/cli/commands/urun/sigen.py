from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, override

from dublib.functions.filesystem import json
from dublib.validators import ValidableType

from .... import utils
from ...base.templates import T_OptionalSingleParser
from ..melon._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ....core.system_objects.manager.parser_operator import ParserOperator
	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(T_OptionalSingleParser):
	"""Required by command processor parameters."""

	image: Path
	signature_version: utils.unstubber.SignatureVersion

class CommandProcessor(CommandProcessorTemplate[Parameters]):
	"""Command processor."""

	#==========================================================================================#
	# >>>>> PRIVATE METHODS <<<<< #
	#==========================================================================================#

	def __export_signature(self, signature: str, required_parser: "ParserOperator") -> bool:
		"""
		Экспортирует сигнатуру в файл конфигурации парсера.

		:param signature: Сигнатура изображения.
		:type signature: str
		:param required_parser: Оператор парсера.
		:type required_parser: ParserOperator
		:return: Возвращает `False`, если команда требует прерывания выполнения.
		:rtype: bool
		"""

		Config: Path = self.system_objects.options.CONFIGS_DIR / f"{required_parser.name}.json"

		if not Config.exists():
			self.printer.emit("Configuration file not found.")
			return False

		ConfigData: dict[str, dict] = json.read(Config)

		if "filters" not in ConfigData: ConfigData["filters"] = {}
		if "images" not in ConfigData["filters"]: ConfigData["filters"]["images"] = {}

		Signatures: list[str] = ConfigData["filters"]["images"].get("signatures", [])

		if signature in Signatures:
			self.printer.warning("Signature already exists. Export skipped.")
			return True

		Signatures.append(signature)
		ConfigData["filters"]["images"]["signatures"] = Signatures
		json.write(Config, ConfigData, atomic = self.system_objects.options.JSON_ATOMIC_WRITE)
		self.printer.emit(f"Exported in [b]{required_parser.name}[/] config.")

		return True

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

		position = model.create_position("VERSION", "Signature version.", important = True)
		position.add_flag("-v1", description = "Based on image sizes and pixels SHA256 hash: exact match.")
		position.add_flag("-v2", description = "Based on perceptual hash: approximate match.")

		self._add_parser_position(key = "--export", description = "Export signature in parser config.", important = False)

		return model

	@override
	def _export_description(self) -> str:
		"""
		Export command description.

		Returns:
			str: Description.
		"""

		return "Generate image filtering signature."

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

		version_key: str = entity.get_position_value("VERSION", expected_type = str, important = True)
		version_key = version_key.lstrip("-")
		version = utils.unstubber.SignatureVersion[version_key]

		return Parameters(
			required_parser = prepared_data.required_parsers[0] if prepared_data.required_parsers else None,
			image = entity.get_position_value("IMAGE", expected_type = Path, important = True),
			signature_version = version,
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

		Unstubber = utils.Unstubber()
		Image = Unstubber.load_image(parameters.image)
		Signature: str = Unstubber.generate_signature(Image, parameters.signature_version)
		self.printer.emit(f"Signature: [i]{Signature}[/]")

		if parameters.required_parser:
			return self.__export_signature(Signature, parameters.required_parser)
