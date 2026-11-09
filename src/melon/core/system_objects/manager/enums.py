from enum import Enum

class ExportResult(Enum):
	"""Settings export result."""

	Missing = 0
	Exported = 1
	AlreadyExists = 2
	Overwtitten = 3
	Merged = 4

class ExportStrategy(Enum):
	"""Settings export strategy."""

	Skip = "-s"
	Overwrite = "-o"
	Merge = "-m"
