"""
Интеграционные тесты для условного выполнения последовательностей
"""
import pytest
import time
from unittest.mock import Mock, patch
from typing import Dict, List

from core.sequence_manager import (
    SequenceManager, CommandSequenceExecutor, FlagManager,
    SequenceKeywords, CancellationToken
)


class TestConditionalExecutionIntegration:
    """Интеграционные тесты условного выполнения"""
    
    @pytest.fixture
    def mock_serial_manager(self):
        """Фикстура с моком SerialManager"""
        mock = Mock()
        mock.is_connected = True
        mock.send_command.return_value = True
        return mock
    
    @pytest.fixture
    def flag_manager(self):
        """Фикстура с FlagManager"""
        return FlagManager()
    
    @pytest.fixture
    def sequence_manager(self, flag_manager):
        """Фикстура с SequenceManager"""
        config = {
            "test_sequence": ["command1", "command2", "command3"],
            "conditional_sequence": [
                "if test_flag",
                "command1",
                "command2",
                "else",
                "command3",
                "command4",
                "endif"
            ],
            "stop_sequence": [
                "stop_if_not safety_flag",
                "command1",
                "command2"
            ],
            "nested_sequence": [
                "if outer_flag",
                "command1",
                "if inner_flag",
                "command2",
                "else",
                "command3",
                "endif",
                "command4",
                "endif"
            ]
        }
        buttons_config = {
            "button1": "cmd1",
            "button2": "cmd2"
        }
        return SequenceManager(config, buttons_config, flag_manager)
    
    def test_simple_conditional_execution_if_true(self, sequence_manager, mock_serial_manager):
        """Тест простого условного выполнения с if true"""
        # Устанавливаем флаг
        sequence_manager.set_flag("test_flag", True)
        
        # Получаем развернутую последовательность
        commands = sequence_manager.expand_sequence("conditional_sequence")
        
        # Создаем исполнитель
        executor = CommandSequenceExecutor(
            mock_serial_manager, commands, flag_manager=sequence_manager.flag_manager
        )
        
        with patch.object(executor, '_send_and_wait_command', return_value=True) as mock_send:
            executor.run()
            
            # Должны выполниться команды из if блока
            assert mock_send.call_count == 2
            mock_send.assert_any_call("command1")
            mock_send.assert_any_call("command2")
            # Команды из else блока не должны выполниться
            mock_send.assert_not_called_with("command3")
            mock_send.assert_not_called_with("command4")
    
    def test_simple_conditional_execution_if_false(self, sequence_manager, mock_serial_manager):
        """Тест простого условного выполнения с if false"""
        # Устанавливаем флаг в false
        sequence_manager.set_flag("test_flag", False)
        
        # Получаем развернутую последовательность
        commands = sequence_manager.expand_sequence("conditional_sequence")
        
        # Создаем исполнитель
        executor = CommandSequenceExecutor(
            mock_serial_manager, commands, flag_manager=sequence_manager.flag_manager
        )
        
        with patch.object(executor, '_send_and_wait_command', return_value=True) as mock_send:
            executor.run()
            
            # Должны выполниться команды из else блока
            assert mock_send.call_count == 2
            mock_send.assert_any_call("command3")
            mock_send.assert_any_call("command4")
            # Команды из if блока не должны выполниться
            mock_send.assert_not_called_with("command1")
            mock_send.assert_not_called_with("command2")
    
    def test_stop_if_not_true(self, sequence_manager, mock_serial_manager):
        """Тест stop_if_not с true условием"""
        # Устанавливаем флаг в true
        sequence_manager.set_flag("safety_flag", True)
        
        # Получаем развернутую последовательность
        commands = sequence_manager.expand_sequence("stop_sequence")
        
        # Создаем исполнитель
        executor = CommandSequenceExecutor(
            mock_serial_manager, commands, flag_manager=sequence_manager.flag_manager
        )
        
        with patch.object(executor, '_send_and_wait_command', return_value=True) as mock_send:
            with patch.object(executor, 'sequence_finished') as mock_finished:
                executor.run()
                
                # Все команды должны выполниться
                assert mock_send.call_count == 2
                mock_send.assert_any_call("command1")
                mock_send.assert_any_call("command2")
                
                # Последовательность должна завершиться успешно
                mock_finished.emit.assert_called_with(True, "Последовательность выполнена успешно")
    
    def test_stop_if_not_false(self, sequence_manager, mock_serial_manager):
        """Тест stop_if_not с false условием"""
        # Устанавливаем флаг в false
        sequence_manager.set_flag("safety_flag", False)
        
        # Получаем развернутую последовательность
        commands = sequence_manager.expand_sequence("stop_sequence")
        
        # Создаем исполнитель
        executor = CommandSequenceExecutor(
            mock_serial_manager, commands, flag_manager=sequence_manager.flag_manager
        )
        
        with patch.object(executor, '_send_and_wait_command', return_value=True) as mock_send:
            with patch.object(executor, 'sequence_finished') as mock_finished:
                executor.run()
                
                # Команды не должны выполниться
                assert mock_send.call_count == 0
                
                # Последовательность должна завершиться с ошибкой
                mock_finished.emit.assert_called_with(False, "Выполнение остановлено: флаг safety_flag = false")
    
    def test_nested_conditionals_both_true(self, sequence_manager, mock_serial_manager):
        """Тест вложенных условий - оба флага true"""
        # Устанавливаем оба флага в true
        sequence_manager.set_flag("outer_flag", True)
        sequence_manager.set_flag("inner_flag", True)
        
        # Получаем развернутую последовательность
        commands = sequence_manager.expand_sequence("nested_sequence")
        
        # Создаем исполнитель
        executor = CommandSequenceExecutor(
            mock_serial_manager, commands, flag_manager=sequence_manager.flag_manager
        )
        
        with patch.object(executor, '_send_and_wait_command', return_value=True) as mock_send:
            executor.run()
            
            # Должны выполниться command1, command2, command4
            assert mock_send.call_count == 3
            mock_send.assert_any_call("command1")
            mock_send.assert_any_call("command2")
            mock_send.assert_any_call("command4")
            # command3 не должна выполниться
            mock_send.assert_not_called_with("command3")
    
    def test_nested_conditionals_outer_true_inner_false(self, sequence_manager, mock_serial_manager):
        """Тест вложенных условий - внешний true, внутренний false"""
        # Устанавливаем флаги
        sequence_manager.set_flag("outer_flag", True)
        sequence_manager.set_flag("inner_flag", False)
        
        # Получаем развернутую последовательность
        commands = sequence_manager.expand_sequence("nested_sequence")
        
        # Создаем исполнитель
        executor = CommandSequenceExecutor(
            mock_serial_manager, commands, flag_manager=sequence_manager.flag_manager
        )
        
        with patch.object(executor, '_send_and_wait_command', return_value=True) as mock_send:
            executor.run()
            
            # Должны выполниться command1, command3, command4
            assert mock_send.call_count == 3
            mock_send.assert_any_call("command1")
            mock_send.assert_any_call("command3")
            mock_send.assert_any_call("command4")
            # command2 не должна выполниться
            mock_send.assert_not_called_with("command2")
    
    def test_nested_conditionals_outer_false(self, sequence_manager, mock_serial_manager):
        """Тест вложенных условий - внешний флаг false"""
        # Устанавливаем внешний флаг в false
        sequence_manager.set_flag("outer_flag", False)
        sequence_manager.set_flag("inner_flag", True)  # Не должно иметь значения
        
        # Получаем развернутую последовательность
        commands = sequence_manager.expand_sequence("nested_sequence")
        
        # Создаем исполнитель
        executor = CommandSequenceExecutor(
            mock_serial_manager, commands, flag_manager=sequence_manager.flag_manager
        )
        
        with patch.object(executor, '_send_and_wait_command', return_value=True) as mock_send:
            executor.run()
            
            # Ни одна команда не должна выполниться
            assert mock_send.call_count == 0
    
    def test_flag_persistence(self, sequence_manager):
        """Тест сохранения состояния флагов"""
        # Устанавливаем флаги
        sequence_manager.set_flag("test_flag", True)
        sequence_manager.set_flag("safety_flag", False)
        
        # Проверяем, что флаги сохранились
        assert sequence_manager.get_flag("test_flag") is True
        assert sequence_manager.get_flag("safety_flag") is False
        
        # Получаем все флаги
        all_flags = sequence_manager.get_all_flags()
        assert all_flags["test_flag"] is True
        assert all_flags["safety_flag"] is False
    
    def test_flag_default_values(self, sequence_manager):
        """Тест значений флагов по умолчанию"""
        # Проверяем, что несуществующие флаги возвращают значение по умолчанию
        assert sequence_manager.get_flag("nonexistent_flag", True) is True
        assert sequence_manager.get_flag("nonexistent_flag", False) is False
        assert sequence_manager.get_flag("nonexistent_flag") is False  # По умолчанию False
    
    def test_sequence_validation_with_conditionals(self, sequence_manager):
        """Тест валидации последовательности с условными командами"""
        # Валидируем корректную последовательность
        is_valid, errors = sequence_manager.validate_sequence("conditional_sequence")
        assert is_valid is True
        assert len(errors) == 0
        
        # Валидируем последовательность с stop_if_not
        is_valid, errors = sequence_manager.validate_sequence("stop_sequence")
        assert is_valid is True
        assert len(errors) == 0
    
    def test_sequence_info_with_conditionals(self, sequence_manager):
        """Тест получения информации о последовательности с условиями"""
        info = sequence_manager.get_sequence_info("conditional_sequence")
        assert info["exists"] is True
        assert info["command_count"] > 0
        assert "command1" in info["commands"]
        assert "if test_flag" in info["commands"]
        assert "else" in info["commands"]
        assert "endif" in info["commands"]
    
    def test_cancellation_during_conditional_execution(self, sequence_manager, mock_serial_manager):
        """Тест отмены во время условного выполнения"""
        # Устанавливаем флаг
        sequence_manager.set_flag("test_flag", True)
        
        # Получаем развернутую последовательность
        commands = sequence_manager.expand_sequence("conditional_sequence")
        
        # Создаем исполнитель с токеном отмены
        cancellation_token = CancellationToken()
        executor = CommandSequenceExecutor(
            mock_serial_manager, commands, 
            flag_manager=sequence_manager.flag_manager,
            cancellation_token=cancellation_token
        )
        
        with patch.object(executor, '_send_and_wait_command', return_value=True) as mock_send:
            with patch.object(executor, 'sequence_finished') as mock_finished:
                # Запускаем выполнение в отдельном потоке
                executor.start()
                
                # Даем немного времени на выполнение
                time.sleep(0.1)
                
                # Отменяем выполнение
                cancellation_token.cancel()
                
                # Ждем завершения
                executor.wait()
                
                # Проверяем, что выполнение было отменено
                mock_finished.emit.assert_called_with(False, "Выполнение прервано")
    
    def test_flag_manager_thread_safety(self, flag_manager):
        """Тест thread-safety FlagManager"""
        import threading
        import time
        
        # Создаем несколько потоков для одновременного изменения флагов
        def set_flags(thread_id):
            for i in range(10):
                flag_manager.set_flag(f"flag_{thread_id}_{i}", True)
                time.sleep(0.001)
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=set_flags, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Проверяем, что все флаги установлены корректно
        all_flags = flag_manager.get_all_flags()
        assert len(all_flags) == 50  # 5 потоков * 10 флагов
        
        for thread_id in range(5):
            for i in range(10):
                flag_name = f"flag_{thread_id}_{i}"
                assert flag_manager.get_flag(flag_name) is True