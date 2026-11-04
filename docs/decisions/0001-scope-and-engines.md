# ADR 0001: WordOps recovery control plane и повторное использование движков

Дата: 2026-11-04 · Статус: предложено, требует G0 spikes.

## Контекст

Есть готовые web backup products. Исследование не обосновывает новый generic
backup engine. Требование проекта — подключать существующий WordOps fleet и
восстанавливать сайт с окружением на clean/existing VPS через проверенный план.
Кроме S3 требуется обычное FTP-хранилище, которое не обладает всеми свойствами S3.

## Решение

1. Создавать независимый control plane для inventory, policy, jobs, assurance и
   recovery WordOps. Не делать WordPress plugin центральным компонентом.
2. Размещать центр отдельно и использовать pull по SSH. На source нет ключей storage.
3. Предложить Restic subprocess adapter для S3. Не копировать UI/код Backrest.
4. FTP/FTPS поддержать через проверенный backend либо независимые encrypted bundles.
   До G0 это не окончательный engine choice. Путь по умолчанию для проектирования —
   full bundles + стандартная age implementation; собственного crypto нет.
5. Backup и restore principals разделить. Постоянный root-доступ не является условием
   регулярного backup; root/sudo допускается для bootstrap и approved restore.
6. Начать с single-organization deployment и ограниченной compatibility matrix.
7. Публиковать собственные исходники/документацию под MIT. Лицензии внешних binaries,
   библиотек, bundled components и их notices проверять на выбранных версиях.

## Альтернативы

- **Adopt Reaver.** Ближайший готовый продукт, но WordOps provisioning и открытая
  модель лицензирования для всего проекта не подтверждены. Нужен demo на G0.
- **Backrest fork.** Быстрый старт generic UI, но WordOps workflow всё равно
  собственный; есть upstream и GPL-3.0 obligations. Форк без проверки не выбран.
- **Duplicati reuse.** Сильный кандидат благодаря storage/UI; проверить API,
  recovery orchestration и dependency footprint до окончательного отказа.
- **Restic + rclone для всего.** Возможно, но наличие FTP transport не доказывает
  нужную семантику locking/commit/recovery. Проверить, не объявлять заранее надёжным.
- **Собственный dedup/crypto engine.** Отклонён: риск и стоимость не отвечают цели.

## Последствия

Собственный UI/jobs слой остаётся значительной разработкой. Два storage-пути
увеличивают число тестов; FTP full bundles требуют больше места/трафика. Зато
формат не должен зависеть от длинной инкрементальной цепочки на слабом backend.
S3 дедупликация и FTP standalone points имеют общий продуктовый recovery contract,
но не обещают одинаковую стоимость и скорость.

Система не заявляет immutable backups в P0 только потому, что доступ идёт pull.
Для защиты от компрометации самого центра нужна дополнительная независимая
protected copy. Публичный GitHub не содержит реальных credentials/данных.

## Условие пересмотра

Если G0 показывает, что готовый открытый продукт закрывает P0 расширением с меньшим
риском, выбрать интеграцию и обновить ADR/PRD. Если FTP bundle не проходит recovery
и corruption tests, не выпускать стабильный продукт с неподтверждённой FTP поддержкой.
