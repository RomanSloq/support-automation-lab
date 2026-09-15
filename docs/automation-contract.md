# Automation contract

Rule engine получает структурированные факты тикета. Если факт неизвестен, он остаётся неизвестным: система его не придумывает.

Поля фактов: `affected_properties`, `issue_type`, `affected_bookings`, `other_bookings_working`, `overbooking_risk`, `error_code`, `problem_active`, `next_checkin_hours` и `claimed_urgency`. Поддерживаемые нормализованные типы: `availability_sync`, `reservation_sync` и `suspected_duplicate_booking`.

`claimed_urgency` — отдельное заявление клиента. Само по себе оно не определяет фактический priority.

В этом MVP `overbooking_risk=true` может означать риск, явно заявленный клиентом; это не доказательство независимой проверки внешней системой.

Текущие возможные результаты маршрутизации:

- `Incident`
- `L1`
- `L2`
- `Clarify`
- `Unmatched`

При нехватке ключевых фактов engine возвращает `Clarify` без priority. `Unmatched` означает, что факты валидны и достаточно полны, но ни одно реализованное правило не подошло; текущий default назначает `Normal` и не является общей проверенной бизнес-политикой.

Каждый результат также содержит `human_review_required`. Это safety gate-сигнал, а не approval workflow и не внешнее действие.
