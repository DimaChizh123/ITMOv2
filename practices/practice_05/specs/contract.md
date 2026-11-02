# Контракт Логики и UI (Sudoku Visual Hint)

Версия: 1.0 (Draft)

Область: согласование интерфейса между Командой Логики (MCP sudoku.hint / sudoku.patterns) и Командой UI (HTML визуализатор).

## Выявленные расхождения ДО согласования

- Индексация координат:
  - Логика: 0-based (0..8) в данных; 1-based только в текстовых сообщениях.
  - UI-спека: ожидала 1-based (1..9) во входных данных.
- Роли anchors:
  - Логика: семантические роли (target, box_candidate, line_candidate, pair, corner, pivot, pincer, row_candidate, col_candidate).
  - UI-спека: описывает primary/secondary и допускает произвольные роли без фиксированной семантики.
- Поля действий и наименования цифры:
  - Логика: placement = {row, col, value}; eliminations = [{row, col, remove}]. В PATTERN_CARDS примерные highlights.eliminations используют поле digit (демо), не совпадает с remove.
  - UI-спека: placement/eliminations используют поле digit.
- Тип поля how_to_apply:
  - Логика (PATTERN_CARDS): list[string].
  - UI-спека: string.
- Поведение при противоречии в сетке:
  - Логика: при contradiction возвращает ok:false и не включает grid.
  - UI-спека: хочет видеть страницу с баннером ошибки и (в идеале) отрисованной сеткой.

## Согласованный контракт

- Индексация:
  - Координаты в данных везде строго 0-based (0..8). Перевод в подписи r1..r9, c1..c9 делает исключительно HTML-рендер при отображении.

- Действия:
  - placement: {row:number, col:number, value:number}.
  - eliminations: [{row:number, col:number, remove:number}].
  - Если UI нужен digit, он локально отображает value/remove как digit без изменения контракта MCP.

- Роли anchors:
  - Логика отдаёт семантические роли: target, box_candidate, line_candidate, pair, corner, pivot, pincer, row_candidate, col_candidate.
  - UI маппит роли в акценты: pivot/target/pair/corner/box_candidate/line_candidate/row_candidate/col_candidate → синий акцент (primary); pincer → жёлтый акцент (secondary).

- how_to_apply:
  - Источник истины — массив строк (list[string]). UI рендерит его как список; если придёт одна строка, UI приведёт к массиву [string].

- Ошибки и visual-режим:
  - Формат ошибок JSON не меняется: {ok:false, error:string}.
  - При передаче флага "visual": true логика дополнительно предоставляет исходный grid в генератор HTML. Если указан "html_out", HTML-страница генерируется даже при противоречии: содержит баннер ошибки и отрисованный grid; подсказочные акценты отсутствуют.

## ВАЖНОЕ ДОПОЛНЕНИЕ (Визуализация сетки-примера из карточки паттерна)

- Унификация примера (Команда Логики):
  - Поле card.example при visual:true отдаётся в том же визуальном формате, что и основное поле результата:
    - grid: 9×9 (значения 0..9),
    - candidates: 9×9 — вычисляется автоматически через gen_all_candidates(example.grid),
    - anchors: непустые, с ролями (role) по тем же правилам,
    - action: placement {row, col, value} или eliminations [{row, col, remove}].
  - В PATTERN_CARDS необходимо заполнить пустые highlights у hidden_single_row/hidden_single_col/hidden_single_box реальными координатами на сетке-примере, чтобы сформировать anchors/action.

- Отрисовка сетки-примера (Команда UI):
  - Использовать один и тот же компонент рендера 9×9 (с кандидатами и подсветками) для основного поля и для блока «Наглядный пример техники» (card.example) в боковой панели.

- Вызов HTML-рендера:
  - Инструменты sudoku.hint и sudoku.patterns поддерживают флаг args.html_out: "путь_к_файлу.html". При его передаче сервер генерирует и сохраняет самодостаточную HTML-страницу (inline CSS) со справкой и визуализацией.
  - Отсутствие html_out не меняет JSON-ответ. Наличие html_out добавляет только побочный эффект записи HTML-файла.
  - При ошибке противоречия и visual:true + html_out — HTML строится с баннером ошибки и отрисованным grid (без anchors/action/card).

## Итоговые поля визуального блока (от Логики к UI)

- result.visual:
  - grid: number[9][9],
  - candidates: number[][9][9],
  - pattern: { id:string, anchors:Array<{row:number, col:number, role:string}>, params?:object } | null,
  - action: { type:"placement"|"elimination", placement?:{row:number, col:number, value:number}, eliminations?:Array<{row:number, col:number, remove:number}> } | null.

- result.card:
  - Объект из PATTERN_CARDS[result.type] (title, difficulty, summary, intuition, how_to_apply:list[string]) плюс example в унифицированном визуальном формате (см. выше). При type:"none" — card отсутствует.

## Ответственности

- Команда Логики:
  - Возвращает 0-based координаты, унифицированные anchors и action, candidates 9×9.
  - При visual:true формирует result.card и card.example в унифицированном визуальном формате.
  - При html_out генерирует самодостаточный HTML (только stdlib, без внешних зависимостей), сохраняя обратную совместимость.

- Команда UI:
  - Преобразует только подписи координат в r1..r9/c1..c9 на рендере; данные остаются 0-based.
  - Маппит роли в цвета: primary для pivot/target/pair/corner/box_candidate/line_candidate/row_candidate/col_candidate; secondary для pincer.
  - Использует единый компонент для основного поля и card.example.

## Совместимость и проверка

- По умолчанию (visual:false, без html_out) поведение sudoku.hint и sudoku.patterns не меняется.
- Новые аргументы строго опциональны и не ломают текущие контракты.
- Верификация: добавить кейсы на visual:true (с подсказкой и без), contradiction + visual:true + html_out, а также на корректность card.example.
