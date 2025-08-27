---
title: "Алгоритм: Выполнение команд"
type: "algorithm_detail"
status: "active"
last_updated: "2024-12-19"
sources:
  - path: "core/command_executor.py"
    lines: "L1-L200"
    permalink: "core/command_executor.py#L1-L200"
  - path: "core/serial_manager.py"
    lines: "L200-L400"
    permalink: "core/serial_manager.py#L200-L400"
  - path: "core/interfaces.py"
    lines: "L100-L200"
    permalink: "core/interfaces.py#L100-L200"
related: ["docs_algoritm/core/serial_communication", "docs_algoritm/utils/validation", "docs_algoritm/utils/error_handling"]
---

# Выполнение команд

## Назначение

Алгоритм выполнения команд отвечает за отправку команд на устройство через последовательный порт, получение ответов и обработку результатов. Включает валидацию команд, управление очередью выполнения и обработку ошибок.

## Входные данные

- **command** (str) - команда для отправки
- **timeout** (float) - таймаут ожидания ответа (по умолчанию 1.0 сек)
- **retry_count** (int) - количество попыток повторной отправки
- **priority** (int) - приоритет команды в очереди

## Алгоритм работы

### 1. Валидация команды
```python
def validate_command(command: str) -> ValidationResult:
    # Проверка синтаксиса команды
    if not command or not command.strip():
        return ValidationResult(False, "Пустая команда")
    
    # Проверка длины команды
    if len(command) > MAX_COMMAND_LENGTH:
        return ValidationResult(False, "Команда слишком длинная")
    
    # Проверка на запрещенные символы
    if contains_forbidden_chars(command):
        return ValidationResult(False, "Запрещенные символы")
    
    return ValidationResult(True, "")
```

**Логика:**
- Проверка на пустые команды
- Валидация длины команды (максимум 1024 символа)
- Проверка на запрещенные символы (null bytes, control chars)
- Валидация формата команды по шаблонам

### 2. Добавление в очередь выполнения
```python
def add_to_execution_queue(command: str, priority: int = 0):
    with self._queue_lock:
        queue_item = CommandQueueItem(
            command=command,
            priority=priority,
            timestamp=time.time(),
            retry_count=0
        )
        self._command_queue.put(queue_item)
        self._queue_condition.notify()
```

**Логика:**
- Создание объекта команды с метаданными
- Добавление в приоритетную очередь
- Уведомление исполнителя о новой команде
- Thread-safe операции с блокировками

### 3. Отправка команды через Serial
```python
def send_command_through_serial(command: str) -> bool:
    try:
        # Проверка подключения
        if not self.serial_manager.is_connected():
            raise ConnectionError("Нет подключения к устройству")
        
        # Отправка команды
        bytes_sent = self.serial_manager.write(command.encode('utf-8'))
        
        # Проверка успешности отправки
        if bytes_sent != len(command.encode('utf-8')):
            raise IOError("Неполная отправка команды")
        
        return True
        
    except Exception as e:
        self.logger.error(f"Ошибка отправки команды: {e}")
        return False
```

**Логика:**
- Проверка состояния подключения
- Кодирование команды в UTF-8
- Отправка через SerialManager
- Проверка количества отправленных байт
- Обработка ошибок отправки

### 4. Ожидание ответа
```python
def wait_for_response(timeout: float) -> Optional[str]:
    start_time = time.time()
    response_buffer = ""
    
    while (time.time() - start_time) < timeout:
        # Чтение доступных данных
        if self.serial_manager.in_waiting > 0:
            chunk = self.serial_manager.read(self.serial_manager.in_waiting)
            response_buffer += chunk.decode('utf-8', errors='ignore')
            
            # Проверка на завершение ответа
            if self.is_response_complete(response_buffer):
                return response_buffer
        
        # Небольшая пауза для снижения нагрузки на CPU
        time.sleep(0.01)
    
    return None  # Таймаут
```

**Логика:**
- Цикл ожидания с таймаутом
- Пошаговое чтение данных из буфера
- Декодирование UTF-8 с обработкой ошибок
- Проверка завершения ответа по маркерам
- Оптимизация нагрузки на CPU

### 5. Обработка ответа
```python
def process_response(response: str) -> CommandResult:
    # Очистка ответа от лишних символов
    cleaned_response = self.clean_response(response)
    
    # Парсинг ответа
    parsed_response = self.parse_response(cleaned_response)
    
    # Проверка на ошибки в ответе
    if self.has_error_in_response(parsed_response):
        return CommandResult(
            success=False,
            response=parsed_response,
            error="Ошибка в ответе устройства"
        )
    
    return CommandResult(
        success=True,
        response=parsed_response,
        error=None
    )
```

**Логика:**
- Очистка от управляющих символов
- Парсинг структурированного ответа
- Проверка на ошибки устройства
- Создание результата выполнения

### 6. Повторные попытки при ошибках
```python
def retry_command(command: str, max_retries: int = 3) -> CommandResult:
    for attempt in range(max_retries):
        try:
            result = self.execute_single_command(command)
            if result.success:
                return result
            
            # Логирование неудачной попытки
            self.logger.warning(f"Попытка {attempt + 1} неудачна: {result.error}")
            
            # Пауза перед повторной попыткой
            time.sleep(0.5 * (attempt + 1))
            
        except Exception as e:
            self.logger.error(f"Ошибка в попытке {attempt + 1}: {e}")
    
    return CommandResult(success=False, error="Превышено количество попыток")
```

