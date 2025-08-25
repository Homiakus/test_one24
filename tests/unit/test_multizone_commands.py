"""
Тесты командной системы мультизонального алгоритма
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from core.sequence_manager import CommandValidator, CommandSequenceExecutor, CommandType
from core.command_executor import BasicCommandExecutor, InteractiveCommandExecutor, CommandExecutorFactory
from core.multizone_manager import MultizoneManager, ZoneStatus
from core.serial_manager import SerialManager


class TestMultizoneCommands:
    """Тесты мультизональных команд"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.multizone_manager = MultizoneManager()
        self.serial_manager = Mock(spec=SerialManager)
        self.serial_manager.is_connected = True
        
        # Мокаем методы SerialManager
        self.serial_manager.send_command = Mock(return_value=True)
        self.serial_manager.receive_response = Mock(return_value="ok")
    
    def test_multizone_command_validation(self):
        """Тест валидации мультизональных команд"""
        validator = CommandValidator(flag_manager=None)
        
        # Валидные мультизональные команды
        test_commands = [
            "og_multizone-test",
            "og_multizone-paint",
            "og_multizone-rinse",
            "og_multizone-clean",
            "og_multizone-dry"
        ]
        
        for command in test_commands:
            result = validator.validate_command(command)
            assert result.is_valid, f"Команда {command} должна быть валидной"
            assert result.command_type == CommandType.MULTIZONE, f"Тип команды должен быть MULTIZONE для {command}"
            assert result.parsed_data.get('base_command') == command[13:], f"Базовая команда должна быть {command[13:]} для {command}"
    
    def test_non_multizone_command_validation(self):
        """Тест валидации обычных команд"""
        validator = CommandValidator(flag_manager=None)
        
        # Обычные команды не должны быть мультизональными
        test_commands = [
            "test",
            "paint",
            "rinse",
            "clean",
            "dry"
        ]
        
        for command in test_commands:
            result = validator.validate_command(command)
            assert result.is_valid, f"Команда {command} должна быть валидной"
            assert result.command_type != CommandType.MULTIZONE, f"Тип команды не должен быть MULTIZONE для {command}"
    
    def test_basic_command_executor_multizone(self):
        """Тест выполнения мультизональных команд в BasicCommandExecutor"""
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 3])
        
        # Создаем исполнитель
        executor = BasicCommandExecutor(
            serial_manager=self.serial_manager,
            multizone_manager=self.multizone_manager
        )
        
        # Выполняем мультизональную команду
        result = executor.execute("og_multizone-test")
        
        # Проверяем результат
        assert result == True
        
        # Проверяем, что команды были отправлены в правильном порядке
        calls = self.serial_manager.send_command.call_args_list
        expected_sequence = [
            "multizone 0001",  # Зона 1
            "test",            # Базовая команда для зоны 1
            "multizone 0100",  # Зона 3
            "test"             # Базовая команда для зоны 3
        ]
        
        for i, expected_command in enumerate(expected_sequence):
            assert calls[i][0][0] == expected_command
    
    def test_interactive_command_executor_multizone(self):
        """Тест выполнения мультизональных команд в InteractiveCommandExecutor"""
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([2, 4])
        
        # Создаем исполнитель
        executor = InteractiveCommandExecutor(
            serial_manager=self.serial_manager,
            multizone_manager=self.multizone_manager
        )
        
        # Настраиваем моки для успешного выполнения
        self.serial_manager.send_command.return_value = True
        # Настраиваем _last_response для возврата "OK"
        self.serial_manager._last_response = "OK"
        
        # Выполняем мультизональную команду
        result = executor.execute("og_multizone-paint")
        
        # Проверяем результат
        assert result == True
        
        # Проверяем, что команды были отправлены в правильном порядке
        calls = self.serial_manager.send_command.call_args_list
        expected_sequence = [
            "multizone 0010",  # Зона 2
            "paint",           # Базовая команда для зоны 2
            "multizone 1000",  # Зона 4
            "paint"            # Базовая команда для зоны 4
        ]
        
        for i, expected_command in enumerate(expected_sequence):
            assert calls[i][0][0] == expected_command
    
    def test_multizone_command_with_no_active_zones(self):
        """Тест мультизональной команды без активных зон"""
        # Не устанавливаем активные зоны
        assert self.multizone_manager.get_active_zones() == []
        
        # Создаем исполнитель
        executor = BasicCommandExecutor(
            serial_manager=self.serial_manager,
            multizone_manager=self.multizone_manager
        )
        
        # Выполняем мультизональную команду
        result = executor.execute("og_multizone-test")
        
        # Команда должна быть пропущена (возвращает True)
        assert result == True
        
        # Никакие команды не должны быть отправлены
        assert self.serial_manager.send_command.call_count == 0
    
    def test_multizone_command_with_all_zones(self):
        """Тест мультизональной команды со всеми зонами"""
        # Устанавливаем все зоны
        self.multizone_manager.set_zones([1, 2, 3, 4])
        
        # Создаем исполнитель
        executor = BasicCommandExecutor(
            serial_manager=self.serial_manager,
            multizone_manager=self.multizone_manager
        )
        
        # Выполняем мультизональную команду
        result = executor.execute("og_multizone-rinse")
        
        # Проверяем результат
        assert result == True
        
        # Проверяем количество отправленных команд (4 зоны * 2 команды = 8 команд)
        assert self.serial_manager.send_command.call_count == 8
        
        # Проверяем порядок команд
        calls = self.serial_manager.send_command.call_args_list
        expected_sequence = [
            "multizone 0001", "rinse",  # Зона 1
            "multizone 0010", "rinse",  # Зона 2
            "multizone 0100", "rinse",  # Зона 3
            "multizone 1000", "rinse"   # Зона 4
        ]
        
        for i, expected_command in enumerate(expected_sequence):
            assert calls[i][0][0] == expected_command
    
    def test_multizone_command_execution_order(self):
        """Тест порядка выполнения мультизональных команд"""
        # Устанавливаем зоны в произвольном порядке
        self.multizone_manager.set_zones([4, 1, 3, 2])
        
        # Создаем исполнитель
        executor = BasicCommandExecutor(
            serial_manager=self.serial_manager,
            multizone_manager=self.multizone_manager
        )
        
        # Выполняем мультизональную команду
        result = executor.execute("og_multizone-clean")
        
        # Проверяем результат
        assert result == True
        
        # Проверяем, что команды выполняются в порядке зон (1, 2, 3, 4)
        calls = self.serial_manager.send_command.call_args_list
        expected_sequence = [
            "multizone 0001", "clean",  # Зона 1
            "multizone 0010", "clean",  # Зона 2
            "multizone 0100", "clean",  # Зона 3
            "multizone 1000", "clean"   # Зона 4
        ]
        
        for i, expected_command in enumerate(expected_sequence):
            assert calls[i][0][0] == expected_command
    
    def test_multizone_command_error_handling(self):
        """Тест обработки ошибок в мультизональных командах"""
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 2])
        
        # Мокаем ошибку при отправке команды
        # Для каждой зоны: маска (True) + базовая команда (False для зоны 1, True для зоны 2)
        self.serial_manager.send_command = Mock(side_effect=[True, False, True, True])
        
        # Создаем исполнитель
        executor = BasicCommandExecutor(
            serial_manager=self.serial_manager,
            multizone_manager=self.multizone_manager
        )
        
        # Выполняем мультизональную команду
        result = executor.execute("og_multizone-test")
        
        # Проверяем, что команда завершилась с ошибкой
        assert result == False
        
        # Проверяем статус зон
        # Первая зона должна быть в состоянии ошибки (базовая команда не прошла)
        assert self.multizone_manager.get_zone_status(1).status == ZoneStatus.ERROR
        # Вторая зона остается активной, но не обрабатывается (выполнение остановилось на первой ошибке)
        assert self.multizone_manager.get_zone_status(2).status == ZoneStatus.ACTIVE
    
    def test_command_executor_factory_multizone(self):
        """Тест фабрики исполнителей команд с мультизональной поддержкой"""
        # Создаем исполнитель через фабрику
        executor = CommandExecutorFactory.create_executor(
            'basic',
            serial_manager=self.serial_manager,
            multizone_manager=self.multizone_manager
        )
        
        # Проверяем тип исполнителя
        assert isinstance(executor, BasicCommandExecutor)
        
        # Проверяем, что MultizoneManager установлен
        assert executor.multizone_manager == self.multizone_manager
        
        # Создаем интерактивный исполнитель
        executor = CommandExecutorFactory.create_executor(
            'interactive',
            serial_manager=self.serial_manager,
            multizone_manager=self.multizone_manager
        )
        
        # Проверяем тип исполнителя
        assert isinstance(executor, InteractiveCommandExecutor)
        
        # Проверяем, что MultizoneManager установлен
        assert executor.multizone_manager == self.multizone_manager
    
    def test_multizone_command_with_zone_status_updates(self):
        """Тест обновления статусов зон при выполнении команд"""
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 2])
        
        # Создаем исполнитель
        executor = BasicCommandExecutor(
            serial_manager=self.serial_manager,
            multizone_manager=self.multizone_manager
        )
        
        # Выполняем мультизональную команду
        result = executor.execute("og_multizone-test")
        
        # Проверяем результат
        assert result == True
        
        # Проверяем статусы зон после выполнения
        assert self.multizone_manager.get_zone_status(1).status == ZoneStatus.COMPLETED
        assert self.multizone_manager.get_zone_status(2).status == ZoneStatus.COMPLETED
    
    def test_multizone_command_serialization(self):
        """Тест сериализации мультизональных команд"""
        from core.multizone_types import MultizoneCommand, MultizoneCommandType
        
        # Создаем мультизональную команду
        command = MultizoneCommand(
            command_type=MultizoneCommandType.ZONE_EXECUTION,
            base_command="test",
            zone_mask=1,
            zones=[1]
        )
        
        # Проверяем атрибуты команды
        assert command.command_type == MultizoneCommandType.ZONE_EXECUTION
        assert command.base_command == "test"
        assert command.zone_mask == 1
        assert command.zones == [1]
        
        # Создаем обычную команду
        command = MultizoneCommand(
            command_type=MultizoneCommandType.ZONE_SELECTION,
            base_command="test",
            zone_mask=0,
            zones=[]
        )
        
        # Проверяем атрибуты команды
        assert command.command_type == MultizoneCommandType.ZONE_SELECTION
        assert command.base_command == "test"
        assert command.zone_mask == 0
        assert command.zones == []


