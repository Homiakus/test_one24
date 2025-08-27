---
title: "Алгоритм: Обработка последовательностей команд"
type: "algorithm_detail"
status: "active"
last_updated: "2024-12-19"
sources:
  - path: "core/sequences/manager.py"
    lines: "L1-L427"
    permalink: "core/sequences/manager.py#L1-L427"
  - path: "core/sequence_manager.py"
    lines: "L314-L500"
    permalink: "core/sequence_manager.py#L314-L500"
  - path: "core/sequences/executor.py"
    lines: "L1-L200"
    permalink: "core/sequences/executor.py#L1-L200"
related: ["docs_algoritm/core/command_execution", "docs_algoritm/core/conditional_logic", "docs_algoritm/utils/threading"]
---

# Обработка последовательностей команд

## Назначение

Алгоритм обработки последовательностей команд отвечает за выполнение списков команд с поддержкой условной логики, обработкой ошибок и управлением состоянием выполнения. Включает парсинг последовательностей, валидацию, выполнение и мониторинг прогресса.

## Входные данные

- **sequence** (List[str]) - список команд для выполнения
- **context** (Dict) - контекст выполнения (флаги, переменные)
- **options** (Dict) - опции выполнения (таймауты, повторные попытки)
- **callbacks** (Dict) - функции обратного вызова для событий

## Алгоритм работы

### 1. Парсинг последовательности
```python
def parse_sequence(sequence: List[str]) -> ParsedSequence:
    parsed_commands = []
    conditional_stack = []
    
    for i, command in enumerate(sequence):
        # Определение типа команды
        command_type = self.detect_command_type(command)
        
        if command_type == CommandType.CONDITIONAL_IF:
            # Обработка условной команды
            condition = self.parse_condition(command)
            conditional_stack.append({
                'type': 'if',
                'condition': condition,
                'start_index': i,
                'active': True
            })
            
        elif command_type == CommandType.CONDITIONAL_ELSE:
            # Обработка else
            if conditional_stack and conditional_stack[-1]['type'] == 'if':
                conditional_stack[-1]['active'] = False
                conditional_stack.append({
                    'type': 'else',
                    'start_index': i,
                    'active': True
                })
                
        elif command_type == CommandType.CONDITIONAL_ENDIF:
            # Завершение условного блока
            if conditional_stack:
                conditional_stack.pop()
                
        # Добавление команды с контекстом
        parsed_commands.append({
            'command': command,
            'type': command_type,
            'index': i,
            'conditional_context': conditional_stack.copy()
        })
    
    return ParsedSequence(commands=parsed_commands)
```

**Логика:**
- Анализ каждой команды в последовательности
- Определение типа команды (обычная, условная, wait)
- Построение стека условных блоков
- Создание контекста для каждой команды

### 2. Валидация последовательности
```python
def validate_sequence(parsed_sequence: ParsedSequence) -> ValidationResult:
    errors = []
    
    # Проверка баланса условных блоков
    if_stack = []
    for cmd in parsed_sequence.commands:
        if cmd['type'] == CommandType.CONDITIONAL_IF:
            if_stack.append(cmd['index'])
        elif cmd['type'] == CommandType.CONDITIONAL_ENDIF:
            if not if_stack:
                errors.append(f"Неожиданный endif в позиции {cmd['index']}")
            else:
                if_stack.pop()
    
    # Проверка незакрытых if блоков
    for if_index in if_stack:
        errors.append(f"Незакрытый if блок начиная с позиции {if_index}")
    
    # Валидация отдельных команд
    for cmd in parsed_sequence.commands:
        if cmd['type'] == CommandType.REGULAR:
            validation = self.validator.validate_command(cmd['command'])
            if not validation.is_valid:
                errors.append(f"Команда {cmd['index']}: {validation.error_message}")
    
    return ValidationResult(len(errors) == 0, errors)
```

**Логика:**
- Проверка баланса if/else/endif блоков
- Валидация синтаксиса каждой команды
- Проверка корректности условных выражений
- Сбор всех ошибок для отчета

### 3. Создание исполнителя последовательности
```python
def create_sequence_executor(parsed_sequence: ParsedSequence) -> SequenceExecutor:
    executor = SequenceExecutor(
        serial_manager=self.serial_manager,
        flag_manager=self.flag_manager,
        parsed_sequence=parsed_sequence
    )
    
    # Настройка callbacks
    executor.set_callbacks(
        on_command_executed=self._on_command_executed,
        on_progress_updated=self._on_progress_updated,
        on_sequence_finished=self._on_sequence_finished,
        on_error_occurred=self._on_error_occurred
    )
    
    return executor
```

