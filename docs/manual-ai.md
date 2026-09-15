# Manual AI Test Harness

Manual AI Test Harness — ручной fallback и учебный инструмент для проверки границы между AI extraction/normalization и детерминированной маршрутизацией.

```text
текст клиента → скопированный prompt → ручной ChatGPT → JSON фактов → POST /route → rule_engine.py → решение
```

ChatGPT вручную извлекает и нормализует явно выраженный смысл в automation contract. Страница требует использовать `null` для неизвестных фактов и не выбирать `route` или `priority`. Бизнес-решение принимает детерминированный `rule_engine.py`.

Ручной copy/paste нужен как учебный integration seam, когда автоматический OpenAI-путь не используется. Сам harness не вызывает OpenAI API и не расходует кредиты; после вставки фактов он обращается только к локальному `/route`.

Во время проверки сообщение `Одна бронь Booking не появилась в PMS.` выявило defect extraction: `problem_active` ошибочно стал `true`, хотя сообщение не говорило, что проблема продолжается. Prompt был усилен: `true` — только при явном текущем состоянии, `false` — только при явном устранении, иначе `null`. Исправленные факты дают `Clarify` без priority.
