---
title: "MOC: Архитектура"
type: "moc"
audiences: ["architect", "backend_dev", "frontend_dev"]
tags: ["doc", "lab-equipment-system", "moc", "architecture"]
status: "approved"
last_updated: "2024-12-19"
---

# MOC: Архитектура

## Общая архитектура

- [[docs/architecture/index]] - Архитектура системы
- [[docs/architecture/patterns]] - Архитектурные паттерны
- [[docs/architecture/principles]] - Принципы проектирования

## Слои архитектуры

### UI Layer
- [[docs/modules/ui/main-window]] - Главное окно
- [[docs/modules/ui/pages]] - Страницы приложения
- [[docs/modules/ui/widgets]] - Виджеты
- [[docs/modules/ui/components]] - Компоненты

### Core Layer
- [[docs/modules/core/di-container]] - Dependency Injection контейнер
- [[docs/modules/core/serial-manager]] - Serial Manager
- [[docs/modules/core/sequence-manager]] - Sequence Manager
- [[docs/modules/core/command-executor]] - Command Executor
- [[docs/modules/core/interfaces]] - Интерфейсы

### Monitoring Layer
- [[docs/modules/monitoring/manager]] - Monitoring Manager
- [[docs/modules/monitoring/health]] - Health Checker
- [[docs/modules/monitoring/performance]] - Performance Monitor
- [[docs/modules/monitoring/errors]] - Error Alerter

### Configuration Layer
- [[docs/modules/config/loader]] - Config Loader
- [[docs/modules/config/settings]] - Settings Manager

### Utilities Layer
- [[docs/modules/utils/logger]] - Logger
- [[docs/modules/utils/error-handler]] - Error Handler
- [[docs/modules/utils/git-manager]] - Git Manager

## Диаграммы

- [[docs/diagrams/container]] - Контейнерная диаграмма
- [[docs/diagrams/component]] - Компонентная диаграмма
- [[docs/diagrams/sequence]] - Диаграммы последовательностей
- [[docs/diagrams/state]] - Диаграммы состояний

## Нефункциональные требования

- [[docs/architecture/performance]] - Производительность
- [[docs/architecture/reliability]] - Надежность
- [[docs/architecture/security]] - Безопасность
- [[docs/architecture/scalability]] - Масштабируемость

## Решения

- [[docs/adr/001-dependency-injection]] - Использование DI
- [[docs/adr/002-command-pattern]] - Command Pattern
- [[docs/adr/003-observer-pattern]] - Observer Pattern
- [[docs/adr/004-solid-principles]] - SOLID принципы

## Автоиндекс (Dataview)

```dataview
TABLE file.link AS "Документ", type, last_updated
FROM "docs/architecture" OR "docs/modules" OR "docs/diagrams" OR "docs/adr"
WHERE type = "architecture" OR type = "module" OR type = "diagram" OR type = "adr"
SORT file.name ASC
```