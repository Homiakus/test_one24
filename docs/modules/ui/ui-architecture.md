---
title: "UI Architecture - Архитектура пользовательского интерфейса"
type: "module"
audiences: ["frontend_dev", "architect"]
tags: ["doc", "lab-equipment-system", "ui", "architecture"]
status: "approved"
last_updated: "2024-12-19"
sources:
  - path: "ui/main_window.py"
    lines: "L1-L100"
    permalink: "https://github.com/lab-equipment-system/blob/main/ui/main_window.py#L1-L100"
  - path: "ui/components/__init__.py"
    lines: "L1-L16"
    permalink: "https://github.com/lab-equipment-system/blob/main/ui/components/__init__.py#L1-L16"
related: ["docs/modules/ui/pages", "docs/modules/ui/widgets"]
---

> [!info] Навигация
> Родитель: [[docs/modules/ui]] • Раздел: [[_moc/Architecture]] • См. также: [[docs/modules/ui/pages]]

# UI Architecture - Архитектура пользовательского интерфейса

## Обзор

UI архитектура системы управления лабораторным оборудованием построена на основе PySide6 (Qt6) с использованием паттернов MVC, Observer и Dependency Injection. Архитектура обеспечивает модульность, расширяемость и тестируемость интерфейса.

## Общая архитектура UI

```plantuml
@startuml UI Architecture Overview
!theme plain
skinparam backgroundColor #FFFFFF

title Общая архитектура UI

package "UI Layer" {
    [MainWindow] as MW
    [PageManager] as PM
    [NavigationManager] as NM
    [EventBus] as EB
    [ConnectionManager] as CM
}

package "Pages" {
    [WizardPage] as WP
    [SettingsPage] as SP
    [CommandsPage] as CP
    [DesignerPage] as DP
    [FirmwarePage] as FP
    [MonitoringPage] as MP
    [SequencesPage] as SQ
}

package "Components" {
    [InfoPanel] as IP
    [ModernWidgets] as MWG
    [MonitoringPanel] as MNP
    [OverlayPanel] as OP
}

package "Core Integration" {
    [DIContainer] as DI
    [SerialManager] as SM
    [SequenceManager] as SQ
    [MonitoringManager] as MM
}

package "Qt Framework" {
    [QMainWindow] as QMW
    [QWidget] as QW
    [QSignal] as QS
    [QSlot] as QSL
}

' MainWindow connections
MW --> PM
MW --> NM
MW --> EB
MW --> CM
MW --> QMW

' PageManager connections
PM --> WP
PM --> SP
PM --> CP
PM --> DP
PM --> FP
PM --> MP
PM --> SQ

' NavigationManager connections
NM --> PM
NM --> EB

' EventBus connections
EB --> WP
EB --> SP
EB --> CP
EB --> DP
EB --> FP
EB --> MP
EB --> SQ

' Components connections
MW --> IP
MW --> MWG
MW --> MNP
MW --> OP

' Core Integration
MW --> DI
DI --> SM
DI --> SQ
DI --> MM

' Qt Framework
QMW --> QW
QW --> QS
QS --> QSL

@enduml
```

## Компонентная архитектура

### MainWindow - Главное окно

```plantuml
@startuml MainWindow Component
!theme plain
skinparam backgroundColor #FFFFFF

title Компонент MainWindow

class MainWindow {
    - page_manager: PageManager
    - navigation_manager: NavigationManager
    - event_bus: EventBus
    - connection_manager: ConnectionManager
    - di_container: DIContainer
    
    + __init__(di_container: DIContainer)
    + setup_ui(): void
    + setup_connections(): void
    + setup_menu(): void
    + setup_toolbar(): void
    + setup_statusbar(): void
    + show_page(page_name: str): void
    + handle_navigation(page_name: str): void
    + handle_event(event_type: str, data: Any): void
    + closeEvent(event: QCloseEvent): void
}

class PageManager {
    - pages: Dict[str, BasePage]
    - current_page: Optional[BasePage]
    
    + register_page(name: str, page_class: type): void
    + get_page(name: str): Optional[BasePage]
    + show_page(name: str): bool
    + get_current_page(): Optional[BasePage]
    + get_registered_pages(): List[str]
}

class NavigationManager {
    - history: List[str]
    - max_history: int
    
    + navigate_to(page_name: str): bool
    + go_back(): bool
    + go_forward(): bool
    + get_current_page(): str
    + get_navigation_history(): List[str]
    + clear_history(): void
}

class EventBus {
    - subscribers: Dict[str, List[Callable]]
    
    + subscribe(event_type: str, callback: Callable): void
    + unsubscribe(event_type: str, callback: Callable): void
    + publish(event_type: str, data: Any): void
    + get_subscribers(event_type: str): List[Callable]
}

class ConnectionManager {
    - serial_manager: ISerialManager
    - connection_status: bool
    
    + connect(port: str, baudrate: int): bool
    + disconnect(): bool
    + is_connected(): bool
    + get_connection_info(): Dict[str, Any]
    + update_connection_status(): void
}

MainWindow --> PageManager
MainWindow --> NavigationManager
MainWindow --> EventBus
MainWindow --> ConnectionManager
MainWindow --> DIContainer

@enduml
```

