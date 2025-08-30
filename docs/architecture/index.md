---
title: "Архитектура системы"
type: "architecture"
audiences: ["backend_dev", "frontend_dev", "devops", "architect"]
tags: ["doc", "lab-equipment-system", "architecture"]
aliases: ["docs/architecture", "docs/arch"]
status: "approved"
last_updated: "2024-12-19"
sources:
  - path: "README.md"
    lines: "L30-L80"
    permalink: "https://github.com/lab-equipment-system/blob/main/README.md#L30-L80"
  - path: "core/di_container.py"
    lines: "L1-L50"
    permalink: "https://github.com/lab-equipment-system/blob/main/core/di_container.py#L1-L50"
  - path: "core/interfaces.py"
    lines: "L1-L453"
    permalink: "https://github.com/lab-equipment-system/blob/main/core/interfaces.py#L1-L453"
related: ["docs/overview", "docs/api/index", "docs/modules/core"]
---

> [!info] Навигация
> Родитель: [[docs/overview]] • Раздел: [[_moc/Architecture]] • См. также: [[docs/api/index]]

# Архитектура системы

## Контекст (C4)

Система управления лабораторным оборудованием представляет собой десктопное приложение, которое взаимодействует с лабораторным оборудованием через последовательные порты и предоставляет пользовательский интерфейс для управления процессами.

### Ключевые стейкхолдеры:
- **Лаборанты**: основные пользователи системы
- **Администраторы**: настройка и обслуживание
- **Разработчики**: поддержка и развитие системы

## Контейнеры

### 1. Desktop Application (PySide6)
- **Технология**: Python + PySide6 (Qt6)
- **Ответственность**: Пользовательский интерфейс, управление жизненным циклом приложения
- **Коммуникация**: Внутренние вызовы методов, сигналы/слоты Qt

### 2. Core Business Logic
- **Технология**: Python
- **Ответственность**: Бизнес-логика, управление оборудованием, последовательности
- **Коммуникация**: Dependency Injection, интерфейсы

### 3. Serial Communication Layer
- **Технология**: pyserial
- **Ответственность**: Коммуникация с лабораторным оборудованием
- **Коммуникация**: Последовательные порты

## Компоненты

### UI Layer
- **MainWindow**: Главное окно приложения
- **WizardPage**: Мастер настройки
- **SettingsPage**: Страница настроек
- **CommandsPage**: Управление командами
- **DesignerPage**: Дизайнер последовательностей
- **FirmwarePage**: Управление прошивкой

### Core Layer
- **SerialManager**: Управление последовательными портами
- **SequenceManager**: Управление последовательностями команд
- **CommandExecutor**: Выполнение команд
- **DIContainer**: Контейнер зависимостей

### Monitoring Layer
- **MonitoringManager**: Мониторинг состояния системы
- **HealthChecker**: Проверка здоровья системы
- **PerformanceMonitor**: Мониторинг производительности
- **ErrorAlerter**: Уведомления об ошибках

### Configuration Layer
- **ConfigLoader**: Загрузка конфигурации
- **SettingsManager**: Управление настройками

### Utilities Layer
- **Logger**: Логирование
- **ErrorHandler**: Обработка ошибок
- **GitManager**: Управление версиями

## Диаграммы

### Контейнерная диаграмма (C4 Level 2)

```plantuml
@startuml Container Diagram
!theme plain
skinparam backgroundColor #FFFFFF
skinparam componentStyle rectangle

title Контейнерная диаграмма системы управления лабораторным оборудованием

package "Desktop Application" {
    [MainWindow] as MW
    [UI Pages] as UP
    [UI Components] as UC
    [UI Widgets] as UW
}

package "Core Business Logic" {
    [DIContainer] as DI
    [SerialManager] as SM
    [SequenceManager] as SQ
    [CommandExecutor] as CE
    [Interfaces] as IF
}

package "Motto Framework" {
    [Motto Parser] as MP
    [Motto Executor] as ME
    [Motto Validator] as MV
    [Motto UI Integration] as MU
}

package "Monitoring System" {
    [MonitoringManager] as MM
    [HealthChecker] as HC
    [PerformanceMonitor] as PM
    [ErrorAlerter] as EA
    [UsageMetrics] as UM
}

package "Configuration System" {
    [ConfigLoader] as CL
    [SettingsManager] as ST
}

package "Utilities" {
    [Logger] as LG
    [ErrorHandler] as EH
    [GitManager] as GM
    [PlatformIOManager] as PI
}

package "External Systems" {
    [Laboratory Equipment] as LE
    [Serial Ports] as SP
    [File System] as FS
    [Git Repository] as GR
}

' UI Layer connections
MW --> UP
MW --> UC
MW --> UW
UP --> DI
UC --> DI
UW --> DI

' Core Layer connections
DI --> SM
DI --> SQ
DI --> CE
DI --> IF
SM --> SP
CE --> SM

' Motto Framework connections
SQ --> MP
MP --> ME
ME --> MV
MU --> MW

' Monitoring connections
MM --> HC
MM --> PM
MM --> EA
MM --> UM
EA --> MW

' Configuration connections
CL --> FS
ST --> FS
DI --> CL
DI --> ST

' Utilities connections
LG --> FS
EH --> LG
GM --> GR
PI --> FS

' External connections
SP --> LE

@enduml
```

