# P1-01 — Zero-shot ревью TRAINING_PR.diff

Источник запуска: opencode run --agent plan --model vsellm/openai/gpt-5 --format json --file TRAINING_PR.diff -- "Ниже diff учебного PR. Посмотри PR и найди проблемы."

Ниже — фактический ответ модели без скрытых рассуждений.

## Findings

- app/api.py:36-37 — Missing input validation leads to 500 on bad input. `create_review(payload: dict)` indexes `payload["diff"]` directly. If the client omits `diff` or sends a non-object body, this raises `KeyError` and returns a 500 instead of a 422. Use a Pydantic model with required `diff: str` or explicitly validate and raise `HTTPException(status_code=422, ...)`.
- app/api.py:35-38 — No error handling around the service call. Any exception from `review_service.review` or the underlying LLM will bubble up as 500 with no clear message. Wrap with try/except and map to appropriate HTTP errors (e.g., 502 for upstream issues, 400 for validation).
- app/api.py:35-38 — No response model declared. FastAPI will generate a vague OpenAPI schema. Define a response model (e.g., `ReviewResponse { comment: str }`) to lock down the contract and improve client generation and docs.
- app/api.py:28-38 — Lack of request/response schemas weakens validation and documentation. Typing the parameter as `dict` does not enforce structure; clients won’t get precise 422s for invalid shapes.
- app/api.py:28-38 — Security/auth not addressed. If this endpoint triggers LLM usage, consider at least basic auth or rate limiting to prevent abuse and cost exposure.
- app/review_service.py:19-22 — Prompt construction is naive and may be vulnerable to prompt-injection style content inside diffs. A malicious diff could steer the model output. Mitigate by delimiting the diff clearly, instructing the model to treat it as data, and constraining the required output format.
- app/review_service.py:19-22 — No safeguards or timeouts for the LLM call. If the LLM client can hang or be slow, consider adding timeouts/retries at the client or service layer.
- app/review_service.py:19-22 — The service returns a single `{"comment": ...}`. Depending on product needs, reviews often include multiple actionable comments. If multi-comment output is expected, the shape should be a list of comments with locations. If single summary is intended, this is fine; otherwise, it’s a mismatch to the endpoint name `/api/reviews`.
- app/api.py:35-38 — Synchronous endpoint calling a likely I/O-bound dependency. If the LLM client is I/O bound and supports async, prefer `async def` and `await` to avoid blocking threads. If the client is strictly sync, this is acceptable.
- app/review_service.py:10-13 — Use of `dict[str, str]` requires Python 3.9+. If the project supports older versions, this will break; use `Dict[str, str]` from `typing`. Same for return type in `api.py`.
- Minor style: The `Protocol` method stub change is fine. Consistency with the codebase’s formatter (e.g., Black) should be verified.

## Open questions

- What Python versions must we support? If <3.9, we need `typing.Dict`.
- Do we expect multiple comments per review, possibly with file/line anchors? If yes, the response schema and service logic should change accordingly.
- Is there an authentication or rate-limiting requirement for `/api/reviews`?
- What error semantics should clients see when the LLM is unavailable or times out?

## Suggested changes

1. Define request and response models:
   - `class CreateReviewRequest(BaseModel): diff: str`
   - `class ReviewResponse(BaseModel): comment: str`
   - Annotate the endpoint with these and let FastAPI validate.
2. Handle missing or invalid input and map service errors:
   - Use `HTTPException(status_code=422, ...)` for validation issues; catch LLM/client errors and return 502 with a sanitized message.
3. Harden prompt construction:
   - Wrap the diff in clear delimiters and instruct the model to treat it strictly as input data and to return only the expected JSON fields.
4. Consider async if the LLM client is async-capable; otherwise ensure your client has timeouts and retries.
5. If supporting older Python, replace `dict[str, str]` with `Dict[str, str]`.
