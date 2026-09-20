# P1-02 — Ревью TRAINING_PR.diff с Master Prompt v1 (RU)

Источник запуска: opencode run --agent plan --model vsellm/openai/gpt-5 --format json --file TRAINING_PR.diff --file prompts.md -- "Используй 'Master Prompt v1' из prompts.md и TRAINING_PR.diff. Ответ дай по-русски. Верни вывод строго в формате: Summary; затем до трёх Risks с file:line или file:start-end и доказательством; затем Checks (нумерованный список). Ничего лишнего."

Ниже — фактический ответ модели без скрытых рассуждений.

## Summary
Добавлен метод ReviewService.review, формирующий prompt из переданного diff и вызывающий LLM; в FastAPI добавлен POST эндпоинт /api/reviews, проксирующий вызов review_service.review. Изменён стиль объявления LLM.generate (многострочный). Явных схем запросов/ответов и обработки ошибок нет.

## Risks
1. app/api.py:35-38 — отсутствует модель/валидация входа и прямой доступ к payload["diff"]. Доказательство: сигнатура функции `def create_review(payload: dict) -> dict[str, str]:` и строка `return review_service.review(payload["diff"])`. При отсутствии ключа "diff" будет KeyError и 500; типы не проверяются.
2. app/review_service.py:21-22 — нет обработки ошибок при вызове LLM. Доказательство: `answer = self.llm.generate(prompt)` без try/except; исключения LLM будут падать до API и возвращать 500.
3. app/api.py:35-38 — отсутствует явный response_model и схема запроса. Доказательство: декоратор `@app.post("/api/reviews")` без параметров схемы и сигнатура с `payload: dict`. Это приведёт к «object» в OpenAPI без полей и осложнит генерацию клиентов/валидацию.

## Checks
1. Отсутствие ключа diff: запустить сервер, выполнить `curl -X POST http://localhost:8000/api/reviews -H "Content-Type: application/json" -d '{}'`. Ожидаемо: 500 Internal Server Error (KeyError: 'diff').
2. Исключение из LLM: в тесте/рантайме подменить `review_service.llm.generate` на функцию, выбрасывающую Exception; вызвать POST /api/reviews с любым diff. Ожидаемо: 500, стек укажет на `self.llm.generate`.
3. Схемы в OpenAPI: открыть http://localhost:8000/docs и проверить, что для POST /api/reviews тело запроса отображается как «object» без описанных полей, а схема ответа не определена как модель.
