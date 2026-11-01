# Tasks

## MCP: sudoku.patterns
- Добавить ветку `tool == "sudoku.patterns"` в `mcp/sudoku/index.py`:
  - Пустые `args` → список доступных `patterns` (из статического реестра).
  - `args.pattern: string` → вернуть карточку; неизвестный `id` → `{"ok": false, "error": "Unknown pattern id: <id>"}`.
  - Строгая валидация: только ключ `pattern` разрешён; иные/лишние → `{"ok": false, "error": "Invalid arguments: only 'pattern' is supported"}`.
  - JSON с `ensure_ascii=False`.
- Сообщение об неизвестном tool:
  - Заменить на: `Unknown tool. Use sudoku.hint or sudoku.patterns`.

## Card registry
- Статический реестр карточек для всех типов из `sudoku.hint` (кроме `none`), в т.ч.:
  - `naked_single`, `hidden_single_row`, `hidden_single_col`, `hidden_single_box`,
  - `locked_candidate_pointing`, `locked_candidate_claiming`,
  - `naked_pair`, `x_wing`, `xy_wing`, `swordfish`.
- Для каждого: заполнить обязательные поля; примеры — реалистичные 9×9 сетки, `highlights` с координатами 0-based.

## Verify
- Добавить тесты:
  - Список паттернов: `{"ok": true, "result.patterns": [...]}`, непустой; содержит `naked_single`.
  - Карточка `x_wing`: проверка полей `id`, `title`, `difficulty`, `summary`, `intuition`, `how_to_apply`, `example.grid` (9×9), `example.highlights` (`cells`, `eliminations`).
  - Неизвестный `pattern` → `{"ok": false, "error": "Unknown pattern id: <id>"}`.
- Улучшить тексты ошибок в verify:
  - Заменить неактуальные формулировки вроде “index.js missing” и “node exited” на корректные для Python: “index.py missing” и “python exited” (или более ясные).

## Synchronization guard
- При добавлении нового `type` в `sudoku.hint` — обновлять реестр и verify-сценарии.

## Docs/Policy
- Обновить AGENTS.md:
  - Добавить политику объяснений: `sudoku.patterns` по `result.type` из `sudoku.hint`; при недоступности — краткое описание без попыток решать сетку.
  - Стандартизировать формат ответа (тип, краткое пояснение, шаги, затем MCP-данные).
  - Правила обработки ошибок входа (строгие; без «починки»).
  - Примеры: сохранить пример для `sudoku.hint`; добавить примеры для `sudoku.patterns` (список и карточка).
  - Примечание о verify-логах: возможны устаревшие упоминания “index.js/node”; ориентироваться на смысл.
