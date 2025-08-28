# Диаграммы архитектуры PyQt6 Device Control

## Общая архитектура системы

```plantuml
@startuml
!define RECTANGLE class

package "UI Layer" {
    RECTANGLE MainWindow {
        +__init__()
        +_setup_ui()
        +_setup_connections()
        +_safe_auto_connect()
    }
    
    RECTANGLE Pages {
        +CommandsPage
        +SequencesPage
        +DesignerPage
        +FirmwarePage
        +FlagsPage
        +SignalsPage
        +SettingsPage
        +WizardPage
    }
    
    RECTANGLE Widgets {
        +ModernCard
        +InfoPanel
        +MonitoringPanel
    }
}

package "Business Logic Layer" {
    RECTANGLE SerialManager {
        +connect()
        +send_command()
        +read_response()
        +disconnect()
    }
    
    RECTANGLE SequenceManager {
        +execute_sequence()
        +set_flag()
        +validate_sequence()
    }
    
    RECTANGLE TagManager {
        +create_tag()
        +get_tagged_commands()
        +delete_tag()
    }
    
    RECTANGLE MultizoneManager {
        +send_multizone_command()
        +configure_zones()
    }
    
    RECTANGLE MonitoringManager {
        +start_monitoring()
        +get_metrics()
    }
}

package "Data Layer" {
    RECTANGLE SettingsManager {
        +save_serial_settings()
        +load_config()
    }
    
    RECTANGLE ConfigLoader {
        +load()
        +validate()
    }
}

package "External" {
    RECTANGLE Device {
        +receive_command()
        +send_response()
    }
    
    RECTANGLE FileSystem {
        +config.toml
        +serial_settings.json
        +update_settings.json
    }
}

MainWindow --> SerialManager
MainWindow --> SequenceManager
MainWindow --> TagManager
MainWindow --> MultizoneManager
MainWindow --> MonitoringManager
MainWindow --> SettingsManager

SerialManager --> Device
SettingsManager --> FileSystem
ConfigLoader --> FileSystem

Pages --> MainWindow
Widgets --> MainWindow
@enduml
```

## Диаграмма последовательности инициализации

```plantuml
@startuml
actor User
participant Main
participant MainWindow
participant SerialManager
participant SettingsManager
participant ConfigLoader
participant Device

User -> Main: Запуск приложения
Main -> Main: Проверка зависимостей
Main -> MainWindow: Создание главного окна

MainWindow -> SettingsManager: Инициализация настроек
SettingsManager -> ConfigLoader: Загрузка конфигурации
ConfigLoader --> SettingsManager: Конфигурация

MainWindow -> SerialManager: Создание менеджера
MainWindow -> MainWindow: Создание других сервисов
MainWindow -> MainWindow: Настройка UI
MainWindow -> MainWindow: Установка соединений

alt Автоподключение включено
    MainWindow -> SerialManager: Подключение
    SerialManager -> Device: Открытие порта
    Device --> SerialManager: Статус
    SerialManager --> MainWindow: Результат
end

MainWindow --> Main: Окно готово
Main -> Main: Запуск главного цикла
@enduml
```

## Диаграмма состояний подключения

```plantuml
@startuml
[*] --> Disconnected

Disconnected --> Connecting : connect()
Connecting --> Connected : Успешное подключение
Connecting --> Disconnected : Ошибка подключения

Connected --> Sending : send_command()
Sending --> Waiting : Команда отправлена
Waiting --> Connected : Ответ получен
Waiting --> Timeout : Таймаут
Timeout --> Connected : Повторная попытка
Timeout --> Disconnected : Максимум попыток

Connected --> Disconnected : disconnect()
Disconnected --> [*]
@enduml
```

## Диаграмма компонентов и зависимостей

```plantuml
@startuml
package "Core Components" {
    component SerialManager
    component SequenceManager
    component TagManager
    component MultizoneManager
    component MonitoringManager
    component SettingsManager
}

package "UI Components" {
    component MainWindow
    component CommandsPage
    component SequencesPage
    component DesignerPage
}

package "Data Storage" {
    component ConfigFiles
    component SettingsFiles
    component LogFiles
}

package "External Interfaces" {
    component SerialPort
    component Device
}

SerialManager --> SerialPort
SerialManager --> Device
SequenceManager --> SerialManager
TagManager --> SequenceManager
MultizoneManager --> SerialManager
MonitoringManager --> SerialManager

MainWindow --> SerialManager
MainWindow --> SequenceManager
MainWindow --> TagManager
MainWindow --> MultizoneManager
MainWindow --> MonitoringManager

CommandsPage --> MainWindow
SequencesPage --> MainWindow
DesignerPage --> MainWindow

SettingsManager --> ConfigFiles
SettingsManager --> SettingsFiles
MonitoringManager --> LogFiles
@enduml
```

