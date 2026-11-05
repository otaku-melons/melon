from typing import TYPE_CHECKING

from dublib.validators import ValidableType

from ...base import BaseCommandProcessor

if TYPE_CHECKING:
	from ...base.templates import BaseParameters

class CommandProcessorTemplate[PARAMS: "BaseParameters"](BaseCommandProcessor[PARAMS]):
	"""Command processor template."""

	def _add_mirror_key(self):
		"""Add mirror key to command model."""

		self._internal_storage.is_mirror_available = True
		self._model.base.add_key("--mirror", value_type = ValidableType.Domain, description = "Source mirror to requests.")
