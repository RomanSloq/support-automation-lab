# Dispatcher rules

На текущем milestone реализованы только эти правила:

1. Не менее 2 затронутых properties, `availability_sync` и риск overbooking → `Incident` / `Critical`.
2. Ровно 1 затронутая property, `reservation_sync`, 1 affected booking и остальные бронирования работают → `L1` / `Normal`.
3. Недостаточно ключевых фактов → `Clarify` / priority не назначается.
4. Активная `reservation_sync` с error code `401` → `L2` / `High`.
5. Активный `suspected_duplicate_booking` с затронутыми бронированиями и заселением сейчас → `L2` / `High` / human review required.

Два технических/safety-sensitive правила уровня L2 проверяются до fallback по недостающим фактам. Валидные факты, которые не подходят ни под одно правило, дают текущий default `Unmatched` / `Normal`; этот default не подтверждён как общая политика маршрутизации.

Для duplicate condition `affected_bookings` должен быть известен, но минимальное количество не задаётся. Подтверждён только тестовый сценарий с двумя бронированиями; изменение порога требует отдельного бизнес-решения.

Остальные сценарии поддержки запланированы, но пока не реализованы.
