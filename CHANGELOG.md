# ChatRunner Change Log


## [0.2.0] - Unreleased

### Added

+ Added the jobe-production docker image

### Changed

+ Use JSON schema in the OpenAI API to force the correct JSON format.
+ Use conversation history in the OpenAI API to give previous answers and feedback.
+ Refactoring: GraderState class, some simplifications

### Added

+ Config in TOML format
+ Batch testing mode, taking question/answer collection from TOML
+ Optionally add question-specific grading criteria

### Fixed

## [0.1.0] - 2025-11-29

+ Intiial release working with OpenAI API, as released on PyPI.
