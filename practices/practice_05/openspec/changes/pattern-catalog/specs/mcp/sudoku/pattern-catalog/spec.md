# Spec Delta: Sudoku Patterns Catalog

## Overview
Добавляется MCP tool `sudoku.patterns`, предоставляющий справочные карточки по техникам судоку, синхронизированные с типами, которые возвращает `sudoku.hint`. Цель — дать новичкам понятные описания, не изменяя поведение `sudoku.hint`.

Локализация: человекочитаемые описания на русском; в скобках латинское имя техники. JSON-ответы сериализуются с ensure_ascii=False.

## Tool
- Имя: `sudoku.patterns`

## Вход
Режимы:
- Без аргументов (`args` отсутствует или `{}`): вернуть список доступных идентификаторов.
- С `args.pattern: string`: вернуть карточку указанного паттерна.

Строгая валидация:
- Любые иные поля в `args` → ошибка: `{"ok": false, "error": "Invalid arguments: only 'pattern' is supported"}`
- `pattern` должен быть непустой строкой → иначе ошибка: `{"ok": false, "error": "Invalid arguments: 'pattern' must be a non-empty string"}`
- Поле `grid` не поддерживается и не должно передаваться в `sudoku.patterns`.

## Выход
Успех:
- Список паттернов:
  ```
  {"ok": true, "result": {"patterns": ["naked_single", "..."]}}
  ```
- Карточка:
  ```
  {"ok": true, "result": { /* см. схему карточки ниже */ }}
  ```

Ошибки:
- Неизвестный идентификатор:
  ```
  {"ok": false, "error": "Unknown pattern id: <id>"}
  ```
- Неверные/лишние аргументы:
  ```
  {"ok": false, "error": "Invalid arguments: only 'pattern' is supported"}
  ```
  или
  ```
  {"ok": false, "error": "Invalid arguments: 'pattern' must be a non-empty string"}
  ```

Совместимость:
- `sudoku.hint` без изменений.
- Сообщение об неизвестном tool:
  ```
  {"ok": false, "error": "Unknown tool. Use sudoku.hint or sudoku.patterns"}
  ```

## Поддерживаемые идентификаторы
Список соответствует всем значениям `result.type` из `sudoku.hint` (кроме `none`):
- `naked_single`
- `hidden_single_row`
- `hidden_single_col`
- `hidden_single_box`
- `locked_candidate_pointing`
- `locked_candidate_claiming`
- `naked_pair`
- `x_wing`
- `xy_wing`
- `swordfish`

## Схема карточки (human-friendly минимальная)
Обязательные поля:
- `id`: string. Совпадает с `result.type` из `sudoku.hint`.
- `title`: string. Человекочитаемое имя, например: "Голый сингл (Naked Single)".
- `difficulty`: "Базовый" | "Средний" | "Продвинутый".
- `summary`: string (1–2 предложения простым языком).
- `intuition`: string. Как «увидеть» приём, в чём идея.
- `how_to_apply`: array of strings (3–5 коротких шагов).
- `example`: object:
  - `grid`: 9×9 массив чисел 0–9. Должен выглядеть как реальное судоку — не тривиальная матрица из нулей.
  - `highlights`: object:
    - `cells`: array of {"row": int, "col": int} — ключевые клетки. Индексация 0-based.
    - `eliminations`: array of {"row": int, "col": int, "digit": int} — удаления кандидатов.

Опциональные поля:
- `common_mistakes`: string или array of strings (1–3 типичных ошибки).
- `see_also`: array of string — идентификаторы смежных техник.

Примечания:
- Все координаты (`row`, `col`) 0-based, чтобы совпадать с данными `sudoku.hint`.
- Текстовые поля — на русском; латинское имя техники указывается в скобках (например, "X-Wing").

## Примеры

Список:
```
Вход:
{"tool":"sudoku.patterns","args":{}}

Выход:
{"ok": true, "result": {"patterns": ["naked_single","hidden_single_row","hidden_single_col","hidden_single_box","locked_candidate_pointing","locked_candidate_claiming","naked_pair","x_wing","xy_wing","swordfish"]}}
```

Карточка (пример структуры для `naked_single`):
```
Вход:
{"tool":"sudoku.patterns","args":{"pattern":"naked_single"}}

Выход:
{"ok": true, "result": {
  "id": "naked_single",
  "title": "Голый сингл (Naked Single)",
  "difficulty": "Базовый",
  "summary": "Клетка, у которой остаётся ровно один возможный кандидат.",
  "intuition": "Если все другие цифры исключены правилами строки/столбца/блока, остаётся единственный вариант.",
  "how_to_apply": [
    "Посчитайте кандидатов для пустых клеток.",
    "Найдите клетки с одним кандидатом.",
    "Поставьте это значение и обновите кандидатов."
  ],
  "example": {
    "grid": [[8,0,0,0,0,0,0,0,0],[0,0,3,6,0,0,0,0,0],[0,7,0,0,9,0,2,0,0],[0,5,0,0,0,7,0,0,0],[0,0,0,0,4,5,7,0,0],[0,0,0,1,0,0,0,3,0],[0,0,1,0,0,0,0,6,8],[0,0,8,5,0,0,0,1,0],[0,9,0,0,0,0,4,0,0]],
    "highlights": {
      "cells": [{"row":0,"col":3}],
      "eliminations": []
    }
  },
  "see_also": ["hidden_single_row","hidden_single_col","hidden_single_box"]
}}
```
(Примерная сетка приведена для формы; фактические карточки должны использовать реалистичные сетки, уместные для техники.)
