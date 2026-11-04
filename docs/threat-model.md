# Модель угроз и границы доступа

Дата: 2026-11-04 · Статус: требования к проектированию, не отчёт об аудите.

## Защищаемые активы

Данные сайтов и клиентов; SSH/DB/storage secrets; возможность менять production;
история резервных точек; ключи расшифрования; доверенные baselines; доступность
соседних сайтов; достоверность аудита и уведомлений.

## Границы доверия

- Браузер оператора ↔ HTTPS API: любой запрос проверяется по RBAC и scope.
- API ↔ worker: API задаёт типизированное задание, не произвольную shell-команду.
- Центр ↔ VPS: host key pinning; источник может быть уже скомпрометирован.
- Backup principal ↔ restore principal: разные capabilities и credentials.
- Сайт ↔ root helper: недоверенный PHP/SQL не становится исполняемым root-кодом.
- Центр ↔ storage: storage может потерять/подменить данные; encryption не заменяет retention.
- Архив ↔ parser/lab: содержимое потенциально враждебно; сеть и mounts ограничены.

## Матрица рисков

| Угроза | Меры первого выпуска | Остаточный риск |
|---|---|---|
| Кража ключа backup | Forced command, site allowlist, запрет записи/restore, revocation | Чтение данных всех разрешённых сайтов |
| Компрометация UI account | MFA, RBAC, reauth, короткие сессии, отдельные restore approvals | Разрешённые роли могут злоупотребить полномочиями |
| Компрометация worker/control host | Разделение сервисов, secret scopes, отдельные keys, audit export | Работающий worker видит нужные ему secrets; возможен массовый ущерб |
| Захваченный production | Pull, отсутствие storage credentials на VPS, внешние baselines | Источник может отдавать ложные данные и скрывать следы |
| SSH MITM | Проверка fingerprint до credentials, pinning, block on change | Нужен доверенный канал первоначальной проверки |
| Shell/path injection | Типизированный protocol, fixed argv, canonical paths, root-owned config | Parser/helper требует fuzzing и review |
| Архивный traversal/symlink/device | Validate до распаковки, safe extraction, лимиты, отдельная VM | Уязвимость decompressor/runtime остаётся возможной |
| Вредоносный SQL/config | Least-privilege DB import, no PHP eval/root execution, runtime sandbox | Восстановленный сайт всё ещё может содержать malware |
| Удаление/шифрование новых файлов | Версионные snapshots, pins, аномалии, отдельная retention очередь | Уже испорченный источник даст испорченную новую копию |
| Удаление старых копий | На проде нет ключей storage; отдельные prune права | Администратор центра/storage может удалить доступные копии; protected copy — P1 |
| Повреждение storage | Authenticated manifests, engine checks, readback, restore tests | Проверки требуют времени, места и egress |
| Потеря master key | Offline recovery kit, проверка процедуры импорта | Без резервного ключа decrypt невозможен |
| Подмена target перед restore | Plan hash, inventory/fingerprint binding, revalidation | После проверки возможна внешняя гонка; site lock + повторные preconditions |
| Ошибка выбора сайта | UUID, domain confirmation, plan diff, checkpoint | Человек может подтвердить неверный план |
| Повреждение соседних сайтов | Site-scoped actions, запрет stack upgrades, integration assertions | Общие сервисы всё равно создают общую область отказа |
| SSRF / metadata theft | Registered targets, CIDR allowlist, redirect policy, isolated scanner egress | Разрешённая приватная сеть остаётся доступной в пределах policy |
| Утечка отчётов/логов | Redaction, safe metadata, download permissions, retention | Backup содержит персональные данные и требует отдельной защиты |
| Остановка scheduler/уведомлений | Внешний heartbeat, freshness checks, visible delivery errors | Потеря одновременно центра и monitor требует внешнего реагирования |

## Правила привилегий

Bootstrap/root credential допустим для инвентаризации и подтверждённой подготовки.
По умолчанию он хранится только на время задания. Root password не включается в
queue payload, argv, export или browser response. При необходимости постоянного
administrative credential нужен явный выбор администратора, encryption и TTL.

Backup helper даёт чтение файлов/DB export/разрешённый inventory. Он не позволяет
пользователю редактировать allowlist, выбирать произвольный путь или подменять
исполняемые файлы. Установка root-owned помощника включает проверку всех parent
directories, config owners и symlinks; sudo validation проводится до изменения правил.

Restore helper имеет отдельную команду и capability. План из UI не считается
достаточной защитой сам по себе: серверная сторона проверяет допустимые операции,
целевой сайт, срок и соответствие текущему состоянию. Подпись/nonce защищают от replay
в пределах заданного протокола; локальный root целевой VPS всё равно выше этой границы.

Недопустимы общие grants на `bash`, `python`, `rsync`, `tar` или unrestricted `wp`.
Недопустимо запускать `wp-config.php`/MU/plugins под root для получения DB password.
Нельзя использовать общий `www-data` как обещание изоляции независимых клиентов.

## Политика подозрительных копий

Подозрительная точка сохраняется с evidence и incident pin. Доверенные предыдущие
точки не удаляются автоматически из-за новой подозрительной. «Acknowledge finding»
не делает архив чистым; baseline approval — отдельное разрешение.

Production restore подозрительной точки заблокирован по умолчанию. Допустим
администраторский override с причиной после просмотра evidence, но integrity failures
не обходятся такой кнопкой: повреждённые данные допускаются только в отдельный
forensic/export workflow без обещания успешного восстановления.

Проверки checksum обнаруживают изменения, а не все способы вторжения. Новая
уязвимость может не менять файлы; вредоносная запись может находиться в БД;
root-компрометация может подделывать любые ответы VPS. Для серьёзного инцидента
предпочтительны изоляция хоста, сохранение evidence и восстановление доверенного
окружения с ротацией credentials, а не «зелёный результат сканера».

## Требования к тестированию

Использовать только синтетические fixtures и разрешённые lab VPS. Проверить
traversal, symlinks, special files, большие архивы, shell metacharacters, replay,
cross-site paths, host key mismatch, secret canaries и scope обходы. Измерить,
что backup principal не может изменить сайт, restore metadata или чужие файлы.

Перед первым стабильным выпуском нужен отдельный review SSH/sudo helper,
credential handling, bundle parser и restore state machine. Реальный malware
не загружается в публичный репозиторий; для детекторов используются безопасные
синтетические индикаторы и тестовые сигнатуры.
