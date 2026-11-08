from typing import TYPE_CHECKING

from ._base import BaseSettingsSection

if TYPE_CHECKING:
	from ..models import CommonModel  # noqa: F401

class Common(BaseSettingsSection["CommonModel"]):
	"""Settings section: common."""

	@property
	def pretty(self) -> bool:
		"""Condition: is content prettier enabled."""

		return self._data.pretty

	@property
	def sizing_images(self) -> bool:
		"""Codnition: is images resolutions required."""

		return self._data.sizing_images

	@property
	def use_id_as_filename(self) -> bool:
		"""Condition: is ID used as title name."""

		return self._data.use_id_as_filename
