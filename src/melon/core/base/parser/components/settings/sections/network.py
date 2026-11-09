from typing import TYPE_CHECKING

from dublib.web_requestor.proxy import Proxy

from ._base import BaseSettingsSection

if TYPE_CHECKING:
	from ..models import NetworkModel  # noqa: F401

class Network(BaseSettingsSection["NetworkModel"]):
	"""Settings section: network."""

	@property
	def delay(self) -> float:
		"""Delay between requests."""

		return self._data.delay

	@property
	def images_mirrors(self) -> dict[str, str]:
		"""Dictionary with images domains redirects."""

		return self._data.images_mirrors.copy()

	@property
	def proxies(self) -> tuple[Proxy, ...]:
		"""Proxies."""

		return self.__proxies

	@property
	def retries(self) -> int:
		"""Retries count if request failed."""

		return self._data.retries

	def _post_init(self):
		"""Execute after instance initialization."""

		self.__proxies: tuple[Proxy, ...] = tuple(Proxy().parse(string) for string in self._data.proxies)
