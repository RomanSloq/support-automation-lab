# Локальный API

Проект предоставляет локальные endpoints для детерминированной и AI-assisted маршрутизации:

```text
POST http://127.0.0.1:8000/route
POST http://127.0.0.1:8000/ai/route
```

API принимает структурированные факты тикета в JSON и передаёт их существующему `rule_engine.py`. Сам API бизнес-решений не принимает. Решение возвращает rule engine, а API отдаёт его клиенту как JSON.

```text
Postman → POST /route → Python API → rule_engine.py → JSON response
```

Запуск из корня репозитория:

```powershell
python -m src.api
```

Локально через Postman успешно проверены reservation-кейс (`L1` / `Normal`) и массовый availability-кейс (`Incident` / `Critical`), оба с HTTP `200 OK`.

`POST /ai/route` принимает `{ "text": "..." }`, получает структурированные факты от OpenAI extractor и передаёт их в тот же rule engine. Его ответ отдельно содержит `facts`, `decision` и диагностические `usage`.
