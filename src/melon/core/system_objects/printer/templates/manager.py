from ...manager.enums import ExportResult
from ._base import _BaseTemplatesSection

class ManagerTemplates(_BaseTemplatesSection):
	"""Extended output templates: manager."""

	def exported(self, result: ExportResult):
		"""
		Emit message: config exported.

		Args:
			result (ExportResult): Config export result.
		"""

		match result:
			case ExportResult.Missing: self.printer.emit("Preset missing. Skipped.")
			case ExportResult.Exported: self.printer.emit("Config exported.")
			case ExportResult.AlreadyExists: self.printer.emit("Config already exists. Skipped.")
			case ExportResult.Overwtitten: self.printer.emit("Config overwritten.")
			case ExportResult.Merged: self.printer.emit("Config merged with preset.")