**Логика:**
- Цикл повторных попыток
- Экспоненциальная задержка между попытками
- Логирование каждой неудачной попытки
- Возврат результата после всех попыток

## Выходные данные

- **CommandResult** - результат выполнения команды
  - **success** (bool) - успешность выполнения
  - **response** (str) - ответ от устройства
  - **error** (str) - описание ошибки (если есть)
  - **execution_time** (float) - время выполнения
  - **attempts** (int) - количество попыток

## Обработка ошибок

### Типы ошибок
- **ValidationError** - ошибки валидации команды
- **ConnectionError** - проблемы с подключением
- **TimeoutError** - превышение времени ожидания
- **SerialError** - ошибки последовательного порта
- **DeviceError** - ошибки устройства

### Стратегии восстановления
```python
def handle_execution_error(error: Exception, command: str) -> CommandResult:
    if isinstance(error, ConnectionError):
        # Попытка переподключения
        self.reconnect_serial()
        return self.retry_command(command)
    
    elif isinstance(error, TimeoutError):
        # Увеличение таймаута для следующей попытки
        return self.execute_with_extended_timeout(command)
    
    elif isinstance(error, SerialError):
        # Сброс состояния порта
        self.reset_serial_port()
        return self.retry_command(command)
    
    else:
        # Логирование неизвестной ошибки
        self.logger.error(f"Неизвестная ошибка: {error}")
        return CommandResult(success=False, error=str(error))
```

## Производительность

### Временная сложность
- **Валидация:** O(n) где n - длина команды
- **Отправка:** O(1) - константное время
- **Ожидание ответа:** O(t) где t - таймаут
- **Обработка ответа:** O(m) где m - длина ответа

### Оптимизации
- **Буферизация** команд в очереди
- **Асинхронное выполнение** в отдельных потоках
- **Кеширование** результатов валидации
- **Батчинг** команд для групповой отправки

### Метрики производительности
- **Среднее время выполнения:** < 100ms
- **Пропускная способность:** > 100 команд/сек
- **Задержка очереди:** < 50ms
- **Успешность выполнения:** > 95%

## Примеры использования

### Базовое выполнение команды
```python
def execute_simple_command():
    executor = CommandExecutor(serial_manager)
    
    # Выполнение команды
    result = executor.execute_command("GET_STATUS")
    
    if result.success:
        print(f"Статус: {result.response}")
    else:
        print(f"Ошибка: {result.error}")
```

### Выполнение с обработкой ошибок
```python
def execute_with_error_handling():
    executor = CommandExecutor(serial_manager)
    
    try:
        result = executor.execute_command(
            command="SET_PARAMETER 123",
            timeout=2.0,
            retry_count=3
        )
        
        if result.success:
            return result.response
        else:
            handle_command_error(result.error)
            
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise
```

### Асинхронное выполнение
```python
def execute_async_commands():
    executor = CommandExecutor(serial_manager)
    
    # Добавление команд в очередь
    commands = ["CMD1", "CMD2", "CMD3"]
    futures = []
    
    for cmd in commands:
        future = executor.execute_async(cmd)
        futures.append(future)
    
    # Ожидание результатов
    results = []
    for future in futures:
        result = future.result(timeout=5.0)
        results.append(result)
    
    return results
```

## Интеграция с другими алгоритмами

### Связи с Serial Communication
- [[docs_algoritm/core/serial_communication|Serial Communication]] - отправка через порт
- Управление состоянием подключения
- Обработка данных от устройства

### Связи с Validation
- [[docs_algoritm/utils/validation|Validation]] - валидация команд
- Проверка синтаксиса и безопасности
- Валидация параметров команд

### Связи с Error Handling
- [[docs_algoritm/utils/error_handling|Error Handling]] - обработка ошибок
- Стратегии восстановления
- Логирование и мониторинг

## Тестирование

### Unit тесты
```python
def test_command_execution():
    # Мок SerialManager
    mock_serial = MockSerialManager()
    executor = CommandExecutor(mock_serial)
    
    # Тест успешного выполнения
    result = executor.execute_command("TEST_CMD")
    assert result.success
    assert result.response == "OK"
    
    # Тест ошибки валидации
    result = executor.execute_command("")
    assert not result.success
    assert "пустая команда" in result.error.lower()
```

### Integration тесты
```python
def test_command_integration():
    # Тест с реальным устройством
    with SerialDevice() as device:
        executor = CommandExecutor(device.serial_manager)
        
        # Тест последовательности команд
        commands = ["INIT", "SET_MODE 1", "GET_STATUS"]
        results = []
        
        for cmd in commands:
            result = executor.execute_command(cmd)
            results.append(result)
            assert result.success
        
        return results
```

### Performance тесты
```python
def test_command_performance():
    executor = CommandExecutor(serial_manager)
    
    # Тест производительности
    start_time = time.time()
    
    for i in range(100):
        result = executor.execute_command(f"CMD_{i}")
        assert result.success
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Проверка производительности
    assert execution_time < 10.0  # Максимум 10 секунд для 100 команд
    assert (100 / execution_time) > 10  # Минимум 10 команд/сек
```
