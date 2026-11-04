# Источники и журнал исследования

Проверено: 2026-11-04. Ниже — первичные источники, фактически открытые при подготовке.
Тезисы в PRD, архитектуре и ADR сверх этих фактов являются проектными решениями.
Документы не воспроизводят чужие статьи, код или иллюстрации.

| ID | Источник | Что проверялось |
|---|---|---|
| W01 | [WordOps repository](https://github.com/WordOps/WordOps) | CLI, заявленные upstream платформы и управляемые компоненты |
| W02 | [WordOps site commands](https://docs.wordops.net/commands/site/) | create/list/info/update и операции над сайтами |
| W03 | [WordOps installation](https://docs.wordops.net/getting-started/installation-guide/) | Способы установки и зависимость от окружения |
| W04 | [WordOps dashboard](https://github.com/WordOps/wordops-dashboard) | Описание штатного dashboard |
| W05 | [WordOps stack](https://docs.wordops.net/commands/stack/) | Общие компоненты и операции upgrade/migrate |
| C01 | [WordOps-Backup](https://github.com/mayur-chavhan/WordOps-Backup) | Full/incremental/DB, restore, CLI/menu, schedules |
| C02 | [wordops-auto-backup-websites](https://github.com/reklamverme/wordops-auto-backup-websites) | Скрипт файлов/БД в S3 и ручной список сайтов |
| C03 | [Reaver home](https://reaverbackup.com/) | Dashboard/agents/discovery/offsite и модель редакций |
| C04 | [Reaver new-server restore](https://reaverbackup.com/guides/restore-wordpress-to-new-server) | Какие компоненты целевого сервера остаются обязанностью оператора |
| C05 | [Backrest](https://github.com/garethgeorge/backrest) | Web orchestration Restic, repo operations, GPL-3.0 |
| C06 | [Duplicati home](https://duplicati.com/) | Backup platform и предложение централизованного управления |
| C07 | [Duplicati source](https://github.com/duplicati/duplicati) | Публичный проект; точные условия зависимостей проверяются при выборе версии |
| C08 | [Duplicati FTP](https://docs.duplicati.com/backup-destinations/standard-based-destinations/ftp-destination) | FTP backend, проверка upload и transport options |
| C09 | [Kopia features](https://kopia.io/docs/features/) | Encryption, GUI, checks, server/API |
| C10 | [borgmatic](https://torsion.org/borgmatic/) | DB backup, consistency, monitoring, конфигурационный подход |
| C11 | [MainWP 6.4 release](https://mainwp.com/mainwp-6-4-native-backups-ai-ready-extensions-and-tighter-security/) | Новая backup beta, опубликованная 2026-11-03 |
| C12 | [MainWP Child 6.4](https://voice.mainwp.com/changelog/mainwp-child-64) | Поддержка нового механизма Child plugin, дата 2026-11-02 |
| C13 | [ManageWP backup](https://managewp.com/features/backup/) | Managed offsite, schedules, restore, cloning |
| C14 | [Duplicator](https://duplicator.com/) | WordPress backup/migration product positioning |
| C15 | [RunCloud restore](https://runcloud.io/docs/restoring-runcloud-backups) | Current/other/new app+DB restore |
| C16 | [RunCloud create backups](https://runcloud.io/docs/creating-backups) | Storage/schedules; особенности внешнего хранения |
| C17 | [Ploi backup documentation](https://ploi.io/documentation/database/how-do-i-set-up-database-and-file-backups) | Destinations и ограничения panel restore |
| E01 | [Restic repositories](https://restic.readthedocs.io/en/stable/030_preparing_a_new_repo.html) | S3/rclone backends, encryption/repository access |
| E02 | [Restic checks](https://restic.readthedocs.io/en/stable/045_working_with_repos.html) | Structural check versus full/subset data reads |
| E03 | [Restic retention](https://restic.readthedocs.io/en/stable/060_forget.html) | forget/prune и append-only considerations |
| E04 | [rclone FTP](https://rclone.org/ftp/) | FTP/FTPS как transport, требующий capability testing |
| E05 | [age](https://github.com/FiloSottile/age) | Готовая encryption implementation для bundle-варианта |
| E06 | [AWS Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html) | WORM, версии объектов, retention и delete markers |
| V01 | [mariadb-dump](https://mariadb.com/docs/server/clients-and-utilities/backup-restore-and-import-clients/mariadb-dump) | Ограничения snapshot и совместимости dump/import |
| V02 | [WP-CLI core checksums](https://developer.wordpress.org/cli/commands/core/verify-checksums/) | Официальный механизм проверки ядра |
| V03 | [WP-CLI plugin checksums](https://developer.wordpress.org/cli/commands/plugin/verify-checksums/) | Официальный механизм проверки plugins |

## Поисковые запросы

- `"WOVault"`, GitHub repository search `wovault`.
- `WordOps backup restore web interface self hosted backup multiple servers`.
- `"WordOps" "backup" github`, GitHub repository search `wordops backup`.
- `"WordOps" "dashboard" github backup restore`, GitHub search `wordops dashboard`.
- `Reaver Backup WordOps restore self hosted` и уточнения по официальному домену.
- `site:mainwp.com "Built-In Backups" restore`.
- `site:runcloud.io backup restore server backup WordPress S3`.
- `site:ploi.io documentation backup restore server S3 FTP`.
- Уточнения по FTP в Duplicati, Restic/rclone, WordOps CLI и checksum WP-CLI.

Поиск также обнаружил archived `harsh8511/wordops-backup-sftp` и скрипты GDrive.
Они не оценивались как полноценные альтернативы UI-продукту. Сторонние обзоры,
Reddit и каталоги не использованы как подтверждение функций или безопасности.

## Достоверность и воспроизводимость

- Публичные страницы могут измениться: дата среза обязательна для сравнений.
- Точные release/commit и версии бинарников следует закрепить в G0 lab report.
- Нельзя переносить upstream support list WordOps в обещания WOVault без испытаний.
- MainWP в исследовании учтён по новому release note, а не старой knowledgebase.
- Reaver прочитан прямым HTTPS после ошибки web reader; страницы не требовали логина.
- Поиск не подтверждает отсутствие закрытых, малоизвестных или новых аналогов.
- Прайсы, market share и оценки SLA не использованы: они не проверялись отдельно.
- Недоступные страницы UpdraftPlus/WP Umbrella не включены в доказательную матрицу.
