# Feature Specification: Visual Hint Logic

**Feature Branch**: `[001-visual-hint-logic]`

**Created**: 2026-11-02

**Status**: Draft

**Input**: User description: "Визуализация подсказок судоку и привязка теоретической справки из каталога паттернов"

## User Scenarios & Testing (mandatory)

### User Story 1 - Визуальный режим ответа (Priority: P1)

Клиент-рендер запрашивает `sudoku.hint` с новым флагом `visual: true` и получает все данные, необходимые для отрисовки: исходную сетку, полную матрицу кандидатов, унифицированные координаты ключевых ячеек найденного паттерна, целевое действие (eliminations/placement) и прикреплённую карточку теории из реестра PATTERNS.

**Why this priority**: Это основная цель фичи — обеспечить фронтенд данными для визуализации подсказки.

**Independent Test**: Запуск MCP с валидной сеткой, где подсказка гарантированно находится; проверка, что ответ содержит `result.visual` со всеми обязательными полями и корректными размерами матриц (9×9), и `result.card` с полями из PATTERNS.

**Acceptance Scenarios**:

1. Given валидная сетка 9×9, When вызов `sudoku.hint` с `{"grid": [...], "visual": true}`, Then ответ `ok: true` содержит `result.type != "none"`, `result.visual.grid` == входной сетке, `result.visual.candidates` — матрица 9×9, `result.visual.pattern.anchors` — список координат с ролями, и `result.card.id` == `result.type`.
2. Given подсказки типа elimination, When визуальный режим включён, Then `result.visual.action.type == "elimination"` и присутствует `eliminations[]` с полем `remove`.
3. Given подсказки типа placement, When визуальный режим включён, Then `result.visual.action.type == "placement"` и присутствует `placement {row,col,value}`.

---

### User Story 2 - Обратная совместимость (Priority: P1)

При отсутствии флага `visual` или при `visual: false` поведение `sudoku.hint` полностью совпадает с текущим: формат ответа и поля не меняются; новые поля не добавляются.

**Why this priority**: Требование Конституции: стабильные контрактные интерфейсы MCP; по умолчанию не ломать существующие соглашения.

**Independent Test**: Сравнение ответов старой и новой версии при вызове без `visual`: поля и значения идентичны.

**Acceptance Scenarios**:

1. Given валидная сетка, When вызов `sudoku.hint` без `visual`, Then ответ не содержит `result.visual` и `result.card`, и формат совпадает с историческим.

---

### User Story 3 - Отсутствие подсказки (Priority: P2)

Если подсказка не найдена, сервер возвращает `type: "none"` и сообщение как сейчас. В визуальном режиме дополнительно возвращается сетка и матрица кандидатов, а `pattern`, `action`, `card` опускаются или равны `null`.

**Why this priority**: Рендер всё равно может отрисовать текущую ситуацию (с кандидатовыми), даже если подсказки нет.

**Independent Test**: Вызов с сеткой, где подсказка не обнаруживается; проверка `result.type == "none"` и наличия `result.visual.grid` и `result.visual.candidates`.

**Acceptance Scenarios**:

1. Given сетка без подсказок, When `visual: true`, Then `ok: true`, `result.type: "none"`, `result.visual.grid` и `result.visual.candidates` присутствуют, `result.visual.pattern == null`, `result.visual.action == null`, `result.card` отсутствует.

---

### User Story 4 - Строгая валидация и ошибки (Priority: P2)

При неверных входных данных или противоречиях сервер возвращает понятные ошибки без попытки «чинить» вход.

**Why this priority**: Проектные правила требуют строгой валидации и читаемых сообщений ошибок.

**Independent Test**: Серия вызовов с невалидной сеткой, пустым/неправильным JSON, противоречиями — проверка формата ошибок.

**Acceptance Scenarios**:

1. Given некорректная матрица (не 9×9 или содержит числа вне 0–9), When вызов `sudoku.hint`, Then `ok: false` и `error: "Grid must be 9x9 array of integers 0-9"`.
2. Given валидный формат, но противоречие в строке/столбце/блоке, When вызов, Then `ok: false` и `error: "Contradiction: Row X has duplicate D"` (или Column/Box — как сейчас).
3. Given некорректный JSON, When вызов, Then `ok: false` и `error: "Invalid JSON input"`.

### Edge Cases

- Сетка полностью заполнена без противоречий: `type` может быть `none`; в визуальном режиме возвращается `grid` и пустые кандидаты матрицы.
- Сетка с несколькими возможными техниками: возвращается первая найденная по текущему порядку (как сейчас); `card` соответствует `result.type`.
- `verbose: false` и `visual: true`: поля `steps` не включаются; визуальные поля включаются.

## Requirements (mandatory)

### Functional Requirements

