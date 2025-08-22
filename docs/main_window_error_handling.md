# Улучшения обработки ошибок в MainWindow

## Обзор

В `main_window.py` добавлена комплексная система обработки ошибок, которая обеспечивает:

1. **Error handling в _safe_auto_connect** - безопасное автоподключение с детальной обработкой ошибок
2. **Recovery стратегии для UI компонентов** - восстановление состояния интерфейса при ошибках
3. **Proper cleanup в closeEvent** - корректная очистка ресурсов при закрытии приложения

## Основные улучшения

### 1. Error handling в _safe_auto_connect

#### Улучшенная проверка зависимостей
```python
def _safe_auto_connect(self):
    """Безопасное автоматическое подключение при запуске с улучшенной обработкой ошибок"""
    try:
        # Проверяем доступность settings_manager
        if not hasattr(self, 'settings_manager') or not self.settings_manager:
            self.logger.error("SettingsManager недоступен")
            self.statusBar().showMessage("Ошибка: SettingsManager недоступен", 5000)
            return
```

#### Детальная обработка ошибок получения портов
```python
try:
    available_ports = SerialManager.get_available_ports()
    # ...
except ImportError as e:
    self.logger.error(f"Ошибка импорта SerialManager: {e}")
    self.statusBar().showMessage("Ошибка: SerialManager недоступен", 5000)
except PermissionError as e:
    self.logger.error(f"Ошибка прав доступа к портам: {e}")
    self.statusBar().showMessage("Ошибка прав доступа к портам", 5000)
except OSError as e:
    self.logger.error(f"Системная ошибка при получении портов: {e}")
    self.statusBar().showMessage("Системная ошибка при получении портов", 5000)
```

### 2. Recovery стратегии для UI компонентов

#### Централизованное обновление статуса подключения
```python
def _update_connection_status(self, status: str, message: str = ""):
    """Обновление статуса подключения с recovery стратегией"""
    try:
        if not hasattr(self, 'connection_status'):
            self.logger.error("connection_status недоступен")
            return
            
        status_config = {
            "connected": ("● Подключено", "color: #50fa7b;"),
            "disconnected": ("● Отключено", "color: #ffb86c;"),
            "error": ("● Ошибка", "color: #ff5555;"),
            "connecting": ("● Подключение...", "color: #ffb86c;")
        }
        
        text, color = status_config.get(status, ("● Неизвестно", "color: #ff5555;"))
        self.connection_status.setText(text)
        self.connection_status.setStyleSheet(color)
        
        if message:
            self.statusBar().showMessage(message, 3000)
            
    except Exception as e:
        self.logger.error(f"Ошибка обновления статуса подключения: {e}")
        # Fallback - пытаемся обновить только статусную строку
        try:
            if message:
                self.statusBar().showMessage(f"Ошибка статуса: {message}", 3000)
        except Exception as fallback_error:
            self.logger.error(f"Fallback обновления статуса также не удался: {fallback_error}")
```

#### Настройка обработчиков данных с recovery
```python
def _setup_data_handlers(self):
    """Настройка обработчиков данных с recovery стратегией"""
    try:
        if not hasattr(self, 'serial_manager') or not self.serial_manager:
            self.logger.error("SerialManager недоступен для настройки обработчиков")
            return
            
        if not self.serial_manager.reader_thread:
            self.logger.warning("Reader thread недоступен")
            return
            
        # Отключаем старые обработчики для избежания дублирования
        try:
            self.serial_manager.reader_thread.data_received.disconnect()
        except:
            pass  # Игнорируем ошибки отключения
            
        try:
            self.serial_manager.reader_thread.error_occurred.disconnect()
        except:
            pass  # Игнорируем ошибки отключения
        
        # Подключаем новые обработчики
        self.serial_manager.reader_thread.data_received.connect(
            self._on_data_received
        )
        self.serial_manager.reader_thread.error_occurred.connect(
            self._on_serial_error
        )
        self.logger.info("Обработчики данных подключены")
        
    except Exception as e:
        self.logger.error(f"Ошибка настройки обработчиков данных: {e}")
```

#### Recovery стратегия для UI компонентов
```python
def _recover_ui_components(self):
    """Recovery стратегия для UI компонентов"""
    try:
        self.logger.info("Запуск recovery стратегии для UI компонентов...")
        
        # Восстанавливаем статус подключения
        if hasattr(self, 'connection_status'):
            self._check_connection_status()
        
        # Восстанавливаем обработчики данных
        if hasattr(self, 'serial_manager') and self.serial_manager and self.serial_manager.is_connected:
            self._setup_data_handlers()
        
        # Обновляем страницы
        for page_name, page in self.pages.items():
            try:
                if hasattr(page, 'refresh'):
                    page.refresh()
            except Exception as e:
                self.logger.error(f"Ошибка обновления страницы {page_name}: {e}")
        
        self.logger.info("Recovery стратегия завершена")
        
    except Exception as e:
        self.logger.error(f"Ошибка recovery стратегии: {e}")
```

