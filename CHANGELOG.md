# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2023-08-11

Implemented checks for overlapping raw data blocks in MCD file metadata [#6](https://github.com/BodenmillerGroup/readimc/issues/6)

Implemented lenient extraction of corrupted imaging data  [#19](https://github.com/BodenmillerGroup/readimc/pull/19)

## [0.6.2] - 2023-01-31

Maintenance release

Made modules public

Renamed `MCDFile.metadata` to `MCDFile.schema_xml`

Toolchain (black, flake8, isort, mypy, pre-commit)

Updated GitHub Actions workflows

Small bugfixes and improvements

Python 3.11 compatibility

## [0.6.1] - 2022-01-28

Rename `MCDXMLParser` to `MCDParser`

Refactor and simplify `MCDParser` usage

BREAKING CHANGES in `MCDFile`:
- Renamed `MCDFile.metadata_xml_str` to `MCDFile.metadata`
- Removed `MCDFile.metadata_xml` and `MCDFile.metadata_xmlns` (use `MCDParser` instead)

## [0.6.0] - 2022-01-28

Expose `MCDXMLParser`

## [0.5.0] - 2021-12-02

Refactored metadata accessors

Refactored accessors for ROI points/coordinates

Added link between acquisitions and associated panoramas

Renamed `IMCMcdFile` and `IMCTxtFile` to `MCDFile` and `TXTFile`

## [0.4.2] - 2021-11-01

Use pandas for reading TXT files (better performance)

## [0.4.1] - 2021-11-01

Added support for Python 3.10

## [0.4.0] - 2021-10-19

Added support for older versions of the Fluidigm software

Use heuristics for determining acquisition start position

Add offline unit tests for data from (Damond et al., 2019)

Fix a numerical bug in determining panorama image dimensions

## [0.3.1] - 2021-10-11

Renamed `IMCMCDFile` and `IMCTXTFile` to `IMCMcdFile` and `IMCTxtFile`, respectively

## [0.3.0] - 2021-10-11

Retain meta-information after closing a file

Pre-compile regular expressions for faster parsing

Separately store and expose channel metals & masses; change channel name format from
`f"{metal}({mass})"` to `f"{metal}{mass}"` for backwards compatibility with imctools

## [0.2.0] - 2021-10-09

Use dataclasses instead of NamedTuples

Renamed TXTFile and MCDFile to IMCTXTFile and IMCMCDFile, respectively

IMCTXTFile and IMCMCDFile now implement a shared IMCFileBase interface

IMCTXTFile and Acquisition now implement a shared AcquisitionBase interface

## [0.1.2] - 2021-10-09

Explicit acquisition image reconstruction based on pixel indices

## [0.1.1] - 2021-10-09

Minor documentation changes

## [0.1.0] - 2021-10-09

Initial release
[0.7.0]: https://github.com/BodenmillerGroup/readimc/compare/v0.6.2...v0.7.0
[0.6.2]: https://github.com/BodenmillerGroup/readimc/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/BodenmillerGroup/readimc/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/BodenmillerGroup/readimc/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/BodenmillerGroup/readimc/compare/v0.4.2...v0.5.0
[0.4.2]: https://github.com/BodenmillerGroup/readimc/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/BodenmillerGroup/readimc/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/BodenmillerGroup/readimc/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/BodenmillerGroup/readimc/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/BodenmillerGroup/readimc/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/BodenmillerGroup/readimc/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/BodenmillerGroup/readimc/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/BodenmillerGroup/readimc/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/BodenmillerGroup/readimc/releases/tag/v0.1.0
