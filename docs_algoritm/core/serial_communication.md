---
title: "Алгоритм: Serial Communication"
type: "algorithm_detail"
status: "active"
last_updated: "2024-12-19"
sources:
  - path: "core/serial_manager.py"
    lines: "L1-L940"
    permalink: "core/serial_manager.py#L1-L940"
  - path: "core/interfaces.py"
    lines: "L20-L80"
    permalink: "core/interfaces.py#L20-L80"
related: ["docs_algoritm/core/command_execution", "docs_algoritm/utils/error_handling", "docs_algoritm/utils/threading"]
---

# Serial Communication

## Назначение

Алгоритм Serial Communication отвечает за управление последовательными портами, включая подключение, отправку данных, получение ответов и обработку ошибок связи. Обеспечивает надежную коммуникацию с устройствами через COM/UART интерфейсы.

## Входные данные

- **port** (str) - имя порта (COM4, /dev/ttyUSB0)
- **baudrate** (int) - скорость передачи данных
- **timeout** (float) - таймаут операций чтения/записи
- **data** (bytes/str) - данные для отправки
- **buffer_size** (int) - размер буфера чтения

## Алгоритм работы

### 1. Подключение к порту
```python
def connect(self, port: str, baudrate: int = 115200, timeout: float = 1.0) -> bool:
    try:
        # Проверка доступности порта
        if not self.is_port_available(port):
            raise ConnectionError(f"Порт {port} недоступен")
        
        # Создание объекта Serial
        self.serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout,
            write_timeout=timeout
        )
        
        # Проверка успешности подключения
        if not self.serial.is_open:
            raise ConnectionError("Не удалось открыть порт")
        
        # Инициализация буферов
        self._initialize_buffers()
        
        # Установка флага подключения
        self._is_connected = True
        self._port_info = self._get_port_info()
        
        return True
        
    except Exception as e:
        self.logger.error(f"Ошибка подключения к {port}: {e}")
        self._is_connected = False
        return False
```

**Логика:**
- Проверка доступности порта в системе
- Создание объекта Serial с заданными параметрами
- Валидация успешности открытия порта
- Инициализация внутренних буферов
- Обновление состояния подключения

### 2. Отправка данных
```python
def send_data(self, data: Union[str, bytes]) -> bool:
    try:
        # Проверка подключения
        if not self.is_connected():
            raise ConnectionError("Нет подключения к порту")
        
        # Преобразование данных в bytes
        if isinstance(data, str):
            data_bytes = data.encode('utf-8')
        else:
            data_bytes = data
        
        # Очистка входного буфера перед отправкой
        self.serial.reset_input_buffer()
        
        # Отправка данных
        bytes_written = self.serial.write(data_bytes)
        
        # Принудительная отправка (flush)
        self.serial.flush()
        
        # Проверка успешности отправки
        if bytes_written != len(data_bytes):
            raise IOError(f"Отправлено {bytes_written} из {len(data_bytes)} байт")
        
        # Логирование отправки
        self.logger.debug(f"Отправлено {bytes_written} байт: {data_bytes}")
        
        return True
        
    except Exception as e:
        self.logger.error(f"Ошибка отправки данных: {e}")
        return False
```

**Логика:**
- Проверка состояния подключения
- Преобразование данных в байты
- Очистка входного буфера
- Отправка данных с проверкой количества
- Принудительная отправка для гарантии передачи

### 3. Чтение данных
```python
def read_data(self, timeout: Optional[float] = None) -> Optional[bytes]:
    try:
        # Установка таймаута
        original_timeout = self.serial.timeout
        if timeout is not None:
            self.serial.timeout = timeout
        
        # Ожидание данных
        if self.serial.in_waiting == 0:
            # Блокирующее чтение с таймаутом
            data = self.serial.read()
            if not data:
                return None  # Таймаут
        
        # Чтение всех доступных данных
        available = self.serial.in_waiting
        if available > 0:
            data = self.serial.read(available)
            self.logger.debug(f"Прочитано {len(data)} байт")
            return data
        
        return None
        
    except Exception as e:
        self.logger.error(f"Ошибка чтения данных: {e}")
        return None
    finally:
        # Восстановление оригинального таймаута
        if timeout is not None:
            self.serial.timeout = original_timeout
```

**Логика:**
- Настройка таймаута для операции чтения
- Проверка наличия данных в буфере
- Блокирующее чтение при отсутствии данных
- Чтение всех доступных данных
- Восстановление настроек таймаута

