# План реализации и приёмки

Дата: 2026-11-04 · Статус: backlog и gates, не календарное обязательство.
P0 означает первый стабильный выпуск; промежуточные alpha не закрывают весь PRD.
Команда, бюджет и измеренный throughput неизвестны, поэтому сроки не выдумываются.

## G0 — Проверка решения и технические spikes

| Работа | Результат | Условие перехода |
|---|---|---|
| Demo Reaver/Backrest/Duplicati | Сценарии S1–S6, подтверждённые license/API limitations | Есть аргумент, почему интеграция не закрывает P0 проще |
| WordOps lab | Закреплённые OS/release/CLI outputs и capability profiles | Inventory без PHP eval и полный create/restore на тестовой VPS |
| Existing-server restore | Staging/cutover/checkpoint, два соседних сайта | Replace не изменяет соседей; failed replace восстанавливает исходный сайт |
| DB/file consistency | Writers map, online и quiesced profiles | Проверен freeze/release при отказе; неизвестный writer блокирует strict |
| Storage comparison | Restic S3; rclone FTP; independent bundles; Duplicati reuse | Проверенные failure semantics, recovery без control DB, измеренная стоимость |
| Key recovery | Offline kit, reimport, ротация | Старые и новые точки читаются на новом центре |
| Security review sketch | Helper protocol и privilege diagram | Backup key не даёт write/restore; нет root выполнения сайта |

G0 может закончиться решением интегрировать готовый продукт. Если Restic через FTP
не проходит тесты, это не повод объявить FTP невозможным: выбрать и проверить
bundle adapter либо другой engine. Если оба пути не проходят, пересмотреть scope
до реализации и явно зафиксировать незакрытое пользовательское требование.

## G1 — Control plane и read-only onboarding

- Public repo, dependency/license policy, CI, threat model, supported matrix.
- Auth/MFA/RBAC, server/site/storage registry, versioned inventory, host key pinning.
- Read-only SSH protocol, bootstrap plan, restricted helper enrollment/revoke.
- PostgreSQL durable jobs, leases/retries, аудит, redaction, scheduler heartbeat.

Gate: demo inventory на двух серверах с несколькими сайтами; нет изменений до
approval; сбой/смена host key безопасно блокируются; secret canaries не утекли.

## G2 — S3 backup alpha

- Полный capture, DB-only/files-only, online consistency и coverage report.
- Restic adapter, manifest/commit reconciliation, каталог и import existing repo.
- Расписание/timezone/retention/pins, progress, уведомления и freshness monitoring.
- Structural/full/subset checks и восстановление файлов/DB в изолированную lab.

Gate: прерванные задания не создают complete points; storage и control DB recovery
работают. Alpha маркируется S3-only и не предлагается как законченный P0.

## G3 — Recovery beta и FTP

- Проверенный FTP/FTPS adapter с readback, partial transfer resume и recovery catalog.
- Clean VPS provisioning и restore; existing WordOps create/clone/replace.
- Plan hash/approval/revalidation, safety checkpoint, rollback/reconciliation.
- URL/secrets policy, isolated previews, WordOps metadata consistency, TLS/DNS states.
- Quiesced profile для подтверждённых writer combinations.

Gate: все AC по clean/existing targets и FTP/S3; failure injection каждого шага;
rollback без ущерба соседям. Проверяется поддержка старых точек после upgrade.

## G4 — Assurance и первый стабильный выпуск

- Checksum/baseline/static/DB findings; quarantine, pins, investigation states.
- Плановые isolated restore drills, HTTP assertions, blocked egress.
- Benchmark profile и опубликованные RPO/RTO measurements с условиями.
- Внешний security review критичных helpers/parsers и release/recovery runbooks.
- RU/EN UI, accessibility, admin guide и disaster recovery центра.

Gate: выполнены все P0 и обязательные acceptance scenarios ниже. Ни одно
`not_checked/unsupported` не отображается как passed. Ограничения описаны до релиза.

## G5 — После стабильного выпуска

P1: дополнительное protected storage, проверенный Object Lock profile, system-level
sensors, YARA/ClamAV/feeds, другие ОС/architectures, дополнительные WordOps versions,
remote DB/media adapters. OIDC, агентские scopes и последующие операции обслуживания
обсуждаются отдельно. Массовые обновления production не добавляются неявно в backup scope.

## Обязательные acceptance scenarios

Каждый сценарий имеет машинный отчёт, входной fixture, ожидаемый результат,
логи без секретов и ссылки на requirement IDs. Используются только lab VPS.

