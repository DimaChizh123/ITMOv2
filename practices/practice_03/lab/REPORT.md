# REPORT: локальная модель и результаты

## Оборудование и версии

- CPU: AMD Ryzen 5 7530U (12 логических ядер)
- RAM: 9.7 GiB, доступно ~3.9 GiB на момент запуска
- OS: WSL Linux
- Ollama: 0.34.4
- OpenCode: 1.18.35

## Модель и параметры

- Модель: qwen3.5:4b (Ollama)
- Квантизация: Q4_K_M
- Контекст по конфигу агента: 4096 токенов ([demo/opencode.json](./demo/opencode.json))
- Системный промпт для экспериментов: [system.txt](./system.txt)

Обоснование выбора: 4B-модель с Q4 квантизацией укладывается в ~3.4 GB VRAM/памяти и стабильно работает на ноутбуке с 10 GB RAM. Контекст 4k достаточен для чтения файлов demo/.

## Подготовка

- Проверен и отредактирован [Modelfile](./Modelfile): `FROM qwen3.5:4b`, `PARAMETER num_ctx 4096`, `PARAMETER temperature 0.2`, обновлён SYSTEM с указанием краткого формата ответа по данным репозитория.
- В [demo/opencode.json](./demo/opencode.json) настроен провайдер Ollama и агент `local-guide` с правами только на чтение (read/glob/grep).
- Тесты запускаются: `make test` в [lab/Makefile](./Makefile) проксирует в demo/ — все ок.
- Подготовлены эталоны: [results/gold.json](./results/gold.json).

## Запуски и сохранение ответов

Пять вопросов из [QUESTIONS.md](./QUESTIONS.md) заданы локальной модели через `opencode run --agent local-guide` из папки `lab/demo`. Ответы сохранены в [lab/results](./results/):

- Q1: [results/Q1.md](./results/Q1.md)
- Q2: [results/Q2.md](./results/Q2.md)
- Q3: [results/Q3.md](./results/Q3.md)
- Q4: [results/Q4.md](./results/Q4.md)
- Q5: [results/Q5.md](./results/Q5.md)

## Сравнение (кратко)

Сопоставление выполнено по сохранённым ответам и [results/gold.json](./results/gold.json). Подтверждения даны файлами-источниками в `demo/`.

Итог:
- Q1: ожидаемо — указана команда из Makefile
- Q2: ожидаемо — ValueError при пустом имени
- Q3: ожидаемо — unsubscribe отсутствует
- Q4: ожидаемо — сведений о CI нет
- Q5: ожидаемо — подписки не сохраняются (in-memory set)

## Ограничения и наблюдения

- Первичный запуск модели занимает больше времени из-за загрузки/инициализации; последующие сессии быстрее.
- В режиме `local-guide` у модели закрыт доступ к shell/записи; она опирается только на чтение файлов, что снижает риск галлюцинаций.
