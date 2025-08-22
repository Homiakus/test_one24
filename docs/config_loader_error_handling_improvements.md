# Улучшения обработки ошибок в config_loader.py

## Обзор

В файле `config/config_loader.py` были реализованы комплексные улучшения обработки ошибок для обеспечения надежной загрузки и валидации TOML конфигурации.

## Ключевые улучшения

### 1. Валидация TOML структуры

#### Основная валидация (`_validate_config_structure`)
- Проверка наличия обязательных секций: `buttons`, `sequences`, `serial_default`, `sequence_keywords`
- Детальная валидация каждой секции
- Логирование предупреждений для отсутствующих секций

#### Валидация секций
- **`_validate_buttons_section`**: Проверка типов данных и пустых значений
- **`_validate_sequences_section`**: Валидация структуры последовательностей
- **`_validate_serial_default_section`**: Проверка обязательных полей и типов
- **`_validate_sequence_keywords_section`**: Валидация ключевых слов
- **`_validate_wizard_section`**: Проверка конфигурации мастера

### 2. Backup и Recovery системы

#### Создание резервных копий (`_create_backup`)
```python
def _create_backup(self):
    """Создание резервной копии конфигурации"""
    try:
        if not self.config_path.exists():
            self.logger.info("Файл конфигурации не существует, резервная копия не требуется")
            return True
        
        backup_dir = self.config_path.parent / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{self.config_path.stem}_backup_{timestamp}.toml"
        backup_path = backup_dir / backup_name
        
        # Копируем файл
        import shutil
        shutil.copy2(self.config_path, backup_path)
        
        self.logger.info(f"Резервная копия создана: {backup_path}")
        
        # Удаляем старые резервные копии (оставляем только 5 последних)
        self._cleanup_old_backups(backup_dir)
        
        return True
        
    except PermissionError as e:
        self.logger.error(f"Ошибка прав доступа при создании резервной копии: {e}")
        return False
    except OSError as e:
        self.logger.error(f"Ошибка ОС при создании резервной копии: {e}")
        return False
    except Exception as e:
        self.logger.error(f"Неожиданная ошибка создания резервной копии: {e}")
        return False
```

#### Восстановление из резервной копии (`_recover_from_backup`)
- Автоматический поиск последней резервной копии
- Восстановление файла конфигурации
- Перезагрузка конфигурации в память

#### Очистка старых резервных копий (`_cleanup_old_backups`)
- Сохранение только 5 последних резервных копий
- Автоматическое удаление старых файлов

### 3. Обработка проблем с кодировкой

#### Загрузка с различными кодировками (`_load_with_different_encodings`)
```python
def _load_with_different_encodings(self):
    """Загрузка конфигурации с различными кодировками"""
    encodings = ['utf-8', 'utf-8-sig', 'cp1251', 'latin-1', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            self.logger.info(f"Попытка загрузки с кодировкой: {encoding}")
            
            with open(self.config_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # Парсим TOML
            self._config = tomli.loads(content)
            
            self.logger.info(f"Конфигурация успешно загружена с кодировкой: {encoding}")
            return True
            
        except UnicodeDecodeError:
            self.logger.debug(f"Кодировка {encoding} не подходит")
            continue
        except Exception as e:
            self.logger.debug(f"Ошибка при загрузке с кодировкой {encoding}: {e}")
            continue
    
    self.logger.error("Не удалось загрузить конфигурацию ни с одной из кодировок")
    return False
```

### 4. Fallback конфигурации

#### Создание fallback групп кнопок (`_create_fallback_button_groups`)
- Базовые группы: "Основные команды", "Последовательности", "Настройки"
- Минимальная fallback конфигурация при ошибках

#### Создание fallback ключевых слов (`_create_default_keywords`)
- Базовые ключевые слова для различных типов ответов
- Обработка ошибок импорта SequenceKeywords

#### Создание fallback конфигурации мастера (`_create_default_wizard_config`)
- Базовая структура мастера с шагами
- Минимальная конфигурация при ошибках

