from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pydantic import BaseModel

class BaseSettingsSection[T: "BaseModel"]:
	"""Base settings section."""

	def __init__(self, data: T):
		"""
		Base settings section.

		Args:
			data (T): Data model.
		"""

		self._data: T = data

		self._post_init()

	def _post_init(self):
		"""Execute after instance initialization."""

		pass
