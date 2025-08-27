---
title: "MOC: Главная навигация"
type: "moc"
audiences: ["all"]
tags: ["moc", "navigation", "home"]
last_updated: "2024-12-19"
---

# 🏠 MOC: Главная навигация

> [!info] Навигация
> Это главная карта контента (MOC) для навигации по всей документации проекта

## 📋 Основные разделы

### [[docs/overview|Обзор проекта]]
- Назначение и возможности приложения
- Ключевые компоненты
- Технологический стек
- Быстрый старт

### [[docs/architecture/index|Архитектура]]
- Архитектурные решения
- Диаграммы системы
- Компоненты и их взаимодействие
- Dependency Injection

### [[docs/api/index|API Reference]]
- Документация всех публичных API
- Интерфейсы и контракты
- Примеры использования
- Справочная информация

### [[docs/guides/index|Руководства]]
- Пошаговые инструкции
- Практические примеры
- Лучшие практики
- Решение типовых задач

### [[docs/tutorials/index|Обучающие материалы]]
- [[docs/tutorials/quick-start|⚡ Быстрый старт]] - Запуск за 5 минут
- [[docs/tutorials/getting-started|🚀 Полное руководство]] - Пошаговая настройка
- Уроки для начинающих
- Интерактивные примеры
- Постепенное изучение функций
- Практические задания

### [[docs/operations/index|Эксплуатация]]
- Развертывание приложения
- Мониторинг и логирование
- Резервное копирование
- Обновления и миграции

### [[docs/security/index|Безопасность]]
- Модель угроз
- Рекомендации по безопасности
- Аудит безопасности
- Обработка уязвимостей

### [[docs/data/index|Данные и схемы]]
- Структуры данных
- Конфигурационные файлы
- Схемы событий
- Форматы обмена данными

### [[docs/faq|FAQ]]
- Часто задаваемые вопросы
- Решения типовых проблем
- Советы и рекомендации

## 🔧 Специализированные разделы

### [[docs/architecture/adr/index|Architecture Decision Records]]
- Записи архитектурных решений
- Обоснования выбора технологий
- Альтернативы и их анализ

### [[docs/runbooks/index|Рунбуки]]
- Операционные процедуры
- Troubleshooting guides
- Playbooks для инцидентов

### [[docs/modules/index|Модули]]
- Документация отдельных модулей
- Внутренние интерфейсы
- Детали реализации

## 📊 Мета-информация

### [[docs/_meta/project_audit|Аудит проекта]]
- Анализ текущего состояния
- Выявленные пробелы
- План развития документации

### [[docs/_meta/ia_spec|Информационная архитектура]]
- Персоны пользователей
- Типы контента
- Навигационные паттерны

### [[docs/_meta/reference_inventory|Инвентарь API]]
- Каталог всех публичных поверхностей
- Ссылки на исходный код
- Статус документации

### [[docs/_meta/doc_quality_report|Отчет о качестве]]
- Метрики покрытия
- Результаты проверок
- Проблемы и их решения

## 🎯 Быстрый доступ по ролям

### Для разработчиков
- [[docs/api/index|API Reference]]
- [[docs/api/interfaces/index|API Interfaces]]
- [[docs/architecture/index|Архитектура]]
- [[docs/guides/development|Руководство разработчика]]
- [[docs/modules/index|Модули]]

### Для DevOps
- [[docs/operations/index|Эксплуатация]]
- [[docs/runbooks/index|Рунбуки]]
- [[docs/security/index|Безопасность]]
- [[docs/guides/deployment|Руководство по развертыванию]]

### Для поддержки
- [[docs/faq|FAQ]]
- [[docs/guides/user|Пользовательское руководство]]
- [[docs/runbooks/troubleshooting|Troubleshooting]]
- [[docs/tutorials/index|Обучающие материалы]]

### Для менеджеров
- [[docs/overview|Обзор проекта]]
- [[docs/architecture/adr/index|Архитектурные решения]]
- [[docs/_meta/project_audit|Аудит проекта]]
- [[docs/guides/contribution|Руководство по участию]]

## 📈 Автоиндекс (Dataview)

```dataview
TABLE file.link AS "Документ", type, audiences, last_updated
FROM "docs"
WHERE type != "moc" AND type != "report"
SORT file.name ASC
```

## 🔗 Связанные документы

- [[AUDIT_REPORT|Аудит приложения]]
- [[README|README проекта]]
- [[pyproject.toml|Конфигурация проекта]]
- [[requirements.txt|Зависимости]]
