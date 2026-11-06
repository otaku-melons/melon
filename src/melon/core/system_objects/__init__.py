import atexit
from importlib.metadata import version

from packaging.version import Version

from ...core.system_objects.manager import Manager
from ...core.system_objects.options import Options
from ...core.system_objects.printer import Printer
from ...core.system_objects.temper import Temper

class SystemObjects:
	"""System objects collection."""

	def __init__(self):
		"""System objects collection."""

		self.__options = Options()
		self.__manager = Manager(self)
		self.__printer = Printer(self)
		self.__temper = Temper(self)

		self.__version: Version = Version(version("melon"))

		atexit.register(self.__printer.progress_indicator.end)

	@property
	def platform_version(self) -> Version:
		"""Melon version."""

		return self.__version

	@property
	def options(self) -> Options:
		"""Melon environment options."""

		return self.__options

	@property
	def manager(self) -> Manager:
		"""System manager."""

		return self.__manager

	@property
	def printer(self) -> Printer:
		"""Output operator."""

		return self.__printer

	@property
	def temper(self) -> Temper:
		"""Temporary data operator."""

		return self.__temper