## Система страниц

### Иерархия страниц

```plantuml
@startuml Pages Hierarchy
!theme plain
skinparam backgroundColor #FFFFFF

title Иерархия страниц

abstract class BasePage {
    + setup_ui(): void
    + setup_connections(): void
    + on_show(): void
    + on_hide(): void
    + handle_event(event_type: str, data: Any): void
}

class WizardPage {
    - steps: List[WizardStep]
    - current_step: int
    
    + setup_ui(): void
    + next_step(): void
    + previous_step(): void
    + validate_current_step(): bool
    + complete_wizard(): void
}

class SettingsPage {
    - settings_manager: ISettingsManager
    - settings_widgets: Dict[str, QWidget]
    
    + setup_ui(): void
    + load_settings(): void
    + save_settings(): void
    + apply_settings(): void
    + reset_settings(): void
}

class CommandsPage {
    - command_executor: ICommandExecutor
    - command_history: List[Command]
    
    + setup_ui(): void
    + execute_command(command: str): void
    + show_command_history(): void
    + clear_history(): void
}

class DesignerPage {
    - sequence_manager: ISequenceManager
    - sequence_editor: SequenceEditor
    
    + setup_ui(): void
    + create_sequence(): void
    + edit_sequence(sequence_name: str): void
    + save_sequence(): void
    + test_sequence(): void
}

class FirmwarePage {
    - platformio_manager: PlatformIOManager
    - firmware_info: Dict[str, Any]
    
    + setup_ui(): void
    + upload_firmware(): void
    + download_firmware(): void
    + check_firmware_version(): void
}

class MonitoringPage {
    - monitoring_manager: IMonitoringManager
    - monitoring_panel: MonitoringPanel
    
    + setup_ui(): void
    + start_monitoring(): void
    + stop_monitoring(): void
    + update_metrics(): void
    + show_alerts(): void
}

class SequencesPage {
    - sequence_manager: ISequenceManager
    - motto_integration: MottoUIIntegration
    
    + setup_ui(): void
    + load_sequences(): void
    + execute_sequence(sequence_name: str): void
    + edit_sequence(sequence_name: str): void
    + delete_sequence(sequence_name: str): void
}

BasePage <|-- WizardPage
BasePage <|-- SettingsPage
BasePage <|-- CommandsPage
BasePage <|-- DesignerPage
BasePage <|-- FirmwarePage
BasePage <|-- MonitoringPage
BasePage <|-- SequencesPage

@enduml
```

## Система компонентов

### UI Components

```plantuml
@startuml UI Components
!theme plain
skinparam backgroundColor #FFFFFF

title UI Components

class InfoPanel {
    - info_data: Dict[str, Any]
    - update_timer: QTimer
    
    + setup_ui(): void
    + update_info(data: Dict[str, Any]): void
    + show_info(info_type: str): void
    + hide_info(): void
    + set_update_interval(interval: int): void
}

class ModernWidgets {
    + create_button(text: str, icon: str): QPushButton
    + create_input_field(placeholder: str): QLineEdit
    + create_dropdown(options: List[str]): QComboBox
    + create_progress_bar(): QProgressBar
    + create_status_indicator(): StatusIndicator
}

class MonitoringPanel {
    - monitoring_manager: IMonitoringManager
    - metrics_widgets: Dict[str, QWidget]
    
    + setup_ui(): void
    + update_metrics(metrics: Dict[str, Any]): void
    + show_alert(alert: Alert): void
    + clear_alerts(): void
    + set_refresh_interval(interval: int): void
}

class OverlayPanel {
    - overlay_type: OverlayType
    - overlay_data: Dict[str, Any]
    
    + setup_ui(): void
    + show_overlay(overlay_type: OverlayType, data: Dict[str, Any]): void
    + hide_overlay(): void
    + update_overlay(data: Dict[str, Any]): void
}

class StatusIndicator {
    - status: Status
    - status_text: str
    
    + set_status(status: Status): void
    + set_text(text: str): void
    + get_status(): Status
    + get_text(): str
}

class SequenceEditor {
    - sequence_data: Dict[str, Any]
    - editor_widgets: List[QWidget]
    
    + setup_ui(): void
    + load_sequence(sequence_data: Dict[str, Any]): void
    + save_sequence(): Dict[str, Any]
    + add_command(command: Command): void
    + remove_command(command_id: str): void
    + validate_sequence(): bool
}

InfoPanel --> ModernWidgets
MonitoringPanel --> ModernWidgets
OverlayPanel --> ModernWidgets
MonitoringPanel --> StatusIndicator
SequenceEditor --> ModernWidgets

@enduml
```

