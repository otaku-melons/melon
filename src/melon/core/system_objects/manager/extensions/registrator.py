from typing import TYPE_CHECKING

from .enums import ParsingStep

if TYPE_CHECKING:
	from collections.abc import Callable, Sequence

class Registrator:
	"""Extension methods registrator."""

	def __init__(self, extension_package_name: str):
		"""
		Extension methods registrator.

		Args:
			extension_package_name (str): Extension package name.
		"""

		self.__extension_package_name: str = extension_package_name

		self.__registrations: dict[ParsingStep, list[Callable]] = {}

	def get_step_methods(self, step: ParsingStep) -> tuple["Callable", ...]:
		"""
		Get registered for parsing step methods.

		Args:
			step (ParsingStep): Parsing step.

		Returns:
			tuple[Callable, ...]: Step methods.
		"""

		methods: Sequence[Callable] | None = self.__registrations.get(step)

		return tuple(methods) if methods is not None else ()

	def register(self, step: ParsingStep, method: "Callable"):
		"""
		Register extension method execution after parsing step.

		Args:
			step (ParsingStep): Parsing step.
			method (Callable): Extension method.
		"""

		self.__registrations.setdefault(step, []).append(method)

	@property
	def extension_package_name(self) -> str:
		"""Extension package name."""

		return self.__extension_package_name


