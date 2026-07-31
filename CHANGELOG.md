# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.3] - 2026-07-31

### Changed

- Refactored into `clickup_mcp` package with retry logic, error handling, and 17 new tools.

### Fixed

- Load `.env` automatically so `CLICKUP_API_TOKEN` is picked up without manual export.
- Pin `mcp<2` to avoid breakage from v2 dropping `mcp.server.fastmcp`.

## [0.0.2] - 2026-06-15

### Added

- `get_members` tool to resolve user names to ClickUp user IDs.

## [0.0.1] - 2026-06-08

### Added

- Initial release with ClickUp task management tools.
- `markdown_content` field for rich task descriptions.
- `custom_id` field included in all task responses.
- GitHub Actions CI test workflow for Python 3.12-3.14.
- Full pytest suite with 100% coverage target.

### Fixed

- Handle empty response from delete task endpoint gracefully.

[Unreleased]: https://github.com/ashleykleynhans/clickup-mcp-server/compare/v0.0.3...HEAD
[0.0.3]: https://github.com/ashleykleynhans/clickup-mcp-server/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/ashleykleynhans/clickup-mcp-server/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/ashleykleynhans/clickup-mcp-server/releases/tag/v0.0.1
