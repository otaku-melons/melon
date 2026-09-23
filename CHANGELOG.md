# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

For visual categorization of changes emojis are used in accordance with [gitmoji](https://gitmoji.dev).

## [1.0.0-rc.6] - YYYY-MM-DD

### ✨ Added
- Now extensions can create CLI handlers.
- Command `melon run` for running extensions CLI.
- Method `set_extra_data()` for title data.
- Universal method `run_extension()` for source operrator (can run extensions by name as `BaseExtension`).
- Parser linter.
- Extensions activation states manager.
- Chapters amending progress.
- Message if chapter is empty after amending.

### 🎨 Changed
- Extensions options settings no more appears in parser config if extension doesn't provide options.
- Extensions operator moved into parser operator property.
- Extensions now must use [pydantic](https://github.com/pydantic/PYDANTIC) models for options typing.
- Unified `amend()` methods of parsers.
- Updated syntax to newer Python versions.

### 🗑️ Deprecated
- Source operator extension property replaced by extension operator. 

### 🔥 Removed
- Property `parser_settings` for extensions (reason is invariant typing issue).

### 🐛 Fixed
- Many spelling issues with [typos](https://pypi.org/project/typos).

### 🔒️ Security
