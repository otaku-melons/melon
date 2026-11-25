from melon.core.base.formats.ranobe.enums import ChapterType
from melon.sdk.chapter_header_parser import ChapterHeaderParser

parser: ChapterHeaderParser = ChapterHeaderParser()
parser.load_keywords_presets("rus")

def test_parse():

	result = parser.parse("Том 1.5.8. Глава 1.2. Название (часть 1)")

	assert result.volume == "1.5.8"
	assert result.number == "1.2"
	assert result.name == "Название (часть 1)"
	assert result.chapter_type is ChapterType.chapter

	for variant in ("глава 1.2 Название", "глава 1.2: Название", "глава 01.2 - Название"):
		result = parser.parse(variant)
		assert result.number == "1.2"

def test_parse_type():

	result = parser.parse("Глава 1. Пролог истории")

	assert result.number == "1"
	assert result.name == "Пролог истории"
	assert result.chapter_type is ChapterType.chapter

	result = parser.parse("глоссарий")

	assert result.name is None
	assert result.chapter_type is ChapterType.glossary
