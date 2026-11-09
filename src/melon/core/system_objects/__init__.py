import atexit

from ...core.system_objects.manager import ParsersManager
from ...core.system_objects.options import Options
from ...core.system_objects.printer import Printer
from ...core.system_objects.temper import Temper

class SystemObjects:
	"""System objects collection."""

	def __init__(self):
		"""System objects collection."""

		self.__options = Options()
		self.__manager = ParsersManager(self)
		self.__printer = Printer(self)
		self.__temper = Temper(self)

		atexit.register(self.__printer.progress_indicator.end)

	@property
	def options(self) -> Options:
		"""Melon environment options."""

		return self.__options

	@property
	def manager(self) -> ParsersManager:
		"""Parsers manager."""

		return self.__manager

	@property
	def printer(self) -> Printer:
		"""Output operator."""

		return self.__printer

	@property
	def temper(self) -> Temper:
		"""Temporary data operator."""

		return self.__temper