**Логика:**
- Создание исполнителя с необходимыми зависимостями
- Настройка функций обратного вызова
- Инициализация состояния выполнения
- Подготовка к асинхронному выполнению

### 4. Выполнение последовательности
```python
def execute_sequence(executor: SequenceExecutor) -> SequenceResult:
    try:
        # Запуск выполнения в отдельном потоке
        executor.start()
        
        # Ожидание завершения с таймаутом
        executor.wait_for_completion(timeout=self.sequence_timeout)
        
        # Получение результата
        result = executor.get_result()
        
        # Обновление статистики
        self._update_execution_stats(result)
        
        return result
        
    except TimeoutError:
        # Прерывание выполнения при таймауте
        executor.cancel()
        return SequenceResult(
            success=False,
            error="Превышен таймаут выполнения последовательности",
            completed_commands=executor.get_completed_count()
        )
    except Exception as e:
        # Обработка неожиданных ошибок
        executor.cancel()
        return SequenceResult(
            success=False,
            error=f"Ошибка выполнения: {str(e)}",
            completed_commands=executor.get_completed_count()
        )
```

**Логика:**
- Запуск выполнения в отдельном потоке
- Мониторинг прогресса выполнения
- Обработка таймаутов и ошибок
- Сбор статистики выполнения

### 5. Обработка условной логики
```python
def handle_conditional_execution(command: Dict, context: Dict) -> bool:
    if command['type'] == CommandType.CONDITIONAL_IF:
        # Вычисление условия
        condition = command['condition']
        result = self.evaluate_condition(condition, context)
        
        # Установка флага выполнения
        command['should_execute'] = result
        return True
        
    elif command['type'] == CommandType.CONDITIONAL_ELSE:
        # Инверсия предыдущего условия
        if command['conditional_context']:
            prev_if = command['conditional_context'][-1]
            command['should_execute'] = not prev_if.get('last_condition', False)
        return True
        
    elif command['type'] == CommandType.CONDITIONAL_ENDIF:
        # Завершение условного блока
        return True
        
    else:
        # Обычная команда - проверяем контекст условности
        should_execute = True
        for cond_block in command['conditional_context']:
            if not cond_block.get('active', True):
                should_execute = False
                break
        
        return should_execute
```

**Логика:**
- Вычисление условий для if блоков
- Обработка else веток
- Управление контекстом выполнения
- Пропуск команд в неактивных блоках

### 6. Мониторинг прогресса
```python
def monitor_progress(executor: SequenceExecutor):
    total_commands = len(executor.parsed_sequence.commands)
    completed_commands = 0
    
    while executor.is_running():
        # Обновление счетчика выполненных команд
        current_completed = executor.get_completed_count()
        if current_completed > completed_commands:
            completed_commands = current_completed
            progress = (completed_commands / total_commands) * 100
            
            # Вызов callback для обновления UI
            if self.on_progress_updated:
                self.on_progress_updated(completed_commands, total_commands)
        
        # Проверка на отмену
        if self.cancellation_token.is_cancelled:
            executor.cancel()
            break
        
        # Пауза для снижения нагрузки
        time.sleep(0.1)
```

**Логика:**
- Отслеживание количества выполненных команд
- Вычисление процента завершения
- Уведомление UI о прогрессе
- Обработка запросов на отмену

## Выходные данные

- **SequenceResult** - результат выполнения последовательности
  - **success** (bool) - успешность выполнения
  - **completed_commands** (int) - количество выполненных команд
  - **total_commands** (int) - общее количество команд
  - **execution_time** (float) - время выполнения
  - **errors** (List[str]) - список ошибок
  - **statistics** (Dict) - статистика выполнения

## Обработка ошибок

### Типы ошибок
- **ValidationError** - ошибки валидации последовательности
- **ExecutionError** - ошибки выполнения команд
- **ConditionalError** - ошибки в условной логике
- **TimeoutError** - превышение времени выполнения
- **CancellationError** - отмена выполнения пользователем

