# Webhook ticket.created

Локальный сервер предоставляет один webhook receiver:

```text
POST http://127.0.0.1:8000/webhook/ticket-created
```

Он принимает событие с `event = "ticket.created"` и вложенным объектом `ticket`. Webhook извлекает факты ticket и передаёт их существующему `rule_engine.py`. Собственных routing rules в webhook-коде нет.

Postman здесь имитирует внешнюю HelpDesk-систему. В реальной интеграции событие автоматически отправляла бы сама HelpDesk при создании тикета. Проект не утверждает, что такая реальная HelpDesk-интеграция уже подключена.