### 4. Обработка прерываний
```python
def handle_interrupt(self):
    """Обработка прерывания работы с портом"""
    try:
        # Установка флага прерывания
        self._interrupted = True
        
        # Остановка активных потоков
        if hasattr(self, '_read_thread') and self._read_thread.is_alive():
            self._read_thread.stop()
        
        # Закрытие порта
        if self.serial and self.serial.is_open:
            self.serial.close()
        
        # Сброс состояния
        self._is_connected = False
        self._port_info = None
        
        self.logger.info("Порт закрыт по прерыванию")
        
    except Exception as e:
        self.logger.error(f"Ошибка при обработке прерывания: {e}")
```

**Логика:**
- Установка флага прерывания
- Остановка активных потоков чтения
- Безопасное закрытие порта
- Сброс состояния подключения
- Логирование операции

### 5. Мониторинг состояния порта
```python
def monitor_port_status(self):
    """Мониторинг состояния порта в отдельном потоке"""
    while not self._interrupted:
        try:
            # Проверка состояния подключения
            if self.serial and self.serial.is_open:
                # Проверка доступности порта
                if not self.is_port_available(self.serial.port):
                    self.logger.warning(f"Порт {self.serial.port} стал недоступен")
                    self._handle_port_disconnection()
                    break
                
                # Обновление статистики
                self._update_port_statistics()
            
            # Пауза между проверками
            time.sleep(1.0)
            
        except Exception as e:
            self.logger.error(f"Ошибка мониторинга порта: {e}")
            time.sleep(5.0)  # Увеличенная пауза при ошибке
```

**Логика:**
- Циклическая проверка состояния порта
- Обнаружение отключения устройства
- Обновление статистики использования
- Обработка ошибок мониторинга
- Graceful shutdown при прерывании

### 6. Управление буферами
```python
def _initialize_buffers(self):
    """Инициализация буферов для чтения и записи"""
    # Очистка существующих буферов
    if self.serial:
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
    
    # Инициализация внутренних буферов
    self._input_buffer = bytearray()
    self._output_buffer = bytearray()
    self._buffer_lock = threading.Lock()
    
    # Настройка размеров буферов
    self._max_buffer_size = 8192  # 8KB
    self._min_read_size = 1
```

**Логика:**
- Очистка системных буферов порта
- Создание внутренних буферов
- Инициализация блокировок для thread-safety
- Настройка параметров буферизации

## Выходные данные

- **ConnectionStatus** - статус подключения
  - **is_connected** (bool) - состояние подключения
  - **port_info** (Dict) - информация о порте
  - **statistics** (Dict) - статистика использования
  - **error_count** (int) - количество ошибок

- **ReadResult** - результат чтения
  - **data** (bytes) - прочитанные данные
  - **bytes_read** (int) - количество прочитанных байт
  - **timestamp** (float) - время чтения
  - **error** (str) - описание ошибки (если есть)

## Обработка ошибок

### Типы ошибок
- **PortNotFoundError** - порт не найден в системе
- **PermissionError** - недостаток прав доступа к порту
- **SerialException** - ошибки библиотеки pyserial
- **TimeoutError** - превышение времени ожидания
- **ConnectionLostError** - потеря соединения с устройством

### Стратегии восстановления
```python
def handle_communication_error(self, error: Exception) -> RecoveryAction:
    if isinstance(error, PortNotFoundError):
        # Порт недоступен - попытка найти альтернативный
        return RecoveryAction.RETRY_WITH_DIFFERENT_PORT
        
    elif isinstance(error, PermissionError):
        # Проблемы с правами - уведомление пользователя
        return RecoveryAction.NOTIFY_USER
        
    elif isinstance(error, SerialException):
        # Ошибка Serial - переподключение
        return RecoveryAction.RECONNECT
        
    elif isinstance(error, TimeoutError):
        # Таймаут - увеличение времени ожидания
        return RecoveryAction.INCREASE_TIMEOUT
        
    elif isinstance(error, ConnectionLostError):
        # Потеря соединения - переподключение
        return RecoveryAction.RECONNECT
        
    else:
        # Неизвестная ошибка - логирование и остановка
        return RecoveryAction.STOP
```

## Производительность

