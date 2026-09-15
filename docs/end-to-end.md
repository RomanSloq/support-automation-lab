# End-to-end-проверка

## Автоматический локальный поток

Структурированные факты или внешнее событие `ticket.created` проходят через локальный API, затем через `rule_engine.py` и возвращают `route`, `priority` и `human_review_required`:

```text
факты/событие → API или webhook → rule_engine.py → решение
```

Проверены четыре сценария:

1. Локальная безопасная reservation-проблема → `L1` / `Normal` / `false`.
2. Массовая availability-проблема с риском overbooking → `Incident` / `Critical` / `false`.
3. Недостаточно фактов при claimed urgency → `Clarify` / без priority / `false`.
4. Подозрение на duplicate booking при заселении сейчас → `L2` / `High` / `true`.

Также проверены webhook `ticket.created` → вложенные факты ticket → rule engine → решение и `GET /manual-ai` с HTTP `200`.

## AI-assisted-потоки

Автоматический путь использует `POST /ai/route`: исходный текст → OpenAI Structured Outputs → факты → rule engine. Обычные тесты используют mock и не делают платных вызовов. Отдельно пользователь выполнил два реальных OpenAI-backed Postman-теста: массовый случай вернул `Incident` / `Critical`, а случай с одной бронью сохранил неизвестный `problem_active = null` и вернул `Clarify` / без priority. Оба ответа имели HTTP `200`.

Manual AI Test Harness остаётся отдельным ручным fallback: пользователь копирует prompt в ChatGPT, получает JSON фактов, вставляет его обратно, а страница отправляет факты в `/route`. В обоих путях AI извлекает факты, а rule engine выбирает решение.

Это локальный MVP verification seam. Реальной HelpDesk-интеграции, базы, авторизации, destructive actions и production deployment нет.
