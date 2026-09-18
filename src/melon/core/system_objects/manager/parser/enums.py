from enum import Enum

class ExportResults(Enum):
	"""Результаты экспорта настроек."""

	Missing = 0
	Installed = 1
	AlreadyExists = 2
	Overwtitten = 3
	Merged = 4

class ExportStrategies(Enum):
	"""Стратегии экспорта настроек."""

	Skip = "-s"
	Overwrite = "-o"
	Merge = "-m"