class TestMultizoneSequenceExecutor:
    """Тесты мультизонального исполнителя последовательностей"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.multizone_manager = MultizoneManager()
        self.serial_manager = Mock(spec=SerialManager)
        self.serial_manager.is_connected = True
        self.serial_manager.send_command = Mock(return_value=True)
        
        # Создаем исполнитель последовательностей
        self.executor = CommandSequenceExecutor(
            serial_manager=self.serial_manager,
            commands=[],  # Пустой список команд
            multizone_manager=self.multizone_manager
        )
    
    def test_multizone_sequence_execution(self):
        """Тест выполнения мультизональной последовательности"""
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 3])
        
        # Определяем последовательность с мультизональными командами
        sequence = [
            "og_multizone-test",
            "og_multizone-paint",
            "og_multizone-rinse"
        ]
        
        # Создаем исполнитель с последовательностью
        executor = CommandSequenceExecutor(
            serial_manager=self.serial_manager,
            commands=sequence,
            multizone_manager=self.multizone_manager
        )
        
        # Запускаем выполнение
        executor.start()
        executor.wait()  # Ждем завершения
        
        # Проверяем количество отправленных команд
        # 2 зоны * 3 команды * 2 команды на зону = 12 команд
        assert self.serial_manager.send_command.call_count == 12
    
    def test_mixed_sequence_execution(self):
        """Тест выполнения смешанной последовательности"""
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 2])
        
        # Определяем смешанную последовательность
        sequence = [
            "test",  # Обычная команда
            "og_multizone-paint",  # Мультизональная команда
            "rinse",  # Обычная команда
            "og_multizone-clean"  # Мультизональная команда
        ]
        
        # Создаем исполнитель с последовательностью
        executor = CommandSequenceExecutor(
            serial_manager=self.serial_manager,
            commands=sequence,
            multizone_manager=self.multizone_manager
        )
        
        # Запускаем выполнение
        executor.start()
        executor.wait()  # Ждем завершения
        
        # Проверяем количество отправленных команд
        # 2 обычные команды + 2 мультизональные * 2 зоны * 2 команды = 10 команд
        assert self.serial_manager.send_command.call_count == 10
    
    def test_multizone_sequence_with_errors(self):
        """Тест выполнения мультизональной последовательности с ошибками"""
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 2, 3])
        
        # Мокаем ошибку при отправке команды
        self.serial_manager.send_command = Mock(side_effect=[True, False, True, True, True, True])
        
        # Определяем последовательность
        sequence = [
            "og_multizone-test",
            "og_multizone-paint"
        ]
        
        # Создаем исполнитель с последовательностью
        executor = CommandSequenceExecutor(
            serial_manager=self.serial_manager,
            commands=sequence,
            multizone_manager=self.multizone_manager
        )
        
        # Запускаем выполнение
        executor.start()
        executor.wait()  # Ждем завершения
        
        # Проверяем статусы зон
        assert self.multizone_manager.get_zone_status(1).status == ZoneStatus.COMPLETED
        assert self.multizone_manager.get_zone_status(2).status == ZoneStatus.ERROR
        assert self.multizone_manager.get_zone_status(3).status == ZoneStatus.ACTIVE  # Не была затронута
    
    def test_multizone_sequence_progress_tracking(self):
        """Тест отслеживания прогресса мультизональной последовательности"""
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 2])
        
        # Список для отслеживания прогресса
        progress_updates = []
        
        # Определяем последовательность
        sequence = [
            "og_multizone-test",
            "og_multizone-paint"
        ]
        
        # Создаем исполнитель с последовательностью
        executor = CommandSequenceExecutor(
            serial_manager=self.serial_manager,
            commands=sequence,
            multizone_manager=self.multizone_manager
        )
        
        # Подключаем сигнал прогресса
        executor.progress_updated.connect(lambda current, total: progress_updates.append((current, total)))
        
        # Запускаем выполнение
        executor.start()
        executor.wait()  # Ждем завершения
        
        # Проверяем обновления прогресса
        # Ожидаем обновления прогресса
        assert len(progress_updates) >= 2
        
        # Проверяем, что прогресс увеличивается
        for i in range(1, len(progress_updates)):
            assert progress_updates[i][0] > progress_updates[i-1][0]
    
    def test_multizone_sequence_zone_status_signals(self):
        """Тест сигналов обновления статуса зон"""
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 2])
        
        # Определяем последовательность
        sequence = [
            "og_multizone-test"
        ]
        
        # Создаем исполнитель с последовательностью
        executor = CommandSequenceExecutor(
            serial_manager=self.serial_manager,
            commands=sequence,
            multizone_manager=self.multizone_manager
        )
        
        # Запускаем выполнение
        executor.start()
        executor.wait()  # Ждем завершения
        
        # Проверяем статусы зон после выполнения
        zone_status_1 = self.multizone_manager.get_zone_status(1)
        zone_status_2 = self.multizone_manager.get_zone_status(2)
        
        # Проверяем, что зоны были затронуты выполнением
        assert zone_status_1 is not None
        assert zone_status_2 is not None
