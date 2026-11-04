from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

from melon.core.base.structs.image import ImageData, ImageType
from melon.core.html.elements import Blockquote, Header, Paragraph
from melon.core.html.enums import Align
from melon.core.html.interpreter import HyperTextInterpreter

if TYPE_CHECKING:
	from melon.core.html.base_elements import BaseElement
	from melon.core.html.footnote import Footnote

interpreter = HyperTextInterpreter()

FOOTNOTE_ID: str = "952a7560-9bf1-4f15-8399-41c6895c54e5"
FOOTNOTES_DATA: dict[str, list[str]] = {
		FOOTNOTE_ID: [
			"<p>This is <i>styled</i> note with <a href=\"www.example.com\">link</a>.</p>",
			"<img src=\"https://example.com/image2.png\" data-file=\"illustrations/image2.png\">",
		],
	}

def test_interpret_footnotes():

	footnotes: tuple[Footnote, ...] = interpreter.interpret_footnotes(FOOTNOTES_DATA)

	assert len(footnotes) == 1
	assert footnotes[0].id == FOOTNOTE_ID
	assert len(footnotes[0].elements) == 2
	assert len(footnotes[0].images) == 1
	assert footnotes[0].images[0].link == "https://example.com/image2.png"
	assert footnotes[0].elements[0].to_html() == "<p>This is <i>styled</i> note with <a href=\"www.example.com\">link</a>.</p>"

def test_interpret_lines():

	lines: list[str] = [
		"<h3>Header</h3>",
		"<img src=\"https://example.com/image1.png\" data-file=\"illustrations/image1.png\" width=\"1280\" height=\"720\">",
		f"<p>This is <s>styled</s> paragraph with<a data-footnote=\"{FOOTNOTE_ID}\">*</a> footnote.</p>",
		"<blockquote style=\"text-align: right\"><p>This <u>is</u> blockquote.</p></blockquote>",
	]

	footnotes: tuple[Footnote, ...] = interpreter.interpret_footnotes(FOOTNOTES_DATA)
	elements: tuple[BaseElement | ImageData, ...] = interpreter.interpret_lines(lines, footnotes)

	assert len(elements) == 4

	assert isinstance(elements[0], Header)
	assert elements[0].level == 3

	assert isinstance(elements[1], ImageData)
	assert elements[1].resolution is not None
	assert elements[1].resolution.height == 720
	assert elements[1].image_type is ImageType.Illustration
	assert elements[1].link == "https://example.com/image1.png"
	assert elements[1].file is not None
	assert elements[1].file.as_posix() == "illustrations/image1.png"

	assert isinstance(elements[2], Paragraph)
	assert len(elements[2].footnotes) == 1
	assert elements[2].footnotes[0].id == FOOTNOTE_ID

	assert isinstance(elements[3], Blockquote)
	assert elements[3].align is Align.Right
	assert len(elements[3].elements) == 1
	assert elements[3].elements[0].to_html() == "<p>This <u>is</u> blockquote.</p>"

def test_parse_align():

	html: str = "<p align=\"center\" style=\"text-align: right\">text</p>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("p")
	assert tag is not None

	assert interpreter.parse_align(tag) is Align.Center

	html: str = "<p style=\"text-align: right\">text</p>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("p")
	assert tag is not None

	assert interpreter.parse_align(tag) is Align.Right

	html: str = "<p style=\"text-align: justify\">text</p>"
	soup = BeautifulSoup(html, "html.parser")
	tag = soup.find("p")
	assert tag is not None

	assert interpreter.parse_align(tag) is None