| ID | Сценарий | Ожидаемый результат | Требования |
|---|---|---|---|
| AC-01 | Connect by root password; separately SSH key+passphrase and sudo-login | Host key verified; inventory before writes; secret not persisted by default | REG-01/02/05, RST-01 |
| AC-02 | Неверный пароль, root SSH disabled, host key mismatch | Понятная ошибка; SSH policy не ослаблена; ни одной мутации | REG-04, RST-01, NFR-02 |
| AC-03 | Обнаружены WO registry/vhost расхождения и dynamic config | Coverage gap/blocker; PHP сайта не исполняется | REG-02/03 |
| AC-04 | Один backup account, три разрешённых сайта и четвёртый запрещённый | Первые копируются; четвёртый/чужой путь/restore/shell недоступны | REG-05, BKP-04, NFR-02 |
| AC-05 | Full backup; все исходные plugin download/GitHub endpoints затем недоступны | Копия восстанавливается по сохранённым файлам | BKP-03, RST-05 |
| AC-06 | DB-only/files-only snapshot | Нет обещания full restore; advanced restore требует отдельного плана | BKP-01/07, RST-07 |
| AC-07 | SSH/network interruption и crash между upload/commit/DB registration | Нет ложного complete; retry/reconcile без дубликата | BKP-02/07, NFR-03 |
| AC-08 | ENOSPC/inodes/quota и storage timeout | Остановка без порчи старых точек, видимая причина и уведомление | BKP-06, STO-01/02, UI-02 |
| AC-09 | Изменения БД/uploads/DDL/нетранзакционные таблицы во время online backup | Честный consistency status, строгая гарантия не заявлена | BKP-05 |
| AC-10 | Quiesced web+cron+queue+external writer; затем ошибка cleanup | Окно подтверждено; исходные состояния восстановлены либо needs_operator + alert | BKP-05/06 |
| AC-11 | FTP сервер не поддерживает rename или даёт задержанный list | Нет ложного commit; фактический readback и безопасный retry | STO-02/03, BKP-07 |
| AC-12 | FTP part/manifest подменён или укорочен | Integrity failed; production restore блокирован | STO-03/04, VER-01/02 |
| AC-13 | Retention после серии backup failures; pinned incident snapshot | Последняя полная и pinned points сохранены; dependencies учтены | BKP-08 |
| AC-14 | DST shift, missed runs, два workers с одним idempotency key | Предсказуемый next-run/catch-up, один committed point | BKP-02, NFR-03 |
| AC-15 | Исходная VPS уничтожена, новый совместимый clean target | Approved WO bootstrap; full restore без источника | S3, RST-02/04/05 |
| AC-16 | Target без WO, но с другой панелью/занятыми сервисами | Conflicting stack и blocker; ничего не удаляется | RST-02/04 |
| AC-17 | Target WO с двумя существующими сайтами; create третьего | Новый сайт работает; hashes/config/DB соседей прежние | RST-04/05 |
| AC-18 | Replace одного сайта; fail на dump, prepare, DB import, config validation, cutover | Checkpoint обязателен; rollback/needs_operator; соседи целы | RST-06/10 |
| AC-19 | Цель/домен/inventory изменились после approval | План устарел; apply заблокирован до нового подтверждения | RST-03 |
| AC-20 | Несовместимые PHP extensions/DB collation/dump client/WordOps | Нет тихого upgrade общего стека; blocker и объяснение | REG-02, RST-02/04 |
| AC-21 | Clone на другой домен с serialized values и SMTP/payment/1С | URLs корректны; тестовые integrations отключены, egress заблокирован | RST-08/09, VER-03 |
| AC-22 | HTTP 200 содержит fatal/error/login вместо нужной страницы | Smoke test failed; cutover не считается успешно проверенным | RST-09 |
| AC-23 | DNS не указывает на цель; ACME HTTP недоступен | Preview работает по override; публичный TLS не объявлен готовым | RST-09 |
| AC-24 | Worker/reboot потерян после каждого изменяющего шага restore | Durable reconciliation, нет слепого повторного cutover | RST-10, NFR-03 |
| AC-25 | WooCommerce принял новые заказы после snapshot | До replace явно показана потеря поздних данных; auto-merge не обещан | RST-07 |
| AC-26 | Test restore со scheduler, SMTP, webhooks, payments | Ни один запрос не ушёл наружу, prod не затронут | VER-03, RST-08 |
| AC-27 | Extra PHP in uploads, изменённый MU, новый admin, baseline drift | Findings с scope/evidence/confidence; no auto-clean | SEC-01/02/03 |
| AC-28 | Plugin без official checksums, недоступный feed или scanner timeout | Unsupported/not_checked; нет зелёного security pass | VER-01, SEC-01 |
| AC-29 | Подозрительная точка; затем попытка production restore | Изоляция по умолчанию; override только admin с причиной | RST-11, SEC-03 |
| AC-30 | Traversal/symlink/bomb/опасный SQL в архиве | Нет записи вне scope и root execution; job безопасно прекращён | NFR-02, RST-11 |
| AC-31 | Потеря control DB/центра; есть storage+offline key kit | Каталог заново построен; restore возможен; планы выключены | S6, STO-04/05 |
| AC-32 | Key rotation и upgrade WOVault | Старые точки доступны, старые approvals недействительны | STO-05, NFR-04 |
| AC-33 | Утечка/неверный scope через API/download/argv/log/notification | Canary secrets не видны; viewer не скачивает дамп | Раздел 3, NFR-02/03, UI-02 |
| AC-34 | Scheduler остановлен, notification channel недоступен | Внешний heartbeat/monitor сообщает stale; delivery failure виден | UI-02, NFR-03 |
| AC-35 | Cancel до/после cutover; сайт уже принял новые записи | Только допустимая отмена; rollback после записей требует нового плана | RST-10 |

## Как сравнивать готовые продукты на G0

Сначала проверить AC-01/03/15/17/18/31 — основной differentiator. Затем storage,
security scopes и лицензирование. Для каждого результата хранить tested version,
environment, steps, actual outcome и verdict. Vendor claim без теста — documented,
не tested. Если возможность не проверена, ставить unknown вместо fail.

## Показатели для пилота

В пилоте измерять долю сайтов с полной свежей точкой, возраст последнего успешного
restore drill, backup window, pause time, восстановление до serving и public cutover,
storage/egress cost, число false-positive findings и время реакции. RPO задаёт владелец
сайта, а расписание проверяется на возможность его соблюдения с учётом очереди/сбоев.
Начальная retention-политика 14 daily / 8 weekly / 12 monthly — редактируемый preset,
а не обязательство, подходящее всем магазинам и клиентам.