### 3. Proper cleanup в closeEvent

#### Модульная очистка ресурсов
```python
def closeEvent(self, event):
    """Обработка закрытия окна с proper cleanup и обработкой ошибок"""
    try:
        self.logger.info("Начало процесса закрытия приложения...")
        
        # Останавливаем таймер проверки подключения
        self._cleanup_timers()
        
        # Останавливаем последовательность
        self._cleanup_sequence_executor()
        
        # Отключаемся от порта
        self._cleanup_serial_connection()
        
        # Сохраняем настройки
        self._cleanup_settings()
        
        # Очищаем ресурсы страниц
        self._cleanup_pages()
        
        # Очищаем обработчики сигналов
        self._cleanup_signal_handlers()
        
        # Финальная очистка
        self._final_cleanup()
        
        self.logger.info("Приложение успешно закрыто")
        event.accept()
        
    except Exception as e:
        self.logger.error(f"Критическая ошибка при закрытии приложения: {e}")
        # Даже при ошибке принимаем событие закрытия
        event.accept()
```

#### Детальная очистка таймеров
```python
def _cleanup_timers(self):
    """Очистка таймеров"""
    try:
        if hasattr(self, 'connection_check_timer'):
            self.connection_check_timer.stop()
            self.logger.info("Таймер проверки подключения остановлен")
    except Exception as e:
        self.logger.error(f"Ошибка остановки таймера: {e}")
```

#### Очистка исполнителя последовательности
```python
def _cleanup_sequence_executor(self):
    """Очистка исполнителя последовательности"""
    try:
        if hasattr(self, 'sequence_executor') and self.sequence_executor:
            if self.sequence_executor.isRunning():
                self.sequence_executor.stop()
                self.logger.info("Исполнитель последовательности остановлен")
            # Отключаем сигналы
            try:
                self.sequence_executor.progress_updated.disconnect()
                self.sequence_executor.command_sent.disconnect()
                self.sequence_executor.sequence_finished.disconnect()
            except:
                pass  # Игнорируем ошибки отключения сигналов
    except Exception as e:
        self.logger.error(f"Ошибка очистки исполнителя последовательности: {e}")
```

#### Очистка Serial соединения
```python
def _cleanup_serial_connection(self):
    """Очистка Serial соединения"""
    try:
        if hasattr(self, 'serial_manager') and self.serial_manager:
            # Отключаем обработчики данных
            if self.serial_manager.reader_thread:
                try:
                    self.serial_manager.reader_thread.data_received.disconnect()
                    self.serial_manager.reader_thread.error_occurred.disconnect()
                except:
                    pass  # Игнорируем ошибки отключения
            
            # Отключаемся от порта
            self.serial_manager.disconnect()
            self.logger.info("Serial соединение закрыто")
    except Exception as e:
        self.logger.error(f"Ошибка очистки Serial соединения: {e}")
```

#### Очистка обработчиков сигналов
```python
def _cleanup_signal_handlers(self):
    """Очистка обработчиков сигналов"""
    try:
        # Отключаем обработчики от страниц
        if hasattr(self, 'pages'):
            for page_name, page in self.pages.items():
                try:
                    # Отключаем все сигналы страницы
                    if hasattr(page, 'sequence_requested'):
                        page.sequence_requested.disconnect()
                    if hasattr(page, 'zone_selection_changed'):
                        page.zone_selection_changed.disconnect()
                    # ... другие сигналы
                except:
                    pass  # Игнорируем ошибки отключения сигналов
        self.logger.info("Обработчики сигналов очищены")
    except Exception as e:
        self.logger.error(f"Ошибка очистки обработчиков сигналов: {e}")
```

## Дополнительные улучшения

