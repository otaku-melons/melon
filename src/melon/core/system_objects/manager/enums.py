from enum import Enum

class ExportResult(Enum):
	"""Результаты экспорта настроек."""

	Missing = 0
	Installed = 1
	AlreadyExists = 2
	Overwtitten = 3
	Merged = 4

class ExportStrategy(Enum):
	"""Стратегии экспорта настроек."""

	Skip = "-s"
	Overwrite = "-o"
	Merge = "-m"

class ParsingStep(Enum):
	"""Parsing step."""

	BeforeParsing = "before_parsing"
	AfterParsing = "after_parsing"
	BeforeAmending = "before_amending"
	AfterAmending = "after_amending"
	BeforeSaving = "before_saving"
	AfterSaving = "after_saving"