### Стратегии восстановления
```python
def handle_sequence_error(error: Exception, context: Dict) -> RecoveryAction:
    if isinstance(error, ValidationError):
        # Ошибка валидации - остановка выполнения
        return RecoveryAction.STOP
        
    elif isinstance(error, ExecutionError):
        # Ошибка выполнения - попытка повтора или пропуск
        if context.get('retry_on_error', False):
            return RecoveryAction.RETRY
        else:
            return RecoveryAction.SKIP
            
    elif isinstance(error, ConditionalError):
        # Ошибка в условии - пропуск блока
        return RecoveryAction.SKIP_BLOCK
        
    elif isinstance(error, TimeoutError):
        # Таймаут - остановка выполнения
        return RecoveryAction.STOP
        
    else:
        # Неизвестная ошибка - остановка
        return RecoveryAction.STOP
```

## Производительность

### Временная сложность
- **Парсинг:** O(n) где n - количество команд
- **Валидация:** O(n) - линейная проверка
- **Выполнение:** O(n) - последовательное выполнение
- **Мониторинг:** O(1) - константное время на итерацию

### Оптимизации
- **Предварительный парсинг** последовательности
- **Кеширование** результатов валидации
- **Асинхронное выполнение** в отдельном потоке
- **Батчинг** команд для групповой обработки

### Метрики производительности
- **Время парсинга:** < 10ms для 100 команд
- **Время валидации:** < 5ms для 100 команд
- **Пропускная способность:** > 50 команд/сек
- **Задержка мониторинга:** < 100ms

## Примеры использования

### Базовое выполнение последовательности
```python
def execute_simple_sequence():
    sequence = [
        "INIT_DEVICE",
        "SET_MODE 1",
        "GET_STATUS",
        "SET_PARAMETER 123"
    ]
    
    manager = SequenceManager(serial_manager)
    result = manager.execute_sequence(sequence)
    
    if result.success:
        print(f"Выполнено {result.completed_commands} команд")
    else:
        print(f"Ошибка: {result.errors}")
```

### Последовательность с условной логикой
```python
def execute_conditional_sequence():
    sequence = [
        "CHECK_DEVICE_STATUS",
        "if device_ready",
        "  INITIALIZE_DEVICE",
        "  SET_PARAMETERS",
        "else",
        "  RESET_DEVICE",
        "  WAIT 2.0",
        "  INITIALIZE_DEVICE",
        "endif",
        "GET_FINAL_STATUS"
    ]
    
    manager = SequenceManager(serial_manager)
    result = manager.execute_sequence(sequence)
    
    return result
```

### Асинхронное выполнение с callbacks
```python
def execute_async_sequence():
    sequence = ["CMD1", "CMD2", "CMD3"]
    
    def on_progress(current, total):
        print(f"Прогресс: {current}/{total}")
    
    def on_complete(result):
        print(f"Завершено: {result.success}")
    
    manager = SequenceManager(serial_manager)
    manager.set_callbacks(
        on_progress_updated=on_progress,
        on_sequence_finished=on_complete
    )
    
    # Асинхронное выполнение
    future = manager.execute_async(sequence)
    
    # Ожидание результата
    result = future.result(timeout=30.0)
    return result
```

## Интеграция с другими алгоритмами

### Связи с Command Execution
- [[docs_algoritm/core/command_execution|Command Execution]] - выполнение отдельных команд
- Управление очередью команд
- Обработка результатов выполнения

### Связи с Conditional Logic
- [[docs_algoritm/core/conditional_logic|Conditional Logic]] - обработка условных блоков
- Вычисление условий
- Управление контекстом выполнения

### Связи с Threading
- [[docs_algoritm/utils/threading|Threading]] - асинхронное выполнение
- Управление потоками выполнения
- Синхронизация между компонентами

## Тестирование

### Unit тесты
```python
def test_sequence_parsing():
    sequence = ["CMD1", "if condition", "CMD2", "endif"]
    manager = SequenceManager(mock_serial_manager)
    
    parsed = manager.parse_sequence(sequence)
    assert len(parsed.commands) == 4
    assert parsed.commands[1]['type'] == CommandType.CONDITIONAL_IF
```

### Integration тесты
```python
def test_sequence_execution():
    sequence = ["INIT", "SET_MODE 1", "GET_STATUS"]
    manager = SequenceManager(real_serial_manager)
    
    result = manager.execute_sequence(sequence)
    assert result.success
    assert result.completed_commands == 3
```

### Performance тесты
```python
def test_sequence_performance():
    # Создание большой последовательности
    sequence = [f"CMD_{i}" for i in range(100)]
    manager = SequenceManager(serial_manager)
    
    start_time = time.time()
    result = manager.execute_sequence(sequence)
    end_time = time.time()
    
    execution_time = end_time - start_time
    assert execution_time < 10.0  # Максимум 10 секунд
    assert result.completed_commands == 100
```