## Система событий

### Event Flow

```plantuml
@startuml UI Event Flow
!theme plain
skinparam backgroundColor #FFFFFF

title Система событий UI

participant "User Action" as UA
participant "UI Component" as UIC
participant "EventBus" as EB
participant "Page" as P
participant "MainWindow" as MW
participant "Core Service" as CS

UA -> UIC: Пользовательское действие
UIC -> EB: publish(event_type, data)
EB -> P: handle_event(event_type, data)
P -> CS: Вызов сервиса
CS -> P: Результат
P -> EB: publish(result_event, result_data)
EB -> MW: handle_event(result_event, result_data)
MW -> UIC: Обновление UI

@enduml
```

### Типы событий

```plantuml
@startuml UI Event Types
!theme plain
skinparam backgroundColor #FFFFFF

title Типы событий UI

enum EventType {
    NAVIGATION
    COMMAND_EXECUTION
    SEQUENCE_EXECUTION
    CONNECTION_STATUS
    MONITORING_UPDATE
    SETTINGS_CHANGE
    ERROR_OCCURRED
    WARNING_SHOWN
    INFO_DISPLAYED
}

class NavigationEvent {
    + from_page: str
    + to_page: str
    + navigation_type: NavigationType
}

class CommandExecutionEvent {
    + command: str
    + result: CommandResult
    + execution_time: float
}

class SequenceExecutionEvent {
    + sequence_name: str
    + status: ExecutionStatus
    + progress: float
    + current_command: str
}

class ConnectionStatusEvent {
    + connected: bool
    + port: str
    + error_message: str
}

class MonitoringUpdateEvent {
    + metrics: Dict[str, Any]
    + alerts: List[Alert]
    + timestamp: datetime
}

class SettingsChangeEvent {
    + setting_key: str
    + old_value: Any
    + new_value: Any
}

class ErrorEvent {
    + error_type: str
    + error_message: str
    + severity: ErrorSeverity
    + timestamp: datetime
}

EventType --> NavigationEvent
EventType --> CommandExecutionEvent
EventType --> SequenceExecutionEvent
EventType --> ConnectionStatusEvent
EventType --> MonitoringUpdateEvent
EventType --> SettingsChangeEvent
EventType --> ErrorEvent

@enduml
```

## Навигация

### Navigation Flow

```plantuml
@startuml Navigation Flow
!theme plain
skinparam backgroundColor #FFFFFF

title Система навигации

participant "User" as U
participant "MainWindow" as MW
participant "NavigationManager" as NM
participant "PageManager" as PM
participant "EventBus" as EB
participant "TargetPage" as TP

U -> MW: Клик по навигации
MW -> NM: navigate_to(page_name)
NM -> NM: validate_navigation(page_name)

alt Навигация разрешена
    NM -> PM: show_page(page_name)
    PM -> TP: on_show()
    TP -> TP: setup_ui()
    TP -> TP: load_data()
    PM -> NM: update_current_page(page_name)
    NM -> NM: add_to_history(page_name)
    NM -> EB: publish(navigation_completed, page_name)
    EB -> MW: handle_event(navigation_completed, page_name)
    MW -> U: Показать новую страницу
else Навигация запрещена
    NM -> EB: publish(navigation_failed, page_name)
    EB -> MW: handle_event(navigation_failed, page_name)
    MW -> U: Показать ошибку
end

@enduml
```

## Управление состоянием

### State Management

