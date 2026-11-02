# mcp/sudoku/pattern-catalog Specification

## Purpose
Этот capability предоставляет MCP-инструмент `sudoku.patterns`, который отдаёт справочные карточки по техникам судоку. Он предназначен для объяснений и обучения: описывает, как распознавать техники, и даёт примеры, при этом не меняя поведение `sudoku.hint`. Ответы локализованы на русском (с латинскими именами в скобках) и сериализуются с `ensure_ascii=False`.

## Requirements

### Requirement: Возврат списка паттернов
The system SHALL, when `args` is absent or an empty object, return a successful response with the list of available pattern identifiers in `result.patterns`.

#### Scenario: Пустые аргументы → список паттернов
- **WHEN** вызван `{ "tool": "sudoku.patterns", "args": {} }`
- **THEN** ответ `{ "ok": true, "result": { "patterns": ["naked_single", "hidden_single_row", "hidden_single_col", "hidden_single_box", "locked_candidate_pointing", "locked_candidate_claiming", "naked_pair", "x_wing", "xy_wing", "swordfish"] } }`

### Requirement: Возврат карточки паттерна
The system SHALL, when a valid `args.pattern` (non-empty string) is provided, return a successful response with a pattern card including at minimum `id`, `title`, `difficulty`, `summary`, `intuition`, `how_to_apply`, and `example.grid` (strict 9×9 matrix of integers 0–9) and `example.highlights`.

#### Scenario: Валидный pattern → детализированная карточка
- **WHEN** вызван `{ "tool": "sudoku.patterns", "args": { "pattern": "naked_single" } }`
- **THEN** ответ `{ "ok": true, "result": { "id": "naked_single", "title": "Голый сингл (Naked Single)", "difficulty": "Базовый", "summary": "...", "intuition": "...", "how_to_apply": ["..."], "example": { "grid": [[8,0,0,0,0,0,0,0,0], ... 9×9 ...], "highlights": { "cells": [...], "eliminations": [...] } } } }`

### Requirement: Строгая валидация — лишние поля недопустимы
The system MUST reject any arguments other than `pattern`, returning the error `"Invalid arguments: only 'pattern' is supported"`.

#### Scenario: Лишние поля → ошибка
- **WHEN** вызван `{ "tool": "sudoku.patterns", "args": { "grid": [[]] } }`
- **THEN** ответ `{ "ok": false, "error": "Invalid arguments: only 'pattern' is supported" }`

### Requirement: Строгая валидация — pattern обязателен и непустой
The system MUST return the error `"Invalid arguments: 'pattern' must be a non-empty string"` when `pattern` is missing, empty, or has a non-string type.

#### Scenario: Пустой pattern → ошибка
- **WHEN** вызван `{ "tool": "sudoku.patterns", "args": { "pattern": "" } }`
- **THEN** ответ `{ "ok": false, "error": "Invalid arguments: 'pattern' must be a non-empty string" }`

#### Scenario: Неверный тип pattern → ошибка
- **WHEN** вызван `{ "tool": "sudoku.patterns", "args": { "pattern": 123 } }`
- **THEN** ответ `{ "ok": false, "error": "Invalid arguments: 'pattern' must be a non-empty string" }`

### Requirement: Неизвестный идентификатор паттерна
The system MUST return the error `"Unknown pattern id: <id>"` when requesting a card for an unknown identifier.

#### Scenario: Неизвестный pattern → ошибка
- **WHEN** вызван `{ "tool": "sudoku.patterns", "args": { "pattern": "no_such" } }`
- **THEN** ответ `{ "ok": false, "error": "Unknown pattern id: no_such" }`

### Requirement: Совместимость — сообщение для неизвестного tool
The system MUST return the error `"Unknown tool. Use sudoku.hint or sudoku.patterns"` when invoked with an unknown tool.

#### Scenario: Неизвестный tool → рекомендация доступных
- **WHEN** вызван `{ "tool": "no_such_tool", "args": {} }`
- **THEN** ответ `{ "ok": false, "error": "Unknown tool. Use sudoku.hint or sudoku.patterns" }`