### Временная сложность
- **Подключение:** O(1) - константное время
- **Отправка данных:** O(n) где n - размер данных
- **Чтение данных:** O(m) где m - количество прочитанных байт
- **Мониторинг:** O(1) - константное время на итерацию

### Оптимизации
- **Буферизация** данных для снижения количества системных вызовов
- **Асинхронное чтение** в отдельном потоке
- **Batch операции** для групповой отправки данных
- **Кеширование** информации о портах

### Метрики производительности
- **Скорость передачи:** До baudrate бит/сек
- **Задержка отправки:** < 10ms для небольших данных
- **Задержка чтения:** < 50ms при наличии данных
- **Надежность:** > 99.9% успешных операций

## Примеры использования

### Базовое подключение и отправка
```python
def basic_communication():
    serial_mgr = SerialManager()
    
    # Подключение к порту
    if serial_mgr.connect("COM4", baudrate=115200):
        # Отправка команды
        success = serial_mgr.send_data("GET_STATUS\n")
        
        if success:
            # Чтение ответа
            response = serial_mgr.read_data(timeout=1.0)
            if response:
                print(f"Ответ: {response.decode('utf-8')}")
        
        # Отключение
        serial_mgr.disconnect()
```

### Асинхронное чтение
```python
def async_reading():
    serial_mgr = SerialManager()
    
    def data_handler(data):
        print(f"Получены данные: {data}")
    
    # Настройка обработчика данных
    serial_mgr.set_data_handler(data_handler)
    
    # Подключение и запуск асинхронного чтения
    if serial_mgr.connect("COM4"):
        serial_mgr.start_async_reading()
        
        # Основная работа
        time.sleep(10)
        
        # Остановка и отключение
        serial_mgr.stop_async_reading()
        serial_mgr.disconnect()
```

### Обработка ошибок
```python
def robust_communication():
    serial_mgr = SerialManager()
    
    try:
        # Попытка подключения с обработкой ошибок
        if not serial_mgr.connect("COM4"):
            # Попытка альтернативного порта
            available_ports = serial_mgr.get_available_ports()
            if available_ports:
                serial_mgr.connect(available_ports[0])
        
        # Отправка с повторными попытками
        for attempt in range(3):
            if serial_mgr.send_data("COMMAND"):
                break
            time.sleep(0.5)
        
    except Exception as e:
        print(f"Ошибка связи: {e}")
    finally:
        serial_mgr.disconnect()
```

## Интеграция с другими алгоритмами

### Связи с Command Execution
- [[docs_algoritm/core/command_execution|Command Execution]] - отправка команд через порт
- Получение ответов от устройства
- Обработка результатов выполнения

### Связи с Error Handling
- [[docs_algoritm/utils/error_handling|Error Handling]] - обработка ошибок связи
- Стратегии восстановления соединения
- Логирование ошибок коммуникации

### Связи с Threading
- [[docs_algoritm/utils/threading|Threading]] - асинхронное чтение данных
- Управление потоками мониторинга
- Синхронизация операций чтения/записи

## Тестирование

### Unit тесты
```python
def test_serial_connection():
    # Мок Serial объекта
    mock_serial = MockSerial()
    serial_mgr = SerialManager()
    serial_mgr.serial = mock_serial
    
    # Тест подключения
    result = serial_mgr.connect("COM4")
    assert result is True
    assert serial_mgr.is_connected()
    
    # Тест отправки данных
    result = serial_mgr.send_data("TEST")
    assert result is True
    assert mock_serial.write_called
```

### Integration тесты
```python
def test_serial_integration():
    # Тест с реальным устройством
    with SerialDevice() as device:
        serial_mgr = SerialManager()
        
        # Подключение к тестовому устройству
        assert serial_mgr.connect(device.port)
        
        # Отправка и получение данных
        serial_mgr.send_data("ECHO test")
        response = serial_mgr.read_data(timeout=1.0)
        
        assert response is not None
        assert b"test" in response
```

### Performance тесты
```python
def test_serial_performance():
    serial_mgr = SerialManager()
    
    # Тест производительности передачи
    test_data = b"x" * 1024  # 1KB данных
    
    start_time = time.time()
    
    for i in range(100):
        serial_mgr.send_data(test_data)
    
    end_time = time.time()
    transfer_time = end_time - start_time
    
    # Проверка производительности
    throughput = (100 * 1024) / transfer_time  # байт/сек
    assert throughput > 10000  # Минимум 10KB/сек
```