```plantuml
@startuml UI State Management
!theme plain
skinparam backgroundColor #FFFFFF

title Управление состоянием UI

class UIState {
    - current_page: str
    - connection_status: bool
    - monitoring_active: bool
    - sequence_running: bool
    - settings_modified: bool
    
    + get_current_page(): str
    + set_current_page(page: str): void
    + is_connected(): bool
    + set_connection_status(status: bool): void
    + is_monitoring_active(): bool
    + set_monitoring_active(active: bool): void
    + is_sequence_running(): bool
    + set_sequence_running(running: bool): void
    + are_settings_modified(): bool
    + set_settings_modified(modified: bool): void
}

class StateObserver {
    + on_state_changed(state_key: str, old_value: Any, new_value: Any): void
}

class StateManager {
    - state: UIState
    - observers: List[StateObserver]
    
    + get_state(): UIState
    + update_state(key: str, value: Any): void
    + add_observer(observer: StateObserver): void
    + remove_observer(observer: StateObserver): void
    + notify_observers(key: str, old_value: Any, new_value: Any): void
}

class MainWindow {
    - state_manager: StateManager
    
    + setup_state_management(): void
    + on_state_changed(state_key: str, old_value: Any, new_value: Any): void
    + update_ui_for_state(): void
}

StateManager --> UIState
StateManager --> StateObserver
MainWindow --> StateManager
MainWindow ..|> StateObserver

@enduml
```

## Интеграция с Core

### Core Integration Flow

```plantuml
@startuml Core Integration Flow
!theme plain
skinparam backgroundColor #FFFFFF

title Интеграция UI с Core

participant "UI Component" as UIC
participant "DIContainer" as DI
participant "Core Service" as CS
participant "EventBus" as EB
participant "Other UI Components" as OUIC

UIC -> DI: resolve(IServiceInterface)
DI -> CS: create instance
DI -> UIC: service instance

UIC -> CS: service_method(params)
CS -> CS: process_request(params)
CS -> EB: publish(result_event, result_data)
EB -> OUIC: handle_event(result_event, result_data)
CS -> UIC: return result

@enduml
```

## Производительность

### Оптимизации UI

```plantuml
@startuml UI Performance Optimizations
!theme plain
skinparam backgroundColor #FFFFFF

title Оптимизации производительности UI

package "Lazy Loading" {
    [PageLoader] as PL
    [ComponentLoader] as CL
    [ResourceLoader] as RL
}

package "Caching" {
    [PageCache] as PC
    [ComponentCache] as CC
    [DataCache] as DC
}

package "Async Operations" {
    [AsyncExecutor] as AE
    [BackgroundWorker] as BW
    [TaskQueue] as TQ
}

package "UI Updates" {
    [UpdateBatcher] as UB
    [UpdateScheduler] as US
    [UpdateOptimizer] as UO
}

PL --> PC
CL --> CC
RL --> DC

AE --> BW
BW --> TQ

UB --> US
US --> UO

@enduml
```

## Тестирование UI

### UI Testing Strategy

```plantuml
@startuml UI Testing Strategy
!theme plain
skinparam backgroundColor #FFFFFF

title Стратегия тестирования UI

package "Unit Tests" {
    [Component Tests] as CT
    [Page Tests] as PT
    [Event Tests] as ET
}

package "Integration Tests" {
    [Navigation Tests] as NT
    [Event Flow Tests] as EFT
    [Core Integration Tests] as CIT
}

package "UI Tests" {
    [Widget Tests] as WT
    [User Interaction Tests] as UIT
    [Visual Tests] as VT
}

package "Test Tools" {
    [pytest-qt] as PQ
    [QTest] as QT
    [Mock Objects] as MO
}

CT --> PQ
PT --> PQ
ET --> PQ

NT --> QT
EFT --> QT
CIT --> QT

WT --> MO
UIT --> MO
VT --> MO

@enduml
```

## Будущие улучшения

1. **Responsive Design**: Адаптивный дизайн для разных разрешений
2. **Theming System**: Система тем и стилей
3. **Accessibility**: Улучшение доступности для пользователей с ограниченными возможностями
4. **Internationalization**: Поддержка множественных языков
5. **Plugin System**: Система плагинов для расширения функциональности
6. **Real-time Collaboration**: Возможность совместной работы
7. **Advanced Visualizations**: Продвинутые визуализации данных
8. **Mobile Support**: Поддержка мобильных устройств