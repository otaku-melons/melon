from enum import Enum

class ParsingStep(Enum):
	"""Parsing step."""

	BeforeParsing = "before_parsing"
	AfterParsing = "after_parsing"
	BeforeAmending = "before_amending"
	AfterAmending = "after_amending"
	BeforeSaving = "before_saving"
	AfterSaving = "after_saving"