- FR-001: Расширить API `sudoku.hint` опциональным флагом `visual` (boolean, по умолчанию `false`). При `visual: true` сервер добавляет к привычному ответу блоки для визуализации, не меняя существующие поля и их значения.
- FR-002: В визуальном режиме сервер возвращает исходную сетку: `result.visual.grid: number[9][9]` (координаты индексируются с 0).
- FR-003: В визуальном режиме сервер возвращает полную матрицу кандидатов: `result.visual.candidates: number[][9][9]`, где для заполненных клеток массив кандидатов пустой `[]`. Размеры строго 9×9.
- FR-004: Унифицированная структура опорных координат паттерна: `result.visual.pattern`.
  - Формат: `{ id: string, anchors: Array<{row:number, col:number, role:string}>, params?: object }`.
  - `id` равен `result.type` из текущего MCP (`naked_single`, `hidden_single_row`, `locked_candidate_pointing`, `x_wing`, `swordfish`, `xy_wing`, `naked_pair`, `locked_candidate_claiming`, `hidden_single_col`, `hidden_single_box`).
  - `anchors` — единый список ключевых клеток с ролью. Роли нормируются:
    - naked_single: `role: "target"` для единственной клетки.
    - hidden_single_row/col/box: `role: "target"` для найденной клетки.
    - locked_candidate_pointing: `role: "box_candidate"` для всех кандидатов цифры внутри блока, которые лежат в одной линии; допускается добавить `params: {digit:number, box:{br,bc}, line:{kind:"row"|"col", index:number}}`.
    - locked_candidate_claiming: `role: "line_candidate"` для всех кандидатов цифры в строке/столбце, лежащих в одном блоке; `params` аналогично (`digit`, `box`, `line`).
    - naked_pair: `role: "pair"` для двух клеток пары; `params: {pair:[number,number], unit:{kind:"row"|"col"|"box", index:number|{br,bc}}}`.
    - x_wing: `role: "corner"` для четырёх углов прямоугольника; `params: {digit:number, rows:[number,number], cols:[number,number]}`.
    - xy_wing: одна опора `role: "pivot"` и два пинцера `role: "pincer"`; `params: {pivot_pair:[x,y], pincer_pairs:[[x,z],[y,z]], digit:number}`.
    - swordfish: `role: "row_candidate"` или `role: "col_candidate"` для соответствующих клеток шаблона; `params: {digit:number, rows:[...], cols:[...]}`.
- FR-005: Унифицированное действие: `result.visual.action`.
  - Формат: `{ type: "elimination"|"placement", eliminations?: Array<{row:number, col:number, remove:number}>, placement?: {row:number, col:number, value:number} }`.
  - Значения и координаты совпадают с текущими полями MCP (`eliminations` с `remove`, а не с `digit`).
- FR-006: При `visual: true` сервер прикрепляет карточку теории паттерна из реестра: `result.card` = объект из `PATTERN_CARDS[result.type]`.
  - Совместимость: карточка добавляется только в визуальном режиме и не влияет на базовый ответ.
  - Примечание: в `result.card.example.highlights.eliminations` используется поле `digit` (демонстрационные данные), не смешивать с `result.visual.action.eliminations.remove`.
- FR-007: При `type: "none"` и `visual: true` сервер возвращает `result.visual.grid` и `result.visual.candidates`; поля `result.visual.pattern`, `result.visual.action`, `result.card` отсутствуют или равны `null`.
- FR-008: Поле `verbose` продолжает работать как сейчас: влияет только на `result.steps`. Визуальные поля не зависят от `verbose`.

### Key Entities

- VisualHintRequest: `{ tool: "sudoku.hint", args: { grid: number[9][9], verbose?: boolean, visual?: boolean } }`.
- VisualHintResponse: `{ ok: boolean, error?: string, result?: { type: string, message: string, steps?: string[], visual?: { grid: number[9][9], candidates: number[][], pattern?: { id: string, anchors: Array<{row, col, role}>, params?: object }|null, action?: { type: "elimination"|"placement", eliminations?: Array<{row, col, remove}>, placement?: {row, col, value} }|null }, card?: object } }`.

## Success Criteria (mandatory)

### Measurable Outcomes

- SC-001: При `visual: true` ответ содержит матрицу кандидатов строго 9×9, проверяем размерность и типы элементов.
- SC-002: Для всех поддержанных техник подсказки `anchors` заполняются в соответствии с нормированными ролями (минимум 1 якорь для single; 2 для naked_pair; 4 для x_wing; >=6 для swordfish по конфигурации).
- SC-003: `result.card.id` всегда равен `result.type` при наличии подсказки.
- SC-004: При отсутствии подсказки в визуальном режиме рендер может корректно отобразить сетку и кандидатов; сервер не возвращает ошибки для случая `type: "none"`.

## Assumptions

