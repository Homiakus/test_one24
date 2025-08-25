"""
Integration тесты для системы тегов команд
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
from pathlib import Path

from core.tag_manager import TagManager
from core.tag_validator import TagValidator
from core.tag_processor import TagProcessor
from core.tags.wanted_tag import WantedTag
from core.flag_manager import FlagManager
from core.command_executor import CommandExecutor, BasicCommandExecutor, InteractiveCommandExecutor
from core.command_validator import CommandValidator
from core.sequence_manager import SequenceManager
from core.serial_manager import SerialManager
from core.multizone_manager import MultizoneManager
from ui.dialogs.tag_dialogs import TagDialogManager, WantedTagDialog
from core.di_container import DIContainer
from core.di_config_loader import DIConfigLoader


class TestTagSystemIntegration:
    """Integration тесты для системы тегов"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.di_container = DIContainer()
        self.di_config_loader = DIConfigLoader()
        
        # Регистрируем сервисы
        self.flag_manager = FlagManager()
        self.tag_manager = TagManager()
        self.tag_validator = TagValidator()
        self.tag_processor = TagProcessor()
        self.tag_dialog_manager = TagDialogManager()
        self.serial_manager = Mock(spec=SerialManager)
        self.multizone_manager = MultizoneManager()
        
        # Регистрируем в DI контейнере
        self.di_container.register("IFlagManager", self.flag_manager)
        self.di_container.register("ITagManager", self.tag_manager)
        self.di_container.register("ITagValidator", self.tag_validator)
        self.di_container.register("ITagProcessor", self.tag_processor)
        self.di_container.register("ITagDialogManager", self.tag_dialog_manager)
        self.di_container.register("ISerialManager", self.serial_manager)
        self.di_container.register("IMultizoneManager", self.multizone_manager)
    
    def test_tag_system_full_workflow(self):
        """Тест полного workflow системы тегов"""
        # Устанавливаем флаг wanted=True
        self.flag_manager.set_flag('wanted', True)
        
        # Создаем команду с тегом
        command = "test_command_wanted"
        
        # Парсим команду
        parsed = self.tag_manager.parse_command(command)
        assert parsed.base_command == "test_command"
        assert len(parsed.tags) == 1
        assert parsed.tags[0].tag_type.value == "wanted"
        
        # Валидируем теги
        assert self.tag_validator.validate_tags(parsed.tags) is True
        
        # Обрабатываем теги
        context = {"flag_manager": self.flag_manager}
        results = self.tag_manager.process_tags(parsed.tags, context)
        
        assert len(results) == 1
        result = results[0]
        assert result.success is True
        assert result.should_continue is False
        assert result.data.get("show_dialog") == "wanted"
    
    def test_command_executor_with_tags(self):
        """Тест CommandExecutor с тегами"""
        # Устанавливаем флаг wanted=True
        self.flag_manager.set_flag('wanted', True)
        
        # Создаем исполнитель команд
        executor = CommandExecutor(
            tag_manager=self.tag_manager,
            tag_dialog_manager=self.tag_dialog_manager
        )
        
        # Мокаем диалог
        with patch.object(self.tag_dialog_manager, 'show_tag_dialog') as mock_dialog:
            mock_dialog.return_value = "check_fluids"
            
            # Выполняем команду с тегом
            result = executor._process_tags("test_command_wanted", {"flag_manager": self.flag_manager})
            
            # Проверяем, что диалог был показан
            assert result is False  # выполнение должно быть остановлено
            mock_dialog.assert_called_once_with('wanted', None)
    
    def test_basic_command_executor_with_tags(self):
        """Тест BasicCommandExecutor с тегами"""
        # Устанавливаем флаг wanted=True
        self.flag_manager.set_flag('wanted', True)
        
        # Создаем исполнитель
        executor = BasicCommandExecutor(
            serial_manager=self.serial_manager,
            tag_manager=self.tag_manager,
            tag_dialog_manager=self.tag_dialog_manager
        )
        
        # Мокаем отправку команды
        self.serial_manager.send_command.return_value = True
        
        # Мокаем диалог
        with patch.object(self.tag_dialog_manager, 'show_tag_dialog') as mock_dialog:
            mock_dialog.return_value = "check_fluids"
            
            # Выполняем команду с тегом
            result = executor.execute("test_command_wanted", flag_manager=self.flag_manager)
            
            # Проверяем, что команда не была отправлена из-за тега
            assert result is False
            self.serial_manager.send_command.assert_not_called()
            mock_dialog.assert_called_once_with('wanted', None)
    
    def test_interactive_command_executor_with_tags(self):
        """Тест InteractiveCommandExecutor с тегами"""
        # Устанавливаем флаг wanted=True
        self.flag_manager.set_flag('wanted', True)
        
        # Создаем исполнитель
        executor = InteractiveCommandExecutor(
            serial_manager=self.serial_manager,
            tag_manager=self.tag_manager,
            tag_dialog_manager=self.tag_dialog_manager
        )
        
        # Мокаем отправку команды и ответ
        self.serial_manager.send_command.return_value = True
        self.serial_manager._last_response = "OK"
        
        # Мокаем диалог
        with patch.object(self.tag_dialog_manager, 'show_tag_dialog') as mock_dialog:
            mock_dialog.return_value = "check_fluids"
            
            # Выполняем команду с тегом
            result = executor.execute("test_command_wanted", flag_manager=self.flag_manager)
            
            # Проверяем, что команда не была отправлена из-за тега
            assert result is False
            self.serial_manager.send_command.assert_not_called()
            mock_dialog.assert_called_once_with('wanted', None)
    
    def test_multizone_command_with_tags(self):
        """Тест мультизональной команды с тегами"""
        # Устанавливаем флаг wanted=True
        self.flag_manager.set_flag('wanted', True)
        
        # Устанавливаем зоны
        self.multizone_manager.set_zones([1, 2])
        
        # Создаем исполнитель
        executor = BasicCommandExecutor(
            serial_manager=self.serial_manager,
            multizone_manager=self.multizone_manager,
            tag_manager=self.tag_manager,
            tag_dialog_manager=self.tag_dialog_manager
        )
        
        # Мокаем отправку команды
        self.serial_manager.send_command.return_value = True
        
        # Мокаем диалог
        with patch.object(self.tag_dialog_manager, 'show_tag_dialog') as mock_dialog:
            mock_dialog.return_value = "check_fluids"
            
            # Выполняем мультизональную команду с тегом
            result = executor.execute("og_multizone-test_command_wanted", flag_manager=self.flag_manager)
            
            # Проверяем, что команда не была отправлена из-за тега
            assert result is False
            self.serial_manager.send_command.assert_not_called()
            mock_dialog.assert_called_once_with('wanted', None)
    
    def test_command_validator_with_tags(self):
        """Тест CommandValidator с тегами"""
        # Создаем валидатор
        validator = CommandValidator(tag_manager=self.tag_manager)
        
        # Тестируем команду с валидным тегом
        result = validator.validate_command("test_command_wanted")
        assert result.is_valid is True
        assert result.command_type == "tagged"
        
        # Тестируем команду без тегов
        result = validator.validate_command("simple_command")
        assert result.is_valid is True
        assert result.command_type != "tagged"
    
    def test_sequence_manager_with_tags(self):
        """Тест SequenceManager с тегами"""
        # Создаем менеджер последовательностей
        sequence_manager = SequenceManager(
            flag_manager=self.flag_manager,
            tag_manager=self.tag_manager
        )
        
        # Устанавливаем флаг wanted=True
        self.flag_manager.set_flag('wanted', True)
        
        # Создаем последовательность с командой, содержащей тег
        sequence = ["test_command_wanted", "simple_command"]
        
        # Мокаем валидацию команд
        with patch.object(sequence_manager.command_validator, 'validate_command') as mock_validate:
            mock_validate.return_value = Mock(is_valid=True, command_type="tagged")
            
            # Валидируем последовательность
            result = sequence_manager.validate_sequence(sequence)
            assert result.is_valid is True
    
    def test_di_container_integration(self):
        """Тест интеграции с DI контейнером"""
        # Загружаем конфигурацию DI
        config_path = Path("resources/di_config.toml")
        if config_path.exists():
            self.di_config_loader.load_config(self.di_container, config_path)
        
        # Проверяем, что сервисы зарегистрированы
        assert self.di_container.has_service("IFlagManager")
        assert self.di_container.has_service("ITagManager")
        assert self.di_container.has_service("ITagValidator")
        assert self.di_container.has_service("ITagProcessor")
        assert self.di_container.has_service("ITagDialogManager")
        
        # Получаем сервисы
        flag_manager = self.di_container.resolve("IFlagManager")
        tag_manager = self.di_container.resolve("ITagManager")
        
        assert isinstance(flag_manager, FlagManager)
        assert isinstance(tag_manager, TagManager)
    
    def test_tag_dialog_callback_integration(self):
        """Тест интеграции callback диалогов тегов"""
        callback_called = False
        callback_result = None
        
        def test_callback(result):
            nonlocal callback_called, callback_result
            callback_called = True
            callback_result = result
        
        # Устанавливаем callback
        self.tag_dialog_manager.on_wanted_dialog_result = test_callback
        
        # Мокаем диалог
        with patch.object(self.tag_dialog_manager, 'show_tag_dialog') as mock_dialog:
            mock_dialog.return_value = "check_fluids"
            
            # Показываем диалог
            result = self.tag_dialog_manager.show_tag_dialog('wanted')
            
            # Проверяем, что callback был вызван
            assert result == "check_fluids"
            assert callback_called is True
            assert callback_result == "check_fluids"
    
    def test_flag_manager_thread_safety(self):
        """Тест потокобезопасности FlagManager"""
        import threading
        import time
        
        # Создаем несколько потоков для одновременного доступа к флагам
        def worker(thread_id):
            for i in range(10):
                self.flag_manager.set_flag(f'flag_{thread_id}_{i}', i)
                time.sleep(0.001)
                value = self.flag_manager.get_flag(f'flag_{thread_id}_{i}')
                assert value == i
        
        # Запускаем потоки
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Проверяем, что все флаги установлены корректно
        for i in range(5):
            for j in range(10):
                assert self.flag_manager.get_flag(f'flag_{i}_{j}') == j
    
    def test_tag_processing_error_handling(self):
        """Тест обработки ошибок при обработке тегов"""
        # Создаем некорректный тег
        from core.tag_types import TagInfo
        invalid_tag = TagInfo(
            tag_type="invalid_type",  # Некорректный тип
            tag_name="_invalid",
            parameters={},
            position=0
        )
        
        # Пытаемся обработать некорректный тег
        context = {"flag_manager": self.flag_manager}
        results = self.tag_manager.process_tags([invalid_tag], context)
        
        # Проверяем, что ошибка обработана корректно
        assert len(results) == 1
        result = results[0]
        assert result.success is False
        assert "неизвестный тип тега" in result.message.lower()
    
    def test_multiple_tags_processing_order(self):
        """Тест порядка обработки нескольких тегов"""
        # Создаем команду с несколькими тегами
        command = "test_command_wanted_another"
        
        # Парсим команду
        parsed = self.tag_manager.parse_command(command)
        assert len(parsed.tags) == 2
        
        # Устанавливаем флаг wanted=True
        self.flag_manager.set_flag('wanted', True)
        
        # Обрабатываем теги
        context = {"flag_manager": self.flag_manager}
        results = self.tag_manager.process_tags(parsed.tags, context)
        
        # Проверяем, что обработка остановилась на первом теге (wanted)
        assert len(results) == 1
        result = results[0]
        assert result.success is True
        assert result.should_continue is False
        assert result.data.get("show_dialog") == "wanted"


