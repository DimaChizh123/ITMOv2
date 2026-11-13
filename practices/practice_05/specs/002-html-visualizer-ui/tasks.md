# Tasks: HTML Visualizer UI (002)

Status: Draft

1. Define Data Interfaces (Spec-only)
   - Описать ожидаемый формат `result.visual` и `result.card` (0-based координаты, value/remove, anchors.roles). [Done in spec.md]

2. Layout Spec (Spec-only)
   - Уточнить HTML/CSS Grid макет: 9×9 поле, координатные подписи, толстые границы 3×3, мини-сетка кандидатов. [Done in spec.md]

3. Anchor Roles Mapping
   - Зафиксировать маппинг ролей → цветов (primary/secondary). [Done in spec.md]

4. Screen States
   - Описать поведение: success (placement/elimination), none, error (ok:false). [Done in spec.md]

5. Component Reuse Requirement
   - Добавить требование: единый компонент рендера 9×9 используется для `card.example` в боковой панели. [Done in spec.md]

6. Input Validation Rules
   - Зафиксировать строгие проверки размеров и диапазонов; 0-based индексация. [Done in spec.md]

7. Accessibility Notes
   - Контрасты, рамки, aria/title. [Done in spec.md]

8. Implementation Prep (Next phase)
   - Подготовить план рендера без кода: функции нормализации и маппинга (normalizeHowToApply, roleToAccent, zeroBasedToLabel).

9. Test Cases Prep (Next phase)
   - Составить набор JSON-фикстур для сценариев: placement, eliminations, both, none, error, card.example.