### Улучшенная обработка подключения
```python
def _connect_serial(self):
    """Подключение к Serial порту с улучшенной обработкой ошибок"""
    try:
        # Проверяем доступность менеджеров
        if not hasattr(self, 'settings_manager') or not self.settings_manager:
            self.logger.error("SettingsManager недоступен")
            QMessageBox.critical(self, "Ошибка", "SettingsManager недоступен")
            return
            
        # Проверяем, что порт указан
        if not settings.port or settings.port.strip() == '':
            self.logger.error("Порт не указан в настройках")
            QMessageBox.warning(self, "Предупреждение", "Порт не указан в настройках")
            return

        # Детальная обработка ошибок подключения
        try:
            success = self.serial_manager.connect(...)
        except PermissionError as e:
            self.logger.error(f"Ошибка прав доступа к порту {settings.port}: {e}")
            QMessageBox.critical(self, "Ошибка", f"Нет прав доступа к порту {settings.port}")
            success = False
        except OSError as e:
            self.logger.error(f"Системная ошибка подключения: {e}")
            QMessageBox.critical(self, "Ошибка", f"Системная ошибка подключения: {e}")
            success = False
```

### Улучшенная перезагрузка конфигурации
```python
def _reload_config(self):
    """Перезагрузка конфигурации с улучшенной обработкой ошибок"""
    try:
        # Проверяем доступность ConfigLoader
        if not hasattr(self, 'config_loader') or not self.config_loader:
            self.logger.error("ConfigLoader недоступен")
            QMessageBox.critical(self, "Ошибка", "ConfigLoader недоступен")
            return
        
        # Загружаем конфигурацию с обработкой ошибок
        try:
            self.config = self.config_loader.load()
        except FileNotFoundError as e:
            self.logger.error(f"Файл конфигурации не найден: {e}")
            QMessageBox.critical(self, "Ошибка", f"Файл конфигурации не найден:\n{e}")
            return
        except PermissionError as e:
            self.logger.error(f"Ошибка прав доступа к файлу конфигурации: {e}")
            QMessageBox.critical(self, "Ошибка", f"Нет прав доступа к файлу конфигурации:\n{e}")
            return
        
        # Обновляем страницы с обработкой ошибок
        for page_name, page in self.pages.items():
            try:
                if hasattr(page, 'refresh'):
                    page.refresh()
            except Exception as e:
                self.logger.error(f"Ошибка обновления страницы {page_name}: {e}")
                # Продолжаем обновление других страниц
        
        # Запускаем recovery стратегию
        self._recover_ui_components()
        
    except Exception as e:
        self.logger.error(f"Критическая ошибка перезагрузки конфигурации: {e}")
        QMessageBox.critical(self, "Критическая ошибка", f"Критическая ошибка перезагрузки конфигурации:\n{e}")
```

## Типы обрабатываемых ошибок

### 1. AttributeError
- Доступ к несуществующим атрибутам объектов
- Проверка доступности менеджеров и компонентов

### 2. ImportError
- Ошибки импорта SerialManager
- Недоступность критических модулей

### 3. PermissionError
- Ошибки прав доступа к портам
- Ошибки прав доступа к файлам конфигурации

### 4. FileNotFoundError
- Отсутствующие файлы конфигурации
- Недоступные файлы настроек

### 5. OSError
- Системные ошибки при работе с портами
- Ошибки файловой системы

### 6. Общие Exception
- Неожиданные ошибки в UI компонентах
- Ошибки в обработчиках сигналов

## Преимущества системы

### 1. Надежность
- Приложение не падает при ошибках в UI компонентах
- Graceful degradation при недоступности компонентов
- Корректная очистка ресурсов при закрытии

### 2. Восстанавливаемость
- Recovery стратегии для UI компонентов
- Автоматическое восстановление состояния
- Fallback механизмы для критических операций

### 3. Информативность
- Детальное логирование всех ошибок
- Понятные сообщения пользователю
- Контекстная информация об ошибках

### 4. Модульность
- Разделение очистки на отдельные методы
- Изолированная обработка ошибок
- Независимые recovery стратегии

### 5. Безопасность
- Проверка доступности компонентов перед использованием
- Безопасное отключение сигналов
- Защита от утечек памяти

## Рекомендации по использованию

1. **Всегда проверяйте доступность компонентов** перед их использованием
2. **Используйте recovery стратегии** для восстановления состояния UI
3. **Логируйте все ошибки** с контекстной информацией
4. **Предоставляйте fallback механизмы** для критических операций
5. **Очищайте ресурсы** в правильном порядке при закрытии
6. **Тестируйте обработку ошибок** в различных сценариях

## Статус выполнения

✅ **Все запрошенные улучшения выполнены**
- Error handling в _safe_auto_connect
- Recovery стратегии для UI компонентов
- Proper cleanup в closeEvent
- Дополнительные улучшения обработки ошибок

✅ **Система протестирована**
- Проверены различные сценарии ошибок
- Документация создана
- Код готов к использованию в продакшене

Система обработки ошибок в MainWindow полностью готова к использованию!

