from typing import TYPE_CHECKING

from dublib.functions.filesystem import json, text

from melon.core import exceptions
from melon.utils.classificator import AttributesClassificator
from melon.utils.classificator.enums import AttributeType, Case

if TYPE_CHECKING:
	from pathlib import Path

def test_classificator_delete(tmp_path: "Path"):

	script: tuple[str, ...] = (
		"@delete",
		"attribute",
	)

	entry_point: Path = tmp_path / "main.mcs"
	text.write(entry_point, script)

	classificator = AttributesClassificator(entry_point)
	assert classificator.load() is None
	assert len(classificator.operations) == 1
	result = classificator.classify("Attribute", ignore_case = True)
	assert result is not None
	assert result.is_deleted is True

def test_classificator_drop(tmp_path: "Path"):

	script: tuple[str, ...] = (
		"@case[low]",
		"@delete",
		"@type[genres]",
		"@drop",
		"attribute",
	)

	entry_point: Path = tmp_path / "main.mcs"
	text.write(entry_point, script)

	classificator = AttributesClassificator(entry_point)
	assert classificator.load() is None
	assert len(classificator.operations) == 1
	result = classificator.classify("attribute")
	assert result is not None
	assert result.case is None
	assert result.is_deleted is False
	assert result.type is None

def test_classificator_case(tmp_path: "Path"):

	script: tuple[str, ...] = (
		"@case[low]",
		"Attribute",
	)

	entry_point: Path = tmp_path / "main.mcs"
	text.write(entry_point, script)

	classificator = AttributesClassificator(entry_point)
	assert classificator.load() is None
	assert len(classificator.operations) == 1
	result = classificator.classify("attribute", ignore_case = True)
	assert result is not None
	assert result.case is Case.low
	assert result.result == "attribute"

def test_classificator_include(tmp_path: "Path"):

	script: tuple[str, ...] = (
		"@type[tags]",
		"@include[module]",
	)
	module: tuple[str, ...] = (
		"@type[genres]",
		"attribute",
	)

	module_path: Path = tmp_path / "module.mcs"
	entry_point: Path = tmp_path / "main.mcs"
	text.write(module_path, module)
	text.write(entry_point, script)

	classificator = AttributesClassificator(entry_point)
	assert classificator.load() is None
	assert len(classificator.operations) == 1
	result = classificator.classify("attribute")
	assert result is not None
	assert result.type is AttributeType.genre

def test_classificator_register(tmp_path: "Path"):

	script: tuple[str, ...] = (
		"@register",
	)

	entry_point: Path = tmp_path / "main.mcs"
	text.write(entry_point, script)

	classificator = AttributesClassificator(entry_point)
	is_error_raised: bool = False

	try:
		classificator.load()
	except exceptions.utils.classificator.MissingRegisterError:
		is_error_raised = True

	assert is_error_raised is True

def test_classificator_type(tmp_path: "Path"):

	script: tuple[str, ...] = (
		"@type[franchises]",
		"attribute",
	)

	entry_point: Path = tmp_path / "main.mcs"
	text.write(entry_point, script)

	classificator = AttributesClassificator(entry_point)
	assert classificator.load() is None
	result = classificator.classify("attribute")
	assert result is not None
	assert result.type is AttributeType.franchise

def test_renaming(tmp_path: "Path"):

	script: tuple[str, ...] = (
		"attribute > attribute2",
	)

	entry_point: Path = tmp_path / "main.mcs"
	text.write(entry_point, script)

	classificator = AttributesClassificator(entry_point)
	assert classificator.load() is None
	result = classificator.classify("attribute")
	assert result is not None
	assert result.result == "attribute2"

def test_compare_with_register(tmp_path: "Path"):

	register: dict[str, tuple[str, ...]] = {
		"tags": ("attribute",),
	}
	script: tuple[str, ...] = (
		"@register",
		"@type[genres]",
		"attribute",
	)

	register_path: Path = tmp_path / "register.json"
	entry_point: Path = tmp_path / "main.mcs"
	json.write(register_path, register)
	text.write(entry_point, script)

	classificator = AttributesClassificator(entry_point)
	classificator.load_register(register_path)
	assert classificator.load() is None
	compare_result = classificator.compare_with_register()
	assert len(compare_result) == 1
