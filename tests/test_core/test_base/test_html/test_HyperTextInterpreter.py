from bs4 import BeautifulSoup

from melon.core.html.enums import Align
from melon.core.html.interpreter import HyperTextInterpreter

interpreter = HyperTextInterpreter()

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
