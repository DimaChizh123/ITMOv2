---
name: sudoku-assistant
description: Use ONLY when the user asks for Sudoku help, validating a 9x9 grid and requesting a logical hint via the MCP server `sudoku.hint`. Trigger on keywords: sudoku, подсказка, 9x9, X-Wing.
---

# Судоку-ассистент

Этот skill направляет задачу к MCP серверу `sudoku`, tool `sudoku.hint`.

Правила:

- Проверяйте, что вход — матрица 9x9 из чисел 0–9, где 0 означает пустую клетку.
- Не решайте судоку самостоятельно; вызывайте `sudoku.hint`.
- Возвращайте пользователю понятную подсказку или понятную ошибку от сервера.
- Соблюдайте правила проекта из `AGENTS.md` и запускайте автопроверку после изменений.
- Для сложных судоку сервер поддерживает: Locked Candidates (pointing/claiming), Naked Pair, X-Wing, XY-Wing, Swordfish. В таких случаях ответ содержит `eliminations` — список кандидатов к удалению.

Пример вызова:

```
tool: sudoku.hint
args: { "grid": [[0,0,0,2,6,0,7,0,1], ...] }
```

Формат ответа:

```
{ ok: true, result: {
  type: "naked_single" | "hidden_single_row" | "hidden_single_col" | "hidden_single_box" |
        "locked_candidate_pointing" | "locked_candidate_claiming" |
        "naked_pair" | "x_wing" | "xy_wing" | "swordfish" | "none",
  message: string,
  placement?: { row, col, value },
  eliminations?: Array<{ row, col, remove }>
}}
```