class TestTagSystemPerformance:
    """Тесты производительности системы тегов"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.tag_manager = TagManager()
        self.flag_manager = FlagManager()
    
    def test_tag_parsing_performance(self):
        """Тест производительности парсинга тегов"""
        import time
        
        # Создаем команду с множеством тегов
        command = "test_command_" + "_".join([f"tag{i}" for i in range(100)])
        
        # Измеряем время парсинга
        start_time = time.time()
        for _ in range(1000):
            parsed = self.tag_manager.parse_command(command)
        end_time = time.time()
        
        # Проверяем, что парсинг выполняется достаточно быстро
        parsing_time = end_time - start_time
        assert parsing_time < 1.0  # менее 1 секунды для 1000 операций
        
        # Проверяем результат
        assert len(parsed.tags) == 100
    
    def test_tag_processing_performance(self):
        """Тест производительности обработки тегов"""
        import time
        
        # Создаем множество тегов
        from core.tag_types import TagInfo
        tags = [
            TagInfo(
                tag_type="wanted",
                tag_name="_wanted",
                parameters={},
                position=i
            )
            for i in range(50)
        ]
        
        context = {"flag_manager": self.flag_manager}
        
        # Измеряем время обработки
        start_time = time.time()
        for _ in range(100):
            results = self.tag_manager.process_tags(tags, context)
        end_time = time.time()
        
        # Проверяем, что обработка выполняется достаточно быстро
        processing_time = end_time - start_time
        assert processing_time < 1.0  # менее 1 секунды для 100 операций
    
    def test_flag_manager_performance(self):
        """Тест производительности FlagManager"""
        import time
        
        # Измеряем время множественных операций с флагами
        start_time = time.time()
        for i in range(10000):
            self.flag_manager.set_flag(f'flag_{i}', i)
            value = self.flag_manager.get_flag(f'flag_{i}')
            assert value == i
        end_time = time.time()
        
        # Проверяем, что операции выполняются достаточно быстро
        operations_time = end_time - start_time
        assert operations_time < 2.0  # менее 2 секунд для 10000 операций


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
