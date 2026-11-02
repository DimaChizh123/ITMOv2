# Tasks: Visual Hint Logic (Логика)

## Аргументы и совместимость
1. [ ] Добавить парсинг `args.visual` (bool; по умолчанию False для включения визуальных блоков).
2. [ ] Добавить парсинг `args.html_out` (Optional[str]) в `sudoku.hint` и `sudoku.patterns`.
3. [ ] Гарантировать, что при `visual:false` и без `html_out` ответы полностью совпадают с текущими.

## Визуальные данные (sudoku.hint)
4. [ ] Реализовать `build_visual_action(result)` для формирования `{type, placement?, eliminations?}` на основе текущих полей `placement`/`eliminations`.
5. [ ] Реализовать `build_visual_pattern(result, grid)` и наполнить anchors/params для техник:
   - naked_single, hidden_single_row, hidden_single_col, hidden_single_box,
   - locked_candidate_pointing, locked_candidate_claiming,
   - naked_pair, x_wing, xy_wing, swordfish.
6. [ ] Включать `visual.grid = grid` и `visual.candidates = gen_all_candidates(grid)` при `visual:true`.
7. [ ] При type:"none" — отдавать только grid/candidates; pattern/action/card опускать.

## Карточка паттерна
8. [ ] Функция `build_card(type_id)` для сборки карточки и `card.example` в унифицированном формате:
   - `example.grid` — из PATTERN_CARDS;
   - `example.candidates` — через `gen_all_candidates`;
   - `example.pattern.anchors` и `example.action` — из `example.highlights` (преобразовать digit→remove/value);
   - how_to_apply — list[string].
9. [ ] Обновить данные PATTERN_CARDS для hidden_single_*: заполнить `highlights` подходящими координатами (отдельная правка данных).

## HTML генерация
10. [ ] Реализация рендера HTML (inline CSS, без JS) с двумя режимами:
    - hint: основное поле + боковая справка + card.example;
    - patterns: карточка и card.example без основного поля.
11. [ ] Поддержать сценарий ошибки: при contradiction + visual:true + html_out — HTML с баннером ошибки и сеткой (без anchors/action/card).

## Валидация и тестирование
12. [ ] Убедиться, что новые поля используют 0-based координаты во всех местах.
13. [ ] Набор проверок:
    - без visual/html_out — идентично текущему;
    - visual:true + подсказка (включая anchors/action/card);
    - visual:true + none (только grid/candidates);
    - contradiction + visual:true + html_out (HTML рендерится);
    - sudoku.patterns + visual:true + html_out (HTML карточки).
14. [ ] Запустить `python3 scripts/verify.py` и устранить замечания.

## Риски
- Неконсистентность координат при построении anchors (следить за 0-based).
- Путаница digit vs remove/value (жёстко следовать контракту: action → remove/value; highlights → digit только как исходные данные).
- Рост времени выполнения при расчёте candidates дважды (основное поле и example). Оптимизация по мере необходимости.