### Компонентная диаграмма (C4 Level 3)

```plantuml
@startuml Component Diagram
!theme plain
skinparam backgroundColor #FFFFFF
skinparam componentStyle rectangle

title Компонентная диаграмма - Детальный вид

package "UI Layer" {
    [MainWindow] as MW
    [WizardPage] as WP
    [SettingsPage] as SP
    [CommandsPage] as CP
    [DesignerPage] as DP
    [FirmwarePage] as FP
    [MonitoringPage] as MP
    [SequencesPage] as SQ
    
    [ConnectionManager] as CM
    [EventBus] as EB
    [NavigationManager] as NM
    [PageManager] as PM
    
    [InfoPanel] as IP
    [ModernWidgets] as MWG
    [MonitoringPanel] as MNP
    [OverlayPanel] as OP
}

package "Core Layer" {
    [DIContainer] as DI
    [SerialManager] as SM
    [SequenceManager] as SQ
    [CommandExecutor] as CE
    [Interfaces] as IF
}

package "Motto Framework" {
    [Motto Parser] as MP
    [Motto Executor] as ME
    [Motto Validator] as MV
    [Motto UI Integration] as MU
    [Motto Types] as MT
    [Motto Events] as MEV
    [Motto Guards] as MG
    [Motto Policies] as MPO
    [Motto Resources] as MR
    [Motto Templates] as MT
    [Motto Compatibility] as MC
    [Motto Audit] as MA
}

package "Monitoring Layer" {
    [MonitoringManager] as MM
    [HealthChecker] as HC
    [PerformanceMonitor] as PM
    [ErrorAlerter] as EA
    [UsageMetrics] as UM
}

package "Configuration Layer" {
    [ConfigLoader] as CL
    [SettingsManager] as ST
}

package "Utilities Layer" {
    [Logger] as LG
    [ErrorHandler] as EH
    [GitManager] as GM
    [PlatformIOManager] as PI
}

' UI Component connections
MW --> CM
MW --> EB
MW --> NM
MW --> PM
MW --> IP
MW --> MWG
MW --> MNP
MW --> OP

WP --> EB
SP --> EB
CP --> EB
DP --> EB
FP --> EB
MP --> EB
SQ --> EB

' Core connections
DI --> SM
DI --> SQ
DI --> CE
DI --> IF

' Motto connections
SQ --> MP
MP --> ME
ME --> MV
MU --> MW
MP --> MT
MP --> MEV
MP --> MG
MP --> MPO
MP --> MR
MP --> MT
MP --> MC
MP --> MA

' Monitoring connections
MM --> HC
MM --> PM
MM --> EA
MM --> UM
EA --> EB

' Configuration connections
CL --> ST
DI --> CL
DI --> ST

' Utilities connections
LG --> EH
GM --> PI
DI --> LG
DI --> EH
DI --> GM

@enduml
```

### Диаграмма последовательности - Выполнение команды

```plantuml
@startuml Command Execution Sequence
!theme plain
skinparam backgroundColor #FFFFFF

title Диаграмма последовательности - Выполнение команды

actor User as U
participant "MainWindow" as MW
participant "CommandsPage" as CP
participant "CommandExecutor" as CE
participant "SerialManager" as SM
participant "SequenceManager" as SQ
participant "DIContainer" as DI
participant "Logger" as LG
participant "Laboratory Equipment" as LE

U -> MW: Выбрать команду
MW -> CP: Открыть страницу команд
CP -> CE: execute_command(command)
CE -> DI: resolve(ISerialManager)
DI -> SM: create instance
CE -> SM: send_command(command)
SM -> LG: log_command(command)
SM -> LE: Отправить команду
LE -> SM: Ответ
SM -> CE: Результат выполнения
CE -> CP: CommandResult
CP -> MW: Обновить UI
MW -> U: Показать результат

@enduml
```

### Диаграмма последовательности - Выполнение последовательности

