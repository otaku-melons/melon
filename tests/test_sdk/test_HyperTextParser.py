from bs4 import BeautifulSoup, NavigableString, Tag

from melon.core.html.enums import Align
from melon.sdk.html_parser import HyperTextParser

parser = HyperTextParser()

def test_check_unresolved_childrens():

	html: str = "<p>text<span>unresolved</span><b>bold</b></p>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("p")
	assert tag is not None

	assert parser.check_unresolved_childrens(tag) == ("span",)

	span = soup.find("span")
	assert span is not None
	span.unwrap()

	assert parser.check_unresolved_childrens(tag) == ()

def test_clear_attributes():

	html: str = "<blockquote data-custom=\"1\" class=\"someclass\">text<b data-color=\"black\">bold</b></blockquote>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("blockquote")
	assert tag is not None

	assert parser.clear_attributes(tag) == ("data-color", "class")
	assert str(tag) == "<blockquote data-custom=\"1\">text<b>bold</b></blockquote>"

def test_clear_styles():

	html: str = "<p style=\"text-align: center\"><b style=\"text-style: bold\"></b></p>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("p")
	assert tag is not None

	assert parser.clear_styles(tag) == ("text-style",)
	assert str(tag) == "<p style=\"text-align: center\"><b></b></p>"

def test_has_child_tag():

	html: str = "<p>text<b>bold</b></p>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("p")
	assert tag is not None

	assert parser.has_child_tag(tag, "b") is True
	assert parser.has_child_tag(tag, "i") is False
	assert parser.has_child_tag(tag, "p") is False

def test_make_tag():

	tag = parser.make_tag("p", "test text")
	assert str(tag) == "<p>test text</p>"

	content = NavigableString("test text")
	tag = parser.make_tag("p", content)
	assert str(tag) == "<p>test text</p>"

	content = (NavigableString("test "), NavigableString("text"))
	tag = parser.make_tag("p", content)
	assert str(tag) == "<p>test text</p>"

	tag = parser.make_tag("div", tag)
	assert str(tag) == "<div><p>test text</p></div>"

	tag = parser.make_tag("p", "test text", {"style": "text-align: center"})
	assert str(tag) == "<p style=\"text-align: center\">test text</p>"

def test_normalize_text():

	text: str = " text\u00a0 with  spaces\t"
	assert parser.normalize_text(text) == "text with spaces"

def test_parse_align():

	html: str = "<p align=\"center\" style=\"text-align: right\">text</p>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("p")
	assert tag is not None

	assert parser.parse_align(tag) is Align.Center

	html: str = "<p style=\"text-align: right\">text</p>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("p")
	assert tag is not None

	assert parser.parse_align(tag) is Align.Right

	html: str = "<p style=\"text-align: justify\">text</p>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("p")
	assert tag is not None

	assert parser.parse_align(tag) is None

def test_split():

	html: str = "<div align=\"center\">text\ncan <i class=\"someclass\">be</i> split<br>in parts<br/>with parser</div>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("div")
	assert tag is not None

	parts: tuple[Tag, ...] = parser.split(tag)

	assert len(parts) == 4

	results_strings: tuple[str, ...] = (
		"<p style=\"text-align: center\">text</p>",
		"<p style=\"text-align: center\">can <i class=\"someclass\">be</i> split</p>",
		"<p style=\"text-align: center\">in parts</p>",
		"<p style=\"text-align: center\">with parser</p>",
	)

	for index in range(4):
		assert str(parts[index]) == results_strings[index]

def test_unwrap_non_styling_childrens():

	html: str = "<p><sup>styled</sup> text <a href=\"somelink\">wrapped</a> or <span>no</span></p>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("p")
	assert tag is not None

	parser.unwrap_non_styling_childrens(tag)
	assert str(tag) == "<p><sup>styled</sup> text wrapped or no</p>"

def test_parse_paragraphs():

	html: str = "<p style=\"text-align: right\">para1\n<i class=\"someclass\">p</i>ara2<br/>para3</p>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("p")
	assert tag is not None

	paragraphs = parser.parse_paragraphs(tag)

	assert len(paragraphs) == 3

	results_strings: tuple[str, ...] = (
		"<p style=\"text-align: right\">para1</p>",
		"<p style=\"text-align: right\"><i>p</i>ara2</p>",
		"<p style=\"text-align: right\">para3</p>",
	)

	for index in range(3):
		assert paragraphs[index].to_html() == results_strings[index]
