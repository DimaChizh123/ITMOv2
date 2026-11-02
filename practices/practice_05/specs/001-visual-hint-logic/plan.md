# План реализации: Visual Hint Logic (Логика)

Цель: реализовать расширение MCP sudoku.hint/sudoku.patterns под визуальный контракт (0-based координаты, visual-блок, card.example в унифицированном формате) и поддержку html_out. Минимальные правки, без изменения текущих контрактов по умолчанию.

1. Парсинг аргументов и совместимость
- Добавить чтение `args.visual` (bool, по умолчанию False для новых полей; текущее verbose поведение сохранить).
- Добавить чтение `args.html_out` (Optional[str]). Не влияет на JSON-ответ; добавляет побочный эффект записи HTML.
- Не менять существующие ответы при `visual` не задан или False.

2. Подготовка утилит
- Использовать существующую `gen_all_candidates(grid)` для расчёта матрицы кандидатов 9×9.
- Ввести `build_visual_action(result)`:
  - Если в `result` есть `placement`, вернуть `{type:"placement", placement:{row,col,value}}`.
  - Если есть `eliminations`, вернуть `{type:"elimination", eliminations:[{row,col,remove}]}`.
  - При наличии обоих — отдавать оба поля в одном объекте (action.type можно опустить или выбрать "elimination"; визуализатор поддержит оба списка).
- Ввести `build_visual_pattern(result, grid)` для унификации anchors/params по каждому паттерну на основе уже возвращаемых полей (`digit`, `rows`, `cols`, `pivot`, `pincers`, `box` и т.д.).

3. Расширение sudoku.hint (успешный путь)
- После нахождения `hint` или `adv` и перед возвратом JSON:
  - Если `visual`:
    - `visual.grid = grid`.
    - `visual.candidates = gen_all_candidates(grid)`.
    - `visual.pattern = build_visual_pattern(result, grid)`.
    - `visual.action = build_visual_action(result)`.
    - `card = build_card(result.type)` (см. п.4), включая унифицированный example.
- Если подсказка не найдена (type:"none") и `visual`:
  - Вернуть `visual.grid` и `visual.candidates`, а `pattern`, `action`, `card` не включать (или null).

4. Карточка паттерна и example
- Функция `build_card(type_id)`:
  - Берёт карточку из PATTERN_CARDS[type_id].
  - На основе `card.example.grid` вычисляет candidates через `gen_all_candidates`.
  - На основе `card.example.highlights` формирует `example.pattern.anchors` (преобразовать в роли по технике) и `example.action`:
    - Если highlights.eliminations заданы с `digit`, трансформировать в `{row,col,remove}`.
    - Если доступны координаты целевой клетки для single, собрать `placement`.
  - Вернуть карточку с полями: title, difficulty, summary, intuition, how_to_apply (list[str]), example в унифицированном визуальном формате.
- Для hidden_single_* заполнить в реестре координаты примеров (отдельная правка данных), чтобы anchors/action были ненулевыми.

5. Генерация HTML (html_out)
- Общая функция рендера HTML (inline CSS), без JS.
- В sudoku.hint:
  - При `visual:true` и `html_out` — рендер основного поля и боковой панели (card + card.example).
  - При ошибке contradiction и `visual:true` + `html_out` — рендер страницы с баннером ошибки и сеткой input grid (без anchors/action/card).
- В sudoku.patterns:
  - При `visual:true` и `html_out` — рендер карточки и card.example без основного поля (или с пустым основным разделом).

6. Ошибки и поведение
- Формат JSON ошибок не меняется.
- Только при сочетании `visual:true` и `html_out` генерируется HTML даже при ошибках (в частности, contradiction).

7. Тестирование и верификация
- Проверить без visual/html_out — идентичность историческому ответу.
- Проверить: visual:true с подсказкой (anchors/action/card присутствуют, координаты 0-based, размеры 9×9).
- Проверить: visual:true с none (только grid/candidates).
- Проверить: contradiction + visual:true + html_out (HTML с баннером ошибки и сеткой).
- Запуск `python3 scripts/verify.py` должен проходить.

8. Ограничения и примечания
- 0-based в данных — строгое правило. UI преобразует подписи.
- Не смешивать remove и digit: в action использовать только remove/value. В карточке в highlights может встречаться digit — преобразовывать.
- Минимизировать объём изменений в существующих функциях; всё новое изолировать в хелперах.
