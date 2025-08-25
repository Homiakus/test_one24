"""
Интеграционные тесты мультизонального алгоритма
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.multizone_manager import MultizoneManager
from core.sequence_manager import CommandSequenceExecutor, CommandValidator
from core.command_executor import CommandExecutorFactory
from core.di_container import get_container, register
from core.interfaces import IMultizoneManager
from monitoring import MonitoringManager
from config.config_loader import ConfigLoader


class TestMultizoneIntegration:
    """Интеграционные тесты мультизонального алгоритма"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        # Создаем моки для внешних зависимостей
        self.serial_manager = Mock()
        self.serial_manager.is_connected = True
        self.serial_manager.send_command = Mock(return_value=True)
        self.serial_manager.receive_response = Mock(return_value="ok")
        
        # Создаем MultizoneManager
        self.multizone_manager = MultizoneManager()
        
        # Создаем MonitoringManager
        self.monitoring_manager = MonitoringManager(multizone_manager=self.multizone_manager)
    
    def test_di_container_integration(self):
        """Тест интеграции с DI контейнером"""
        # Получаем DI контейнер
        container = get_container()
        
        # Регистрируем MultizoneManager
        register(IMultizoneManager, MultizoneManager, singleton=True)
        
        # Разрешаем зависимость
        multizone_manager = container.resolve(IMultizoneManager)
        
        # Проверяем, что получен правильный объект
        assert isinstance(multizone_manager, MultizoneManager)
        
        # Проверяем функциональность
        multizone_manager.set_zones([1, 2, 3])
        active_zones = multizone_manager.get_active_zones()
        assert set(active_zones) == {1, 2, 3}
    
    def test_command_executor_integration(self):
        """Тест интеграции с CommandExecutor"""
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 3])
        
        # Создаем CommandExecutor через фабрику
        executor = CommandExecutorFactory.create_executor(
            'basic',
            serial_manager=self.serial_manager,
            multizone_manager=self.multizone_manager
        )
        
        # Выполняем мультизональную команду
        result = executor.execute("og_multizone-test")
        
        # Проверяем результат
        assert result == True
        
        # Проверяем, что команды были отправлены
        assert self.serial_manager.send_command.call_count == 4  # 2 зоны * 2 команды
        
        # Проверяем порядок команд
        calls = self.serial_manager.send_command.call_args_list
        expected_sequence = [
            "multizone 0001", "test",  # Зона 1
            "multizone 0100", "test"   # Зона 3
        ]
        
        for i, expected_command in enumerate(expected_sequence):
            assert calls[i][0][0] == expected_command
    
    def test_sequence_executor_integration(self):
        """Тест интеграции с SequenceExecutor"""
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 2])
        
        # Создаем SequenceExecutor
        sequence_executor = CommandSequenceExecutor(
            serial_manager=self.serial_manager,
            multizone_manager=self.multizone_manager
        )
        
        # Определяем последовательность
        sequence = [
            "og_multizone-test",
            "og_multizone-paint"
        ]
        
        # Выполняем последовательность
        result = sequence_executor.run(sequence)
        
        # Проверяем результат
        assert result == True
        
        # Проверяем количество отправленных команд
        # 2 команды * 2 зоны * 2 команды на зону = 8 команд
        assert self.serial_manager.send_command.call_count == 8
    
    def test_monitoring_integration(self):
        """Тест интеграции с системой мониторинга"""
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 2, 3])
        
        # Записываем тестовую статистику
        self.monitoring_manager.record_multizone_execution(
            zones=[1, 2, 3],
            command="og_multizone-test",
            success=True,
            execution_time=2.5
        )
        
        # Получаем статистику
        stats = self.monitoring_manager.get_multizone_stats()
        
        # Проверяем статистику
        assert stats['total_executions'] == 1
        assert stats['successful_executions'] == 1
        assert stats['failed_executions'] == 0
        assert stats['success_rate'] == 100.0
        assert stats['active_zones'] == [1, 2, 3]
        assert stats['zone_mask'] == 7  # 0111 в двоичной системе
        
        # Проверяем статистику использования зон
        assert stats['zone_usage'][1] == 1
        assert stats['zone_usage'][2] == 1
        assert stats['zone_usage'][3] == 1
        assert stats['zone_usage'][4] == 0
    
    def test_config_integration(self):
        """Тест интеграции с конфигурацией"""
        # Создаем ConfigLoader
        config_loader = ConfigLoader(Path("config.toml"))
        
        # Загружаем конфигурацию
        config = config_loader.load()
        
        # Проверяем наличие мультизональных команд
        buttons = config.get('buttons', {})
        multizone_commands = [cmd for cmd in buttons.keys() if cmd.startswith('og_multizone-')]
        
        assert len(multizone_commands) > 0, "Не найдены мультизональные команды в конфигурации"
        
        # Проверяем наличие мультизональных последовательностей
        sequences = config.get('sequences', {})
        multizone_sequences = [seq for seq in sequences.keys() if 'multizone' in seq]
        
        assert len(multizone_sequences) > 0, "Не найдены мультизональные последовательности в конфигурации"
        
        # Проверяем наличие флагов зон
        flags = config.get('flags', {})
        zone_flags = [flag for flag in flags.keys() if 'zone' in flag]
        
        assert len(zone_flags) > 0, "Не найдены флаги зон в конфигурации"
    
    def test_full_workflow_integration(self):
        """Тест полного рабочего процесса"""
        # 1. Настройка зон
        self.multizone_manager.set_zones([1, 3, 4])
        
        # 2. Создание исполнителя команд
        executor = CommandExecutorFactory.create_executor(
            'basic',
            serial_manager=self.serial_manager,
            multizone_manager=self.multizone_manager
        )
        
        # 3. Создание исполнителя последовательностей
        sequence_executor = CommandSequenceExecutor(
            serial_manager=self.serial_manager,
            multizone_manager=self.multizone_manager
        )
        
        # 4. Выполнение последовательности
        sequence = [
            "og_multizone-test",
            "og_multizone-paint",
            "og_multizone-rinse"
        ]
        
        result = sequence_executor.run(sequence)
        
        # 5. Проверка результата
        assert result == True
        
        # 6. Запись статистики
        self.monitoring_manager.record_multizone_execution(
            zones=[1, 3, 4],
            command="multizone_sequence",
            success=True,
            execution_time=5.0
        )
        
        # 7. Проверка статистики
        stats = self.monitoring_manager.get_multizone_stats()
        assert stats['total_executions'] == 1
        assert stats['successful_executions'] == 1
        assert stats['success_rate'] == 100.0
        
        # 8. Проверка статусов зон
        for zone_id in [1, 3, 4]:
            zone_status = self.multizone_manager.get_zone_status(zone_id)
            assert zone_status.status.value == "completed"
    
    def test_error_handling_integration(self):
        """Тест обработки ошибок в интеграции"""
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 2, 3])
        
        # Мокаем ошибку при отправке команды
        self.serial_manager.send_command = Mock(side_effect=[True, False, True, True, True, True])
        
        # Создаем исполнитель
        executor = CommandExecutorFactory.create_executor(
            'basic',
            serial_manager=self.serial_manager,
            multizone_manager=self.multizone_manager
        )
        
        # Выполняем мультизональную команду
        result = executor.execute("og_multizone-test")
        
        # Проверяем, что команда завершилась с ошибкой
        assert result == False
        
        # Записываем статистику об ошибке
        self.monitoring_manager.record_multizone_execution(
            zones=[1, 2, 3],
            command="og_multizone-test",
            success=False,
            execution_time=1.0,
            error_message="Serial communication error"
        )
        
        # Проверяем статистику
        stats = self.monitoring_manager.get_multizone_stats()
        assert stats['total_executions'] == 1
        assert stats['successful_executions'] == 0
        assert stats['failed_executions'] == 1
        assert stats['success_rate'] == 0.0
        
        # Проверяем статусы зон
        assert self.multizone_manager.get_zone_status(1).status.value == "completed"
        assert self.multizone_manager.get_zone_status(2).status.value == "error"
        assert self.multizone_manager.get_zone_status(3).status.value == "active"  # Не была затронута
    
    def test_concurrent_access_integration(self):
        """Тест конкурентного доступа в интеграции"""
        import threading
        import time
        
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 2, 3, 4])
        
        # Создаем исполнитель
        executor = CommandExecutorFactory.create_executor(
            'basic',
            serial_manager=self.serial_manager,
            multizone_manager=self.multizone_manager
        )
        
        results = []
        
        def worker(zone_id):
            """Рабочая функция для тестирования конкурентности"""
            try:
                # Устанавливаем статус зоны
                self.multizone_manager.set_zone_status(zone_id, "executing")
                
                # Выполняем команду
                result = executor.execute("og_multizone-test")
                
                # Устанавливаем статус зоны
                if result:
                    self.multizone_manager.set_zone_status(zone_id, "completed")
                else:
                    self.multizone_manager.set_zone_status(zone_id, "error")
                
                results.append(f"zone_{zone_id}_completed")
                
            except Exception as e:
                results.append(f"zone_{zone_id}_error: {e}")
        
        # Запускаем потоки
        threads = []
        for zone_id in [1, 2, 3, 4]:
            thread = threading.Thread(target=worker, args=(zone_id,))
            threads.append(thread)
            thread.start()
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Проверяем результаты
        assert len(results) == 4
        assert all("completed" in result for result in results)
        
        # Проверяем статусы зон
        for zone_id in [1, 2, 3, 4]:
            zone_status = self.multizone_manager.get_zone_status(zone_id)
            assert zone_status.status.value == "completed"
    
    def test_performance_integration(self):
        """Тест производительности в интеграции"""
        import time
        
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 2, 3, 4])
        
        # Создаем исполнитель
        executor = CommandExecutorFactory.create_executor(
            'basic',
            serial_manager=self.serial_manager,
            multizone_manager=self.multizone_manager
        )
        
        # Измеряем время выполнения
        start_time = time.time()
        
        # Выполняем мультизональную команду
        result = executor.execute("og_multizone-test")
        
        execution_time = time.time() - start_time
        
        # Проверяем результат
        assert result == True
        
        # Проверяем время выполнения (должно быть менее 1 секунды)
        assert execution_time < 1.0, f"Время выполнения {execution_time:.3f}с превышает 1 секунду"
        
        # Записываем статистику производительности
        self.monitoring_manager.record_multizone_execution(
            zones=[1, 2, 3, 4],
            command="og_multizone-test",
            success=True,
            execution_time=execution_time
        )
        
        # Проверяем статистику
        stats = self.monitoring_manager.get_multizone_stats()
        assert stats['total_executions'] == 1
        assert stats['successful_executions'] == 1
        assert stats['success_rate'] == 100.0
    
    def test_memory_usage_integration(self):
        """Тест использования памяти в интеграции"""
        import psutil
        import os
        
        # Получаем текущий процесс
        process = psutil.Process(os.getpid())
        
        # Измеряем использование памяти до теста
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 2, 3, 4])
        
        # Создаем исполнитель
        executor = CommandExecutorFactory.create_executor(
            'basic',
            serial_manager=self.serial_manager,
            multizone_manager=self.multizone_manager
        )
        
        # Выполняем несколько мультизональных команд
        for i in range(10):
            executor.execute("og_multizone-test")
        
        # Измеряем использование памяти после теста
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        
        # Вычисляем прирост памяти
        memory_increase = memory_after - memory_before
        
        # Проверяем, что прирост памяти не превышает 50MB
        assert memory_increase < 50, f"Прирост памяти {memory_increase:.2f}MB превышает 50MB"
        
        # Проверяем общее использование памяти
        assert memory_after < 100, f"Общее использование памяти {memory_after:.2f}MB превышает 100MB"


