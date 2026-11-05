from bs4 import BeautifulSoup, NavigableString, Tag

from melon.core.html.elements import Paragraph
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

	html: str = "<p><b class=\"someclass1\"><i class=\"someclass2\">text</i></b><a href=\"www.example.com\" target=\"_blank\">anchor</a></p>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("p")
	assert tag is not None

	assert parser.clear_attributes(tag) == ("class", "class", "target")
	assert str(tag) == "<p><b><i>text</i></b><a href=\"www.example.com\">anchor</a></p>"

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

def test_parse_blockquote():

	html: str = "<blockquote style=\"text-align: center\">para1<b>bold</b><p>para2</p><p>para3<br/>para4</p><img src=\"https://example.com/image.png\"></blockquote>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("blockquote")
	assert tag is not None

	blockquote = parser.parse_blockquote(tag)
	assert blockquote is not None
	assert len(blockquote.elements) == 5

	assert blockquote.elements[0].to_html() == "<p>para1<b>bold</b></p>"
	assert blockquote.elements[1].to_html() == "<p>para2</p>"
	assert blockquote.elements[2].to_html() == "<p>para3</p>"
	assert blockquote.elements[3].to_html() == "<p>para4</p>"
	assert blockquote.elements[4].to_html() == "<img src=\"https://example.com/image.png\">"

def test_parse_elements():

	html: str = """
	<div>
		<h1 align=\"center\">Header</h1>
		<blockquote style=\"text-align: right\"><p>sometext</p>in blockquote</blockquote>
		<p>sometext with footnote<a data-footnote>this is note<img src=\"https://example.com/image.png\"></a></p>
	</div>
	"""
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("div")
	assert tag is not None

	elements = parser.parse_elements(tag, allow_footnotes = True)

	assert len(elements) == 3
	assert elements[0].to_html() == "<h3 style=\"text-align: center\">Header</h3>"
	assert elements[1].to_html() == "<blockquote style=\"text-align: right\"><p>sometext</p><p>in blockquote</p></blockquote>"
	assert isinstance(elements[2], Paragraph)
	assert len(elements[2].footnotes) == 1
	assert elements[2].footnotes[0].elements[0].to_html() == "<p>this is note</p>"
	assert elements[2].footnotes[0].elements[1].to_html() == "<img src=\"https://example.com/image.png\">"

def test_parse_footnotes():

	html: str = "<p>sometext<a data-footnote><p>note <b>bold</b></p><img src=\"https://example.com/image.png\"></a></p>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("p")
	assert tag is not None

	footnotes = parser.parse_footnotes(tag)

	assert len(footnotes) == 1
	assert len(footnotes[0].images) == 1
	assert len(footnotes[0].elements) == 2
	assert footnotes[0].elements[0].to_html() == "<p>note <b>bold</b></p>"

def test_parse_header():

	html: str = "<h3 style=\"text-align: center\"><b>header</b></h3>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("h3")
	assert tag is not None

	header = parser.parse_header(tag)

	assert header is not None
	assert header.to_html() == html

	html: str = "<h1 class=\"someclass\">header</h3>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("h1")
	assert tag is not None

	header = parser.parse_header(tag, autolevel = True)

	assert header is not None
	assert header.to_html() == "<h3>header</h3>"

	html: str = "<h6></h6>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("h6")
	assert tag is not None
	assert parser.parse_header(tag) is None

def test_parse_image():

	html: str = "<img width=\"1280\" height=\"720\" src=\"https://example.com/image.png\">"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("img")
	assert tag is not None

	image = parser.parse_image(tag)

	assert image is not None
	assert image.link == "https://example.com/image.png"
	assert image.resolution is not None
	assert image.resolution.width == 1280
	assert image.resolution.height == 720

	paragraph = parser.make_tag("p", "some text")

	is_error_raised: bool = False

	try:
		parser.parse_image(paragraph)
	except ValueError:
		is_error_raised = True

	assert is_error_raised is True

	html: str = "<img>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("img")
	assert tag is not None

	image = parser.parse_image(tag)

	assert image is None

def test_parse_paragraphs():

	html: str = "<p style=\"text-align: right\">para1\n<i class=\"someclass\">p</i>ara2<br/>para3</p>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("p")
	assert tag is not None

	paragraphs = parser.parse_paragraphs(tag, allow_footnotes = False)

	assert len(paragraphs) == 3

	results_strings: tuple[str, ...] = (
		"<p style=\"text-align: right\">para1</p>",
		"<p style=\"text-align: right\"><i>p</i>ara2</p>",
		"<p style=\"text-align: right\">para3</p>",
	)

	for index in range(3):
		assert paragraphs[index].to_html() == results_strings[index]

	html: str = "<p styles=\"decoration: none\" >sometext<a href=\"www.example.com\" data-footnote>note</a></p>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("p")
	assert tag is not None

	paragraphs = parser.parse_paragraphs(tag, allow_footnotes = True)
	assert len(paragraphs[0].footnotes) == 1

	paragraph_html: str = paragraphs[0].to_html()
	assert ">*</a></p>" in paragraph_html # Check footnote content replacing by *.
	assert paragraph_html.startswith("<p>sometext<a") # Check is unresolved styles removed.

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

	html: str = "<p><sup>styled</sup> text <a href=\"www.example.com\">wrapped</a> or <span>no</span></p>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("p")
	assert tag is not None

	parser.unwrap_non_styling_childrens(tag)
	assert str(tag) == "<p><sup>styled</sup> text <a href=\"www.example.com\">wrapped</a> or no</p>"
