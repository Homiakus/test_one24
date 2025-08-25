# Техническая архитектура системы

## 1. Диаграмма компонентов

```mermaid
graph TB
    subgraph "Presentation Layer"
        MW[MainWindow]
        WP[WizardPage]
        SP[SettingsPage]
        CP[CommandsPage]
        DP[DesignerPage]
        FP[FirmwarePage]
    end
    
    subgraph "Business Logic Layer"
        SM[SerialManager]
        SQ[SequenceManager]
        CE[CommandExecutor]
        DI[DIContainer]
    end
    
    subgraph "Data Access Layer"
        CM[ConfigLoader]
        ST[SettingsManager]
        GM[GitManager]
    end
    
    subgraph "Infrastructure Layer"
        LG[Logger]
        EH[ErrorHandler]
        MM[MonitoringManager]
    end
    
    MW --> SM
    MW --> SQ
    MW --> MM
    SM --> DI
    SQ --> DI
    MM --> DI
    CM --> DI
```

## 2. Диаграмма последовательности

### 2.1 Выполнение команды
```mermaid
sequenceDiagram
    participant UI as MainWindow
    participant SM as SerialManager
    participant CE as CommandExecutor
    participant Device as Hardware
    
    UI->>SM: send_command("sm 0 0 0 0 0")
    SM->>CE: execute_command()
    CE->>Device: send_command()
    Device-->>CE: response
    CE-->>SM: result
    SM-->>UI: success/failure
```

### 2.2 Выполнение последовательности
```mermaid
sequenceDiagram
    participant UI as MainWindow
    participant SQ as SequenceManager
    participant CE as CommandExecutor
    participant SM as SerialManager
    participant Device as Hardware
    
    UI->>SQ: execute_sequence("coloring")
    SQ->>CE: create_executor()
    CE->>SM: connect()
    loop For each command
        CE->>SM: send_command(command)
        SM->>Device: execute
        Device-->>SM: response
        SM-->>CE: result
        CE->>SQ: update_progress()
    end
    SQ-->>UI: sequence_completed
```

## 3. Диаграмма состояний

### 3.1 Состояние SerialManager
```mermaid
stateDiagram-v2
    [*] --> Disconnected
    Disconnected --> Connecting : connect()
    Connecting --> Connected : success
    Connecting --> Disconnected : failure
    Connected --> Sending : send_command()
    Sending --> Connected : command_sent
    Sending --> Error : timeout/error
    Error --> Connected : retry
    Connected --> Disconnected : disconnect()
```

### 3.2 Состояние SequenceExecutor
```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Running : execute_sequence()
    Running --> Paused : pause()
    Paused --> Running : resume()
    Running --> Completed : all_commands_done
    Running --> Error : command_failed
    Error --> Running : retry
    Completed --> Idle : reset()
```

## 4. Диаграмма классов

```mermaid
classDiagram
    class ISerialManager {
        <<interface>>
        +connect(port, baudrate, timeout) bool
        +disconnect() void
        +send_command(command) bool
        +is_connected() bool
        +get_available_ports() List~string~
    }
    
    class SerialManager {
        -port: Serial
        -reader: SerialReader
        -lock: RLock
        +connect(port, baudrate, timeout) bool
        +disconnect() void
        +send_command(command) bool
        +is_connected() bool
    }
    
    class ISequenceManager {
        <<interface>>
        +execute_sequence(name) bool
        +stop_sequence() void
        +get_sequences() Dict
    }
    
    class SequenceManager {
        -sequences: Dict
        -executor: CommandSequenceExecutor
        +execute_sequence(name) bool
        +stop_sequence() void
        +create_executor(name) CommandSequenceExecutor
    }
    
    class DIContainer {
        -services: Dict
        -instances: Dict
        -lock: RLock
        +register(interface, implementation) void
        +resolve(interface) Any
        +register_instance(interface, instance) void
    }
    
    ISerialManager <|.. SerialManager
    ISequenceManager <|.. SequenceManager
    SerialManager --> DIContainer
    SequenceManager --> DIContainer
```

## 5. Диаграмма пакетов