```plantuml
@startuml Sequence Execution Flow
!theme plain
skinparam backgroundColor #FFFFFF

title Диаграмма последовательности - Выполнение последовательности

actor User as U
participant "MainWindow" as MW
participant "SequencesPage" as SP
participant "SequenceManager" as SQ
participant "Motto Parser" as MP
participant "Motto Executor" as ME
participant "Motto Validator" as MV
participant "CommandExecutor" as CE
participant "SerialManager" as SM
participant "MonitoringManager" as MM
participant "ErrorAlerter" as EA

U -> MW: Запустить последовательность
MW -> SP: execute_sequence(sequence_name)
SP -> SQ: execute_sequence(sequence_name)
SQ -> MP: parse_sequence(sequence_data)
MP -> MV: validate_sequence(parsed_data)
MV -> SQ: ValidationResult

alt Валидация успешна
    SQ -> ME: execute_sequence(validated_data)
    ME -> CE: execute_command(command)
    CE -> SM: send_command(command)
    SM -> CE: CommandResult
    CE -> ME: ExecutionResult
    ME -> SQ: SequenceResult
    SQ -> MM: update_metrics(result)
    SQ -> SP: SequenceCompleted
    SP -> MW: Обновить UI
    MW -> U: Показать результат
else Валидация неуспешна
    MV -> SQ: ValidationError
    SQ -> EA: report_error(error)
    EA -> MW: Показать ошибку
    MW -> U: Показать ошибку
end

@enduml
```

### Диаграмма состояний - SerialManager

```plantuml
@startuml SerialManager State Diagram
!theme plain
skinparam backgroundColor #FFFFFF

title Диаграмма состояний - SerialManager

[*] --> Disconnected : Инициализация

state Disconnected {
    [*] --> Ready
    Ready --> Connecting : connect()
    Connecting --> Connected : Успешное подключение
    Connecting --> Error : Ошибка подключения
    Error --> Ready : reset()
}

state Connected {
    [*] --> Idle
    Idle --> Sending : send_command()
    Sending --> Waiting : Команда отправлена
    Waiting --> Idle : Получен ответ
    Waiting --> Error : Таймаут/Ошибка
    Idle --> Disconnecting : disconnect()
    Sending --> Disconnecting : disconnect()
    Waiting --> Disconnecting : disconnect()
}

state Error {
    [*] --> ErrorState
    ErrorState --> Ready : reset()
    ErrorState --> Disconnected : force_disconnect()
}

Disconnecting --> Disconnected : Отключение завершено

@enduml
```

### Диаграмма состояний - SequenceManager

```plantuml
@startuml SequenceManager State Diagram
!theme plain
skinparam backgroundColor #FFFFFF

title Диаграмма состояний - SequenceManager

[*] --> Idle : Инициализация

state Idle {
    [*] --> Ready
    Ready --> Parsing : execute_sequence()
    Parsing --> Validating : Парсинг завершен
    Parsing --> Error : Ошибка парсинга
}

state Validating {
    [*] --> ValidationInProgress
    ValidationInProgress --> Valid : Валидация успешна
    ValidationInProgress --> Invalid : Валидация неуспешна
    Invalid --> Error : Ошибка валидации
}

state Valid {
    [*] --> ReadyToExecute
    ReadyToExecute --> Executing : start_execution()
}

state Executing {
    [*] --> CommandExecution
    CommandExecution --> WaitingResponse : Команда отправлена
    WaitingResponse --> CommandExecution : Получен ответ
    WaitingResponse --> Error : Таймаут/Ошибка
    CommandExecution --> Completed : Все команды выполнены
    CommandExecution --> Cancelled : cancel_execution()
}

state Completed {
    [*] --> Success
    Success --> Idle : reset()
}

state Cancelled {
    [*] --> CancelledState
    CancelledState --> Idle : reset()
}

state Error {
    [*] --> ErrorState
    ErrorState --> Idle : reset()
    ErrorState --> Idle : handle_error()
}

@enduml
```

### Диаграмма классов - Основные интерфейсы

