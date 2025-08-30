---
title: "MOC: Обзор проекта"
type: "moc"
audiences: ["pm", "architect", "devops"]
tags: ["doc", "lab-equipment-system", "moc"]
status: "approved"
last_updated: "2024-12-19"
---

# MOC: Обзор проекта

## Основные документы

- [[docs/overview]] - Обзор системы управления лабораторным оборудованием
- [[docs/architecture/index]] - Архитектура системы
- [[docs/api/index]] - API Reference
- [[docs/operations/index]] - Операции и развертывание

## Быстрый старт

- [[docs/runbooks/installation]] - Установка и настройка
- [[docs/runbooks/quick-start]] - Быстрый старт
- [[docs/runbooks/troubleshooting]] - Диагностика проблем

## Архитектура

- [[docs/architecture/index]] - Общая архитектура
- [[docs/modules/core]] - Core модули
- [[docs/modules/ui]] - UI модули
- [[docs/modules/monitoring]] - Мониторинг

## API и интерфейсы

- [[docs/api/index]] - Обзор API
- [[docs/api/serial]] - Serial Manager API
- [[docs/api/commands]] - Command Executor API
- [[docs/api/sequences]] - Sequence Manager API

## Операции

- [[docs/operations/index]] - Операции
- [[docs/operations/deployment]] - Развертывание
- [[docs/operations/monitoring]] - Мониторинг
- [[docs/operations/maintenance]] - Обслуживание

## Безопасность

- [[docs/security/index]] - Безопасность
- [[docs/security/threat-model]] - Модель угроз
- [[docs/security/compliance]] - Соответствие требованиям

## Данные

- [[docs/data/index]] - Управление данными
- [[docs/data/configurations]] - Конфигурации
- [[docs/data/sequences]] - Последовательности
- [[docs/schemas/commands]] - Схемы команд

## Миграции

- [[docs/migration/index]] - Миграции
- [[docs/migration/versions]] - Версии и обновления

## FAQ и поддержка

- [[docs/faq]] - Часто задаваемые вопросы
- [[docs/runbooks/support]] - Поддержка пользователей

## Автоиндекс (Dataview)

```dataview
TABLE file.link AS "Документ", type, last_updated
FROM "docs"
WHERE type = "overview" OR type = "architecture" OR type = "api_reference"
SORT file.name ASC
```