```mermaid
graph TB
    subgraph "Core Package"
        core_interfaces[interfaces.py]
        core_serial[serial_manager.py]
        core_sequence[sequence_manager.py]
        core_di[di_container.py]
        core_executor[command_executor.py]
    end
    
    subgraph "UI Package"
        ui_main[main_window.py]
        ui_pages[pages/]
        ui_widgets[widgets/]
        ui_components[components/]
    end
    
    subgraph "Monitoring Package"
        monitoring_manager[monitoring_manager.py]
        health_checker[health_checker.py]
        performance_monitor[performance_monitor.py]
        error_alerter[error_alerter.py]
    end
    
    subgraph "Utils Package"
        utils_logger[logger.py]
        utils_error[error_handler.py]
        utils_git[git_manager.py]
    end
    
    ui_main --> core_serial
    ui_main --> core_sequence
    ui_main --> monitoring_manager
    core_serial --> core_di
    core_sequence --> core_di
```

## 6. Диаграмма развертывания

```mermaid
graph TB
    subgraph "Client Machine"
        UI[PySide6 Application]
        Config[Configuration Files]
        Logs[Log Files]
    end
    
    subgraph "Hardware Interface"
        Serial[Serial Port]
        USB[USB Connection]
    end
    
    subgraph "Laboratory Equipment"
        Multi[Multi Mechanism]
        RRight[RRight Mechanism]
        Clamp[Clamp Device]
        Pumps[Pump System]
        Valves[Valve System]
    end
    
    UI --> Serial
    Serial --> Multi
    Serial --> RRight
    Serial --> Clamp
    Serial --> Pumps
    Serial --> Valves
    UI --> Config
    UI --> Logs
```

## 7. Диаграмма потоков данных

```mermaid
flowchart TD
    A[User Input] --> B[UI Validation]
    B --> C[Command Processing]
    C --> D[Serial Communication]
    D --> E[Hardware Execution]
    E --> F[Response Processing]
    F --> G[UI Update]
    G --> H[Logging]
    
    I[Configuration] --> J[Settings Manager]
    J --> K[DI Container]
    K --> L[Service Resolution]
    L --> M[Command Execution]
    
    N[Monitoring] --> O[Health Checker]
    O --> P[Performance Monitor]
    P --> Q[Error Alerter]
    Q --> R[UI Notifications]
```

## 8. Диаграмма безопасности

```mermaid
graph TB
    subgraph "Security Layers"
        L1[Input Validation]
        L2[Command Sanitization]
        L3[Serial Port Security]
        L4[Error Handling]
        L5[Logging & Audit]
    end
    
    subgraph "Threats"
        T1[Command Injection]
        T2[Buffer Overflow]
        T3[Resource Exhaustion]
        T4[Information Disclosure]
    end
    
    subgraph "Mitigations"
        M1[Type Checking]
        M2[Input Sanitization]
        M3[Timeout Protection]
        M4[Graceful Degradation]
    end
    
    T1 --> L1
    T2 --> L2
    T3 --> L3
    T4 --> L4
    L1 --> M1
    L2 --> M2
    L3 --> M3
    L4 --> M4
```

## 9. Диаграмма производительности

```mermaid
graph TB
    subgraph "Performance Metrics"
        PM1[Response Time]
        PM2[Throughput]
        PM3[Resource Usage]
        PM4[Error Rate]
    end
    
    subgraph "Optimization Strategies"
        OS1[Connection Pooling]
        OS2[Command Batching]
        OS3[Async Processing]
        OS4[Memory Management]
    end
    
    subgraph "Monitoring Points"
        MP1[Serial Communication]
        MP2[UI Responsiveness]
        MP3[Memory Consumption]
        MP4[CPU Usage]
    end
    
    PM1 --> MP1
    PM2 --> MP2
    PM3 --> MP3
    PM4 --> MP4
    MP1 --> OS1
    MP2 --> OS2
    MP3 --> OS3
    MP4 --> OS4
```

## 10. Диаграмма тестирования

```mermaid
graph TB
    subgraph "Test Types"
        TT1[Unit Tests]
        TT2[Integration Tests]
        TT3[UI Tests]
        TT4[Performance Tests]
    end
    
    subgraph "Test Tools"
        TO1[pytest]
        TO2[pytest-qt]
        TO3[pytest-cov]
        TO4[pytest-benchmark]
    end
    
    subgraph "Test Coverage"
        TC1[Core Logic]
        TC2[UI Components]
        TC3[Serial Communication]
        TC4[Error Handling]
    end
    
    TT1 --> TO1
    TT2 --> TO2
    TT3 --> TO3
    TT4 --> TO4
    TO1 --> TC1
    TO2 --> TC2
    TO3 --> TC3
    TO4 --> TC4
```

---

**Документ**: Техническая архитектура  
**Версия**: 1.0.0  
**Дата**: 2024  
**Статус**: Утверждено

