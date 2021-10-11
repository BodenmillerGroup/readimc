# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2021-10-11

Renamed `IMCMCDFile` and `IMCTXTFile` to `IMCMcdFile` and `IMCTxtFile`, respectively

## [0.3.0] - 2021-10-11

Retain meta-information after closing a file

Pre-compile regular expressions for faster parsing

Separately store and expose channel metals & masses; change channel name format from `f"{metal}({mass})"` to `f"{metal}{mass}"` for backwards compatibility with imctools

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


[0.3.1]: https://github.com/BodenmillerGroup/readimc/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/BodenmillerGroup/readimc/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/BodenmillerGroup/readimc/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/BodenmillerGroup/readimc/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/BodenmillerGroup/readimc/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/BodenmillerGroup/readimc/releases/tag/v0.1.0