#### Создание конфигурации в памяти (`_create_in_memory_default_config`)
```python
def _create_in_memory_default_config(self):
    """Создание конфигурации по умолчанию в памяти"""
    try:
        self.logger.warning("Создание конфигурации по умолчанию в памяти")
        
        # Создаем базовую конфигурацию
        default_config = {
            'buttons': {
                'Вперед': 'G1 X100',
                'Назад': 'G1 X-100',
                'Стоп': 'M112',
                'Домой': 'G28',
                'Покраска': 'M1000',
                'Промывка': 'M1001'
            },
            'sequences': {
                'Покраска': ['G28', 'M1000', 'G1 X100', 'M1001'],
                'Промывка': ['G28', 'M1001', 'G1 X50', 'M1001'],
                'Тест': ['G28', 'G1 X10', 'G1 X-10', 'G28']
            },
            'serial_default': {
                'port': 'COM1',
                'baudrate': 115200
            },
            'sequence_keywords': {
                'complete': ['OK', 'DONE', 'COMPLETE'],
                'received': ['RECEIVED', 'ACK'],
                'error': ['ERROR', 'FAIL'],
                'complete_line': ['READY', '>']
            },
            'wizard': {
                'image_dir': 'back',
                'paint_sequence': 'Покраска',
                'rinse_sequence': 'Промывка'
            }
        }
        
        self._config = default_config
        self.button_groups = {'Основные': ['Вперед', 'Назад', 'Стоп', 'Домой']}
        
        # Создаем базовые ключевые слова
        try:
            from core.sequence_manager import SequenceKeywords
            self.sequence_keywords = SequenceKeywords.from_dict(default_config['sequence_keywords'])
        except Exception as e:
            self.logger.error(f"Ошибка создания ключевых слов: {e}")
            self.sequence_keywords = None
        
        self.logger.info("Конфигурация по умолчанию в памяти создана")
        
    except Exception as e:
        self.logger.error(f"Ошибка создания конфигурации по умолчанию в памяти: {e}")
        # Минимальная fallback конфигурация
        self._config = {
            'buttons': {'Стоп': 'M112'},
            'sequences': {'Тест': ['G28']},
            'serial_default': {'port': 'COM1', 'baudrate': 115200},
            'sequence_keywords': {
                'complete': ['OK'],
                'received': ['OK'],
                'error': ['ERROR'],
                'complete_line': ['>']
            }
        }
        self.button_groups = {'Основные': ['Стоп']}
        self.sequence_keywords = None
```

### 5. Улучшенная обработка ошибок в методе `load`

#### Обработка различных типов ошибок
- **FileNotFoundError**: Создание конфигурации по умолчанию
- **UnicodeDecodeError**: Попытка загрузки с различными кодировками
- **tomli.TOMLDecodeError**: Восстановление из резервной копии
- **PermissionError**: Логирование и повторный вызов ошибки
- **ValueError**: Восстановление из резервной копии и повторная валидация

#### Fallback механизмы
- Создание fallback групп кнопок при ошибках парсинга
- Создание fallback ключевых слов при ошибках импорта
- Создание fallback конфигурации мастера при ошибках обработки

## Типы обрабатываемых ошибок

### 1. Ошибки файловой системы
- **PermissionError**: Отсутствие прав доступа к файлам
- **OSError**: Общие ошибки операционной системы
- **FileNotFoundError**: Отсутствие файла конфигурации

### 2. Ошибки кодировки
- **UnicodeDecodeError**: Проблемы с кодировкой файла
- Автоматическое тестирование различных кодировок

### 3. Ошибки парсинга TOML
- **tomli.TOMLDecodeError**: Ошибки синтаксиса TOML
- **ValueError**: Ошибки валидации структуры

### 4. Ошибки импорта
- **ImportError**: Отсутствие модулей
- **AttributeError**: Отсутствие атрибутов в модулях

## Логирование

### Уровни логирования
- **INFO**: Успешные операции, создание резервных копий
- **WARNING**: Отсутствующие секции, создание fallback конфигураций
- **ERROR**: Критические ошибки, невозможность восстановления
- **DEBUG**: Детальная информация о попытках загрузки

### Примеры логов
```
INFO: Резервная копия создана: config/backups/config_backup_20241201_143022.toml
WARNING: Создание fallback групп кнопок
ERROR: Ошибка прав доступа при создании резервной копии: [Errno 13] Permission denied
```

## Преимущества

### 1. Надежность
- Автоматическое создание резервных копий
- Восстановление из резервных копий при ошибках
- Fallback конфигурации для критических ошибок

### 2. Гибкость
- Поддержка различных кодировок
- Детальная валидация структуры
- Модульная архитектура обработки ошибок

### 3. Информативность
- Подробное логирование всех операций
- Четкие сообщения об ошибках
- Отслеживание процесса восстановления

### 4. Производительность
- Эффективная очистка старых резервных копий
- Оптимизированная валидация структуры
- Минимальные накладные расходы

## Рекомендации по использованию

### 1. Мониторинг логов
- Регулярно проверяйте логи на наличие предупреждений
- Отслеживайте частоту создания fallback конфигураций

### 2. Резервные копии
- Периодически проверяйте директорию `backups/`
- Настройте автоматическое резервное копирование

### 3. Валидация
- Регулярно проверяйте структуру конфигурации
- Используйте валидацию при изменении конфигурации

### 4. Тестирование
- Тестируйте загрузку с различными кодировками
- Проверяйте восстановление из резервных копий

