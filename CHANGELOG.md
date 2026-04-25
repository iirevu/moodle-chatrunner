# ChatRunner Change Log


## Unreleased

## [0.2.0] - Unreleased

### Added

+ Config in TOML format
+ Batch testing mode, taking question/answer collection from TOML
+ Optionally add question-specific grading criteria
+ prettyprint script
+ Added the jobe-production docker image

### Changed

+ Use JSON schema in the OpenAI API to force the correct JSON format.
+ Use conversation history in the OpenAI API to give previous answers and feedback.
+ Substantial refactoring:
    + new GraderState class
    + moved the parsing of GPT output to the TestResults class
    + cleaner API for the TestResults class

### Fixed

## [0.1.0] - 2025-11-29

+ Intiial release working with OpenAI API, as released on PyPI.