## Диаграмма потоков данных

```plantuml
@startuml
!define RECTANGLE class

RECTANGLE User {
    +Ввод команды
    +Выбор последовательности
    +Настройка параметров
}

RECTANGLE UI {
    +Обработка событий
    +Валидация ввода
    +Обновление интерфейса
}

RECTANGLE BusinessLogic {
    +Парсинг команд
    +Валидация последовательностей
    +Управление флагами
    +Обработка тегов
}

RECTANGLE Communication {
    +Отправка команд
    +Чтение ответов
    +Обработка ошибок
    +Управление таймаутами
}

RECTANGLE Device {
    +Выполнение команд
    +Отправка ответов
    +Обработка ошибок
}

RECTANGLE Storage {
    +Конфигурация
    +Настройки
    +Логи
    +История команд
}

User --> UI : События пользователя
UI --> BusinessLogic : Валидированные данные
BusinessLogic --> Communication : Команды для отправки
Communication --> Device : Команды
Device --> Communication : Ответы
Communication --> BusinessLogic : Результаты
BusinessLogic --> UI : Статус выполнения
UI --> User : Обновление интерфейса

BusinessLogic --> Storage : Сохранение данных
Storage --> BusinessLogic : Загрузка конфигурации
@enduml
```

## Диаграмма обработки ошибок

```plantuml
@startuml
start
:Попытка операции;

if (Операция успешна?) then (да)
    :Возврат результата;
    stop
else (нет)
    :Логирование ошибки;
    
    if (Тип ошибки?) then (Connection)
        :Попытка переподключения;
        if (Переподключение успешно?) then (да)
            :Повтор операции;
        else (нет)
            :Уведомление пользователя;
            stop
        endif
    else if (Timeout)
        :Увеличение счетчика попыток;
        if (Счетчик < максимум?) then (да)
            :Повтор операции;
        else (нет)
            :Ошибка таймаута;
            stop
        endif
    else if (Validation)
        :Показать ошибку валидации;
        stop
    else (Other)
        :Общая обработка ошибки;
        :Уведомление пользователя;
        stop
    endif
endif
@enduml
```

## Диаграмма жизненного цикла приложения

```plantuml
@startuml
!define RECTANGLE class

package "Application Lifecycle" {
    RECTANGLE Startup {
        +Проверка зависимостей
        +Инициализация Qt
        +Загрузка конфигурации
        +Создание сервисов
    }
    
    RECTANGLE Running {
        +Главный цикл
        +Обработка событий
        +Мониторинг состояния
        +Периодические задачи
    }
    
    RECTANGLE Shutdown {
        +Graceful shutdown
        +Сохранение настроек
        +Закрытие соединений
        +Очистка ресурсов
    }
}

Startup --> Running : Инициализация завершена
Running --> Running : Обработка событий
Running --> Shutdown : Запрос завершения
Shutdown --> [*] : Приложение завершено
@enduml
```

## Диаграмма модульной структуры

```plantuml
@startuml
package "Core" {
    package "Communication" {
        [SerialManager]
        [Protocol]
        [Connection]
    }
    
    package "Sequences" {
        [SequenceManager]
        [Executor]
        [Validator]
        [Parser]
    }
    
    package "Tags" {
        [TagManager]
        [Processor]
        [Validator]
    }
    
    package "Multizone" {
        [MultizoneManager]
        [Types]
        [Validator]
    }
    
    package "DI" {
        [Container]
        [Resolver]
        [Types]
    }
}

package "UI" {
    package "Pages" {
        [CommandsPage]
        [SequencesPage]
        [DesignerPage]
        [SettingsPage]
    }
    
    package "Widgets" {
        [ModernCard]
        [InfoPanel]
        [MonitoringPanel]
    }
    
    package "Components" {
        [NavigationManager]
        [PageManager]
        [EventBus]
    }
}

package "Config" {
    [SettingsManager]
    [ConfigLoader]
    [SignalConfigParser]
}

package "Utils" {
    [Logger]
    [ErrorHandler]
    [GitManager]
}

package "Monitoring" {
    [MonitoringManager]
    [HealthChecker]
    [PerformanceMonitor]
}

[SerialManager] --> [Protocol]
[SequenceManager] --> [Executor]
[TagManager] --> [Processor]
[MultizoneManager] --> [Types]

[CommandsPage] --> [SerialManager]
[SequencesPage] --> [SequenceManager]
[DesignerPage] --> [TagManager]

[SettingsManager] --> [ConfigLoader]
[MonitoringManager] --> [HealthChecker]
@enduml
```