- Реализация выполняется в `mcp/sudoku/index.py` только с использованием Python 3 стандартной библиотеки.
- UI — статичное HTML+CSS; текущая спецификация описывает логический API, а не визуальные стили.
- Обратная совместимость: новые поля и флаги добавляются опционально, поведение по умолчанию не меняется.
- Реестр PATTERNS — текущий `PATTERN_CARDS` в `index.py`; сервер выбирает карточку по `result.type`.

## API Contract Extension

### Request

Пример запроса визуального режима:

```json
{
  "tool": "sudoku.hint",
  "args": {
    "grid": [[4,0,0,0,5,0,0,0,0],[5,0,1,0,8,0,0,0,0],[0,0,0,7,9,6,0,0,0],[0,0,7,0,0,0,0,0,0],[0,0,9,0,0,8,6,0,0],[0,5,0,0,0,0,9,0,7],[0,0,0,0,0,3,0,0,5],[0,0,0,6,0,0,0,8,0],[2,3,0,0,0,0,0,1,0]],
    "verbose": true,
    "visual": true
  }
}
```

### Response (success with hint)

```json
{
  "ok": true,
  "result": {
    "type": "naked_pair",
    "message": "Голая пара {x,y} ...",
    "eliminations": [{"row":0,"col":5,"remove":2}],
    "steps": ["..."],
    "visual": {
      "grid": [[...9x9...]],
      "candidates": [[[...]], ... 9x9],
      "pattern": {
        "id": "naked_pair",
        "anchors": [
          {"row":0,"col":1,"role":"pair"},
          {"row":0,"col":2,"role":"pair"}
        ],
        "params": {"pair": [x,y], "unit": {"kind": "row", "index": 0}}
      },
      "action": {
        "type": "elimination",
        "eliminations": [{"row":0,"col":5,"remove":2}]
      }
    },
    "card": {"id": "naked_pair", "title": "Голая пара (Naked Pair)", "summary": "..."}
  }
}
```

### Response (success, none)

```json
{
  "ok": true,
  "result": {
    "type": "none",
    "message": "Подсказок не найдено на текущем уровне",
    "steps": ["..."],
    "visual": {
      "grid": [[...9x9...]],
      "candidates": [[[...]], ... 9x9],
      "pattern": null,
      "action": null
    }
  }
}
```

### Error Formats (unchanged)

- Invalid JSON input: `{ "ok": false, "error": "Invalid JSON input" }`.
- Unknown tool: `{ "ok": false, "error": "Unknown tool. Use sudoku.hint or sudoku.patterns" }`.
- Invalid grid shape/values: `{ "ok": false, "error": "Grid must be 9x9 array of integers 0-9" }`.
- Contradiction: `{ "ok": false, "error": "Contradiction: Row X has duplicate D" }` (или Column/Box).

## Mapping Rules per Pattern (server-side filling of anchors)

- naked_single: anchors = [{row, col, role:"target"}] из `placement`.
- hidden_single_row/col/box: anchors = [{row, col, role:"target"}] из `placement`.
- locked_candidate_pointing: anchors = все клетки в блоке, где искомая `digit` является кандидатом и ограничена одной строкой/столбцом; role:"box_candidate". params включает `{digit, box:{br,bc}, line:{kind,index}}`.
- locked_candidate_claiming: anchors = все клетки строки/столбца, где `digit` кандидаты и лежат в одном блоке; role:"line_candidate". params включает `{digit, box:{br,bc}, line:{kind,index}}`.
- naked_pair: anchors = две клетки пары; role:"pair"; params `{pair, unit}`.
- x_wing: anchors = четыре угла (две строки × два столбца); role:"corner"; params `{digit, rows, cols}`.
- xy_wing: anchors = pivot (role:"pivot") и два pincers (role:"pincer"); params `{pivot_pair, pincer_pairs, digit}`.
- swordfish: anchors = все клетки в выбранной конфигурации (по строкам или столбцам); role:"row_candidate" или "col_candidate" в зависимости от варианта; params `{digit, rows, cols}`.

Примечание: координаты `row`, `col` — 0-базные индексы [0..8]. Текстовые сообщения могут использовать 1-базные значения как сейчас.

## Validation Rules

- Входной `grid` проверяется на:
  - Тип: список из 9 списков.
  - Диапазон значений: целые числа 0–9.
  - Противоречия: дубликаты по строкам, столбцам и блокам (как реализовано сейчас).
- При ошибках возвращается `{ok:false, error:...}` без попытки корректировать вход.
- При `visual: true` дополнительные поля строятся только после успешной базовой валидации и вычисления подсказки.

## Non-Goals

- Не изменять существующую логику поиска подсказок, порядок их проверки и текущее текстовое содержимое сообщений.
- Не добавлять новые обязательные аргументы или изменять контракт `sudoku.patterns` (он уже строго валидирует `pattern`).
