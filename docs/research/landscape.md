# Исследование аналогов и решение о продукте

Дата среза: **2026-11-04**. Исследование проведено до подготовки PRD и до реализации.
Цель: проверить, существует ли уже открытый внешний центр для WordOps с backup,
контролем копий и восстановлением стека на чистую или действующую VPS.

## Вывод

Похожие продукты существуют. Особенно близок Reaver Backup: внешний dashboard,
обнаружение сайтов, серверные агенты, snapshots и restore. Создавать ещё один
универсальный backup UI без специализации на WordOps нецелесообразно.

В просмотренных первичных источниках не найдено подтверждения **всего сочетания**:
публичный open-source проект + импорт существующего парка WordOps + pull-доступ +
FTP/S3 + inventory/plan + подготовка чистой VPS + безопасная замена сайта на занятой
VPS + доказуемые проверки восстановления. Это результат ограниченного поиска,
а не доказательство отсутствия любого такого продукта на рынке.

Рекомендация: разрабатывать WordOps recovery orchestration поверх существующих
backup engines. Ценность — адаптер WordOps, согласованность, target planning и
безопасный cutover. Дедупликацию, криптографию и универсальное хранение заново не писать.

## Метод

Просмотрены официальные README, документация CLI, restore guides и changelog.
Для Reaver официальные страницы прочитаны прямым HTTPS-запросом: web-инструмент
их не открывал, но сайт отдавал HTTP 200. Reddit/каталоги использовались только
для обнаружения названия, не как основание технических выводов.

Отдельно выполнены GitHub repository searches: `wovault`, `wordops backup`,
`wordops dashboard`. Поиск названия WOVault не вернул репозиториев на момент проверки;
доступность домена, имени организации, пакетов и товарного знака не проверялась.
GitHub-поиск не является полным поиском по всем файлам и закрытым продуктам.

«Не подтверждено» ниже означает отсутствие соответствующего описания в просмотренных
источниках. Это не равнозначно «продукт не умеет»; требуются demo или отдельный тест.
Продукты не устанавливались, производительность и безопасность не сертифицировались.

## Сравнение

