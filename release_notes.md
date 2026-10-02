# System Manager Config Tool CLI - Release Notes

## Version 25.12.00 - Initial Release

**Release Date:** 2025-12-17

### Features
- Generation of the System Manager FW configuration
- Storing the configuration in a JSON database
- Input validation and problem reporting
- Exporting an enhanced configuration to the CFG format
- Support for i.MX 95 devices
- Support for i.MX 943 devices

## Version 26.03.00

**Release Date:** 2026-03-26

### Features
- Supported `kpaen` and `sidsz` parameters processing
- Updated FuSa task structure generation in config_fusa.
- Added MRC origin and region size to the chip database
- Improved validation
- Fixed BASE, special test, and board-resource permission generation
- Support for i.MX 952 devices

## Version 26.06.00

**Release Date:** 2026-06-26

### Features
- Added the`dom_clr_unused` parameter support for MBC/MRC resources
- Added the `dom_exclusive` resource parameter validation
- Added TRDC MBC/MRC deduplication and the `dup` command with agent filtering
- Added automatic resource loading during CFG file pre-processing
- Added SMCT version validation from `user_configuration.json`
- Extended TRDC configuration records generation

### Bug Fixes
- Fixed missing parser when loading device/board configurations

## Version 26.09.00

**Release Date:** 2026-09-25

### Features
- Support for i.MX 937 devices

### Bug Fixes
- Preserved duplicate `start=`/`stop=` order entries in LM start/stop sequences (Perl parity); duplicate entries are now reported as validation errors instead of being silently discarded.
- Strengthened JSON schema validation and resolved false-positive validation errors for loopback mailboxes and non-SCMI channels.
- Fixed an uncaught crash when a domain/LM uses an out-of-range `did`; the tool now reports a clear configuration error.
- Fixed an issue where hdr_parser incorrectly identified editor backup files (.bak, .orig) as SM FW headers, resulting in duplicate resources and silent configuration symbol loss.
