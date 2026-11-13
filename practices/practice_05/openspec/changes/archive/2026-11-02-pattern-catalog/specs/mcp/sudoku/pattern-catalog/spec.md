# Spec Delta: Sudoku Patterns Catalog

## Purpose
Добавляет в проект новый MCP-инструмент `sudoku.patterns`, который предоставляет справочные карточки по техникам судоку. Цель — дать новичкам понятные описания и ориентиры для изучения приёмов, не изменяя поведение `sudoku.hint`. Ответы локализованы на русском, латинские названия техник указываются в скобках; JSON сериализуется с `ensure_ascii=False`.

## ADDED Requirements

### Requirement: Возврат списка паттернов
Система ДОЛЖНА, когда `args` отсутствует или является пустым объектом, возвращать успешный ответ со списком доступных идентификаторов паттернов в поле `result.patterns`.

#### Scenario: Пустые аргументы → список паттернов
- **WHEN** вызван `{ "tool": "sudoku.patterns", "args": {} }`
- **THEN** ответ `{ "ok": true, "result": { "patterns": ["naked_single", "hidden_single_row", "hidden_single_col", "hidden_single_box", "locked_candidate_pointing", "locked_candidate_claiming", "naked_pair", "x_wing", "xy_wing", "swordfish"] } }`

### Requirement: Возврат карточки паттерна
Система ДОЛЖНА, когда передан валидный `args.pattern` (непустая строка), возвращать успешный ответ с карточкой паттерна, включающей минимум поля `id`, `title`, `difficulty`, `summary`, `intuition`, `how_to_apply`, а также `example.grid` (строгая 9×9 матрица чисел 0–9) и `example.highlights`.

#### Scenario: Валидный pattern → детализированная карточка
- **WHEN** вызван `{ "tool": "sudoku.patterns", "args": { "pattern": "naked_single" } }`
- **THEN** ответ `{ "ok": true, "result": { "id": "naked_single", "title": "Голый сингл (Naked Single)", "difficulty": "Базовый", "summary": "...", "intuition": "...", "how_to_apply": ["..."], "example": { "grid": [[8,0,0,0,0,0,0,0,0], ... 9×9 ...], "highlights": { "cells": [...], "eliminations": [...] } } } }`

### Requirement: Строгая валидация — лишние поля недопустимы
Система ДОЛЖНА отклонять любые аргументы, отличные от `pattern`, возвращая ошибку `"Invalid arguments: only 'pattern' is supported"`.

#### Scenario: Лишние поля → ошибка
- **WHEN** вызван `{ "tool": "sudoku.patterns", "args": { "grid": [[]] } }`
- **THEN** ответ `{ "ok": false, "error": "Invalid arguments: only 'pattern' is supported" }`

### Requirement: Строгая валидация — pattern обязателен и непустой
Система ДОЛЖНА возвращать ошибку `"Invalid arguments: 'pattern' must be a non-empty string"`, когда `pattern` отсутствует, пустой или имеет иной тип, отличный от строки.

#### Scenario: Пустой pattern → ошибка
- **WHEN** вызван `{ "tool": "sudoku.patterns", "args": { "pattern": "" } }`
- **THEN** ответ `{ "ok": false, "error": "Invalid arguments: 'pattern' must be a non-empty string" }`

#### Scenario: Неверный тип pattern → ошибка
- **WHEN** вызван `{ "tool": "sudoku.patterns", "args": { "pattern": 123 } }`
- **THEN** ответ `{ "ok": false, "error": "Invalid arguments: 'pattern' must be a non-empty string" }`

### Requirement: Неизвестный идентификатор паттерна
Система ДОЛЖНА возвращать ошибку вида `"Unknown pattern id: <id>"` при запросе карточки неизвестного идентификатора.

#### Scenario: Неизвестный pattern → ошибка
- **WHEN** вызван `{ "tool": "sudoku.patterns", "args": { "pattern": "no_such" } }`
- **THEN** ответ `{ "ok": false, "error": "Unknown pattern id: no_such" }`

### Requirement: Совместимость — сообщение для неизвестного tool
Система ДОЛЖНА возвращать ошибку `"Unknown tool. Use sudoku.hint or sudoku.patterns"` при обращении к неизвестному tool.

#### Scenario: Неизвестный tool → рекомендация доступных
- **WHEN** вызван `{ "tool": "no_such_tool", "args": {} }`
- **THEN** ответ `{ "ok": false, "error": "Unknown tool. Use sudoku.hint or sudoku.patterns" }`
