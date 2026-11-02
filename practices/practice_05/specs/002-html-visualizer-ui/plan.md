# Plan: HTML Visualizer UI (002)

Status: Draft

Scope:
- Реализовать самодостаточный HTML-генератор, который принимает `result` по контракту (0-based координаты) и рендерит:
  - Основное поле 9×9 с кандидатами и подсветками (anchors, placement, eliminations).
  - Боковую панель с карточкой паттерна (title, difficulty, summary, intuition, how_to_apply:list) и рендером `card.example` тем же компонентом.
  - Состояния none и error.

Key Decisions:
- Один компонент рендера 9×9 для основного поля и примера из `card.example`.
- Маппинг ролей anchors: primary=синий для pivot/target/pair/corner/box_candidate/line_candidate/row_candidate/col_candidate; secondary=жёлтый для pincer.
- Конвертация подписей координат: вход 0-based → подписи r1..r9, c1..c9 при рендере.
- Отрисовка eliminations по полю `remove`; placement по `value`.

Deliverables:
- HTML шаблон с inline CSS, без внешних библиотек.
- Функции/утилиты форматирования данных для рендера (без вычислений судоку):
  - normalizeHowToApply (string|string[] → string[])
  - roleToAccent (string → primary|secondary)
  - zeroBasedToLabel (index:number → r/c label)

Verification:
- Верификация запускается скриптом `python3 scripts/verify.py` (не меняем). Добавить примеры входов для local тестирования.
- Тестовые сценарии:
  - placement, eliminations, both.
  - none.
  - error (ok:false, error:string) с/без предоставленного grid.
  - card.example присутствует: рендерится тем же компонентом.

Risks:
- Несогласованность ролей anchors → минимизируется фиксированным маппингом.
- Большой объём summary/how_to_apply → решается прокруткой панели.