class TestMultizoneEndToEnd:
    """End-to-end тесты мультизонального алгоритма"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        # Создаем полную систему
        self.serial_manager = Mock()
        self.serial_manager.is_connected = True
        self.serial_manager.send_command = Mock(return_value=True)
        self.serial_manager.receive_response = Mock(return_value="ok")
        
        self.multizone_manager = MultizoneManager()
        self.monitoring_manager = MonitoringManager(multizone_manager=self.multizone_manager)
        
        # Создаем DI контейнер
        self.container = get_container()
        register(IMultizoneManager, MultizoneManager, singleton=True)
    
    def test_complete_multizone_workflow(self):
        """Тест полного мультизонального рабочего процесса"""
        # 1. Инициализация системы
        multizone_manager = self.container.resolve(IMultizoneManager)
        multizone_manager.set_zones([1, 2, 3])
        
        # 2. Создание исполнителей
        executor = CommandExecutorFactory.create_executor(
            'basic',
            serial_manager=self.serial_manager,
            multizone_manager=multizone_manager
        )
        
        sequence_executor = CommandSequenceExecutor(
            serial_manager=self.serial_manager,
            multizone_manager=multizone_manager
        )
        
        # 3. Выполнение рабочего процесса
        workflow_sequence = [
            "og_multizone-test",    # Тестирование
            "og_multizone-paint",   # Покраска
            "og_multizone-rinse",   # Промывка
            "og_multizone-dry"      # Сушка
        ]
        
        result = sequence_executor.run(workflow_sequence)
        
        # 4. Проверка результатов
        assert result == True
        
        # Проверяем количество отправленных команд
        # 4 команды * 3 зоны * 2 команды на зону = 24 команды
        assert self.serial_manager.send_command.call_count == 24
        
        # Проверяем статусы зон
        for zone_id in [1, 2, 3]:
            zone_status = multizone_manager.get_zone_status(zone_id)
            assert zone_status.status.value == "completed"
        
        # 5. Запись статистики
        self.monitoring_manager.record_multizone_execution(
            zones=[1, 2, 3],
            command="complete_workflow",
            success=True,
            execution_time=10.0
        )
        
        # 6. Проверка статистики
        stats = self.monitoring_manager.get_multizone_stats()
        assert stats['total_executions'] == 1
        assert stats['successful_executions'] == 1
        assert stats['success_rate'] == 100.0
        assert stats['active_zones'] == [1, 2, 3]
        assert stats['zone_mask'] == 7  # 0111
    
    def test_multizone_error_recovery(self):
        """Тест восстановления после ошибок в мультизональном режиме"""
        # 1. Настройка системы
        multizone_manager = self.container.resolve(IMultizoneManager)
        multizone_manager.set_zones([1, 2, 3, 4])
        
        # 2. Создание исполнителя
        executor = CommandExecutorFactory.create_executor(
            'basic',
            serial_manager=self.serial_manager,
            multizone_manager=multizone_manager
        )
        
        # 3. Симуляция ошибки в середине выполнения
        call_count = 0
        def mock_send_command(command):
            nonlocal call_count
            call_count += 1
            # Ошибка на 5-й команде
            if call_count == 5:
                return False
            return True
        
        self.serial_manager.send_command = Mock(side_effect=mock_send_command)
        
        # 4. Выполнение команды
        result = executor.execute("og_multizone-test")
        
        # 5. Проверка результата
        assert result == False
        
        # 6. Проверка статусов зон
        # Зоны 1 и 2 должны быть завершены, зона 3 должна быть в ошибке
        assert multizone_manager.get_zone_status(1).status.value == "completed"
        assert multizone_manager.get_zone_status(2).status.value == "completed"
        assert multizone_manager.get_zone_status(3).status.value == "error"
        assert multizone_manager.get_zone_status(4).status.value == "active"  # Не была затронута
        
        # 7. Восстановление и повторное выполнение
        # Сбрасываем ошибку
        multizone_manager.set_zone_status(3, "active")
        
        # Восстанавливаем нормальную работу
        self.serial_manager.send_command = Mock(return_value=True)
        
        # Повторно выполняем команду
        result = executor.execute("og_multizone-test")
        
        # 8. Проверка восстановления
        assert result == True
        
        # Все зоны должны быть завершены
        for zone_id in [1, 2, 3, 4]:
            zone_status = multizone_manager.get_zone_status(zone_id)
            assert zone_status.status.value == "completed"