| Решение | Подтверждённые возможности | Пробел относительно WOVault | Вывод |
|---|---|---|---|
| [WordOps + dashboard](https://github.com/WordOps/wordops-dashboard) | WordOps CLI управляет сайтами/стеком; dashboard — backend tools/status | Внешний каталог recovery points и мастер disaster recovery в просмотренном описании не подтверждены | Использовать WordOps как управляемую платформу |
| [WordOps-Backup](https://github.com/mayur-chavhan/WordOps-Backup) | Full/DB/incremental, restore, cron, retention, notifications, CLI/menu | Не подтверждены внешний web control plane и подготовка чистой VPS | Изучить требования к WordOps backup/restore, не считать отсутствующим restore |
| [wordops-auto-backup-websites](https://github.com/reklamverme/wordops-auto-backup-websites) | Python script для файлов и MySQL с отправкой в S3 | Настройки сайтов вручную; внешний inventory/restore UI не описан | Показывает наличие задачи, не заменяет центр |
| [Reaver Backup](https://reaverbackup.com/) | Self-hosted dashboard, discovery, agents, расписания, incremental, offsite S3/B2/SSH, restore | Официальный new-server guide требует подготовленный web/DB stack; полная открытая лицензия и WordOps provisioning не подтверждены | Самый близкий прямой аналог; обязательное сравнение на gate G0 |
| [Backrest](https://github.com/garethgeorge/backrest) | Open-source web UI для Restic, repository operations, schedules, browse/restore | Нет подтверждённого готового WordOps inventory/bootstrap/cutover workflow | Сильная альтернатива для ручного ops; кандидат интеграции |
| [Duplicati](https://duplicati.com/) | Backup UI, encryption, расписания; FTP и S3 backends, есть central management предложение | WordOps-aware DB/file consistency и восстановление стека не подтверждены | Реальный конкурент generic backup; проверить reuse до собственного FTP engine |
| [Kopia](https://kopia.io/docs/features/) | Encryption, dedup, policies, GUI, validity checks, optional server/API | Нет подтверждённого WordOps restore planner | Альтернативный engine, не полный готовый продукт под задачу |
| [borgmatic](https://torsion.org/borgmatic/) | Config-driven Borg orchestration, DB hooks, checks, retention, monitoring | Базовый интерфейс CLI/config; WordOps inventory/target installer не описан | Полезен как образец backup policy и DB handling |
| [MainWP 6.4](https://mainwp.com/mainwp-6-4-native-backups-ai-ready-extensions-and-tighter-security/) | Новые встроенные backups beta: full/DB/files/incremental, storage, restore, health | Нужен MainWP Child на WordPress; WordOps bootstrap bare VPS не подтверждён | Сильный WordPress-конкурент; старое описание «только extensions» устарело |
| [ManageWP](https://managewp.com/features/backup/) | SaaS dashboard, offsite incremental, schedules, restore, cloning | Self-hosted WordOps control plane и подготовка ОС не подтверждены | Альтернатива тем, кому важнее готовый сервис |
| [Duplicator](https://duplicator.com/) | WordPress backup/migration packages и installer workflows | Установка серверного WordOps stack и registry парка не подтверждены | Учитывать переносимость и аварийный standalone installer |
| [RunCloud](https://runcloud.io/docs/restoring-runcloud-backups) | Backup UI; restore в текущий, другой или новый app/database; внешние storage | Собственная платформа; импорт существующего WordOps без смены управления не подтверждён | Близкий UX-референс, другой операционный контракт |
| [Ploi](https://ploi.io/documentation/database/how-do-i-set-up-database-and-file-backups) | Files/DB schedules, S3/FTP/SFTP и другие destinations, central UI | Есть ограничения panel restore для FTP/SFTP и файлов; WordOps import не подтверждён | Не считать наличие FTP backup доказательством полноценного web restore |

## Существенные наблюдения

### Reaver: ближе всего, но не готовая замена WordOps recovery

Официальная страница описывает внешний dashboard, отдельные серверные агенты и
управляемое пользователем хранилище. Это уже реализует большую часть идеи «центр
бэкапов вне WordPress». Продукт предлагается в бесплатной ограниченной и платных
редакциях; наличие self-hosted режима само по себе не означает open-source.
Не фиксируем цены: они не нужны для продуктового решения. [Источник](https://reaverbackup.com/).

Guide восстановления на новый сервер прямо оставляет установку веб-сервера,
БД, vhost, сертификатов и DNS оператору. Именно эту границу должен закрыть
WordOps adapter WOVault, сохранив осознанный контроль над DNS. Заявление о таком
различии основано на документации, а не на пробной установке.
[New-server guide](https://reaverbackup.com/guides/restore-wordpress-to-new-server).

### MainWP: учитывать обновление ноября 2026

В релизе Dashboard 6.4, описанном 3 ноября, встроенные backups имеют beta-статус
и работают вместе с Child 6.4. Поэтому исследование не опирается на прежний тезис,
что MainWP умеет только интеграции backup-плагинов. У нового варианта остаётся
другой уровень управления: WordPress sites, а не provisioning WordOps VPS.
[Release note](https://mainwp.com/mainwp-6-4-native-backups-ai-ready-extensions-and-tighter-security/).

### Панели серверов: хороший UX, иной способ владения стеком

RunCloud документирует восстановление в существующий или новый app/database.
Но это не подтверждает возможность безопасно подключить уже работающий WordOps.
Ploi отдельно сообщает, что file restore из панели недоступен, а DB restore имеет
ограничения для FTP/SFTP. Эти различия требуют проверки по каждому сценарию.
[RunCloud](https://runcloud.io/docs/restoring-runcloud-backups),
[Ploi](https://ploi.io/documentation/database/how-do-i-set-up-database-and-file-backups).

### Проверка архива — отдельна от проверки сайта

Restic разделяет структурную проверку и чтение содержимого пакетов. Даже успешная
проверка файлов не доказывает совместимость SQL dump/runtime, согласованность uploads
с БД или отсутствие вредоносного кода. В PRD эти состояния независимы.
[Restic check](https://restic.readthedocs.io/en/stable/045_working_with_repos.html).

## Build / integrate / adopt

| Вариант | Преимущество | Цена и условие |
|---|---|---|
| Adopt Reaver | Короткий путь к готовому backup UI и fleet registry | Нужно проверить лицензию, условия, WordOps покрытие и дополнить provisioning |
| Backrest + ops scripts | Готовая зрелая orchestration Restic | Inventory/restore UX остаются собственной разработкой; fork несёт GPL и upstream maintenance |
| Duplicati + WordOps adapter | Уже есть FTP/S3 и UI | Нужно проверить документированный API, jobs/recovery contract и пригодность embedding |
| Собственный control plane + Restic | Полный контроль над WordOps recovery и privilege model | Нужно строить UI/jobs/adapters и отдельно решить FTP; рекомендуемый путь при прохождении spikes |
| Собственный backup/crypto engine | Нет зависимости от движка | Не оправдано для этого проекта; отклонено |

Продуктовая рекомендация — самостоятельный WordOps control plane, но **не немедленное
написание всего приложения**. На G0 проверяется, можно ли закрыть требования расширением
Backrest/Duplicati или интеграцией с ближайшим аналогом. Если готовое решение закрывает
P0 без платной зависимости и опасного форка, план меняется в пользу интеграции.

## Что нужно проверить экспериментально до разработки

1. Какие версии WordOps реально можно надёжно инвентаризировать через CLI/конфиги.
2. Восстановление одного сайта без изменения соседей на занятом WordOps сервере.
3. Управление окнами записи: web, WP-Cron, очереди, импорты и внешние writers.
4. Restic S3 и FTP через rclone: locking, частичная передача, readback, quota,
   последствия сбоев. Наличие backend не заменяет испытаний безопасной семантики.
5. Standalone encrypted bundles для FTP как запасной путь; цена хранения и RTO.
6. Reaver/Backrest/Duplicati: demo по сценариям S1–S6, актуальные license/API условия.
7. Восстановление каталога из storage без исходного control DB и без исходной VPS.

Ограничения исследования: отсутствуют hands-on trials, vendor interviews,
performance tests, юридическая проверка имени и количественная оценка спроса.
Это не мешает специфицировать продукт, но не позволяет объявить его уникальным
или автоматически рекомендовать немедленную полную разработку.