```plantuml
@startuml Core Interfaces Class Diagram
!theme plain
skinparam backgroundColor #FFFFFF

title Диаграмма классов - Основные интерфейсы

interface ISerialManager {
    + connect(port: str, baudrate: int): bool
    + disconnect(): void
    + send_command(command: str): bool
    + is_connected(): bool
    + get_available_ports(): List[str]
    + get_port_info(): Dict[str, Any]
}

interface ICommandExecutor {
    + execute(command: str): bool
    + validate_command(command: str): bool
}

interface ISequenceManager {
    + expand_sequence(sequence_name: str): List[str]
    + validate_sequence(sequence_name: str): tuple[bool, List[str]]
    + get_sequence_info(sequence_name: str): Dict[str, Any]
    + clear_cache(): void
}

interface IConfigLoader {
    + load(): Optional[Dict[str, Any]]
    + save(config: Dict[str, Any]): bool
    + reload(): Optional[Dict[str, Any]]
}

interface ISettingsManager {
    + get_setting(key: str, default: Any): Any
    + set_setting(key: str, value: Any): bool
    + save_settings(): bool
    + load_settings(): bool
}

interface ILogger {
    + debug(message: str): void
    + info(message: str): void
    + warning(message: str): void
    + error(message: str): void
    + critical(message: str): void
}

interface IThreadManager {
    + start_thread(name: str, target: callable): Any
    + stop_thread(name: str, timeout: float): bool
    + stop_all_threads(timeout: float): Dict[str, bool]
    + get_thread_info(): Dict[str, Dict]
}

interface IEventBus {
    + subscribe(event_type: str, callback: callable): void
    + unsubscribe(event_type: str, callback: callable): void
    + publish(event_type: str, data: Any): void
}

interface IConnectionManager {
    + connect(**kwargs): bool
    + disconnect(): bool
    + is_connected(): bool
    + get_connection_info(): Dict[str, Any]
}

interface INavigationManager {
    + navigate_to(page_name: str): bool
    + go_back(): bool
    + get_current_page(): str
    + get_navigation_history(): List[str]
}

interface IPageManager {
    + register_page(name: str, page_class: type): void
    + get_page(name: str): Optional[Any]
    + create_page(name: str, **kwargs): Optional[Any]
    + get_registered_pages(): List[str]
}

interface IDIContainer {
    + register(interface: type, implementation: type): void
    + resolve(interface: type): Any
    + resolve_by_name(service_name: str): Any
    + register_instance(interface: type, instance: Any): void
    + has_service(interface: type): bool
    + clear(): void
}

class ServiceRegistration {
    + interface: type
    + implementation: type
    + singleton: bool
    + factory: Optional[Callable]
    + dependencies: Optional[Dict[str, str]]
}

@enduml
```

### Диаграмма развертывания

```plantuml
@startuml Deployment Diagram
!theme plain
skinparam backgroundColor #FFFFFF

title Диаграмма развертывания

node "Desktop Computer" {
    node "Python Runtime" {
        [PySide6 Application] as APP
        [Python 3.9+] as PY
    }
    
    node "Operating System" {
        [Serial Port Driver] as SPD
        [File System] as FS
        [Network Stack] as NS
    }
    
    node "Hardware" {
        [Serial Port] as SP
        [USB Interface] as USB
        [Display] as DISP
        [Keyboard/Mouse] as KB
    }
}

node "Laboratory Equipment" {
    [Microcontroller] as MC
    [Sensors] as SENS
    [Actuators] as ACT
    [Communication Module] as CM
}

node "External Systems" {
    [Git Repository] as GR
    [Configuration Files] as CF
    [Log Files] as LF
}

' Application connections
APP --> PY
APP --> SPD
APP --> FS
APP --> NS

' Hardware connections
SPD --> SP
SP --> USB
APP --> DISP
APP --> KB

' External connections
SP --> CM
CM --> MC
MC --> SENS
MC --> ACT

NS --> GR
FS --> CF
FS --> LF

@enduml
```

## Нефункциональные требования

### Производительность
- Время отклика UI: < 100ms
- Время выполнения команд: < 5s
- Потребление памяти: < 500MB

### Надежность
- Доступность: 99.9%
- Graceful shutdown при ошибках
- Автоматическое восстановление соединений

### Безопасность
- Валидация всех команд
- Защита от некорректных последовательностей
- Логирование всех операций

### Масштабируемость
- Поддержка множественных устройств
- Модульная архитектура
- Расширяемые интерфейсы

## Архитектурные паттерны

### Dependency Injection
- **DIContainer**: Центральный контейнер для управления зависимостями
- **ServiceRegistration**: Регистрация сервисов с различными жизненными циклами
- **Автоматическое разрешение**: Рекурсивное разрешение зависимостей

### Command Pattern
- **CommandExecutor**: Выполнение команд на устройстве
- **CommandSequenceExecutor**: Выполнение последовательностей команд
- **AsyncCommandExecution**: Асинхронное выполнение с таймаутами

### Observer Pattern
- **Signal/Slot механизм Qt**: Реактивное обновление UI
- **MonitoringManager**: Наблюдение за состоянием системы
- **ErrorAlerter**: Уведомления об ошибках

### State Pattern
- **SerialManager**: Управление состояниями подключения
- **SequenceManager**: Управление состояниями выполнения последовательностей
- **ThreadManager**: Управление состояниями потоков

## Принципы SOLID

- **Single Responsibility**: Каждый класс имеет одну ответственность
- **Open/Closed**: Расширение через интерфейсы и наследование
- **Liskov Substitution**: Замена реализаций через интерфейсы
- **Interface Segregation**: Специализированные интерфейсы
- **Dependency Inversion**: Зависимость от абстракций