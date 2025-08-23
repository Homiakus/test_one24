"""
Unit тесты для CommandSequenceExecutor с поддержкой условного выполнения
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List

from core.sequence_manager import (
    CommandSequenceExecutor, FlagManager, SequenceKeywords,
    CancellationToken, ConditionalState
)


class TestCommandSequenceExecutor:
    """Тесты для CommandSequenceExecutor"""
    
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
    def cancellation_token(self):
        """Фикстура с CancellationToken"""
        return CancellationToken()
    
    @pytest.fixture
    def keywords(self):
        """Фикстура с SequenceKeywords"""
        return SequenceKeywords()
    
    @pytest.fixture
    def executor(self, mock_serial_manager, flag_manager, cancellation_token, keywords):
        """Фикстура с CommandSequenceExecutor"""
        commands = ["command1", "command2", "command3"]
        return CommandSequenceExecutor(
            mock_serial_manager, commands, keywords, cancellation_token, flag_manager
        )
    
    def test_executor_initialization(self, executor):
        """Тест инициализации CommandSequenceExecutor"""
        assert executor.serial_manager is not None
        assert executor.commands == ["command1", "command2", "command3"]
        assert executor.flag_manager is not None
        assert executor.conditional_state is not None
    
    def test_is_wait_command(self, executor):
        """Тест определения wait команды"""
        assert executor._is_wait_command("wait 5") is True
        assert executor._is_wait_command("wait 0.5") is True
        assert executor._is_wait_command("command1") is False
    
    def test_is_conditional_command(self, executor):
        """Тест определения условных команд"""
        assert executor._is_conditional_command("if flag1") is True
        assert executor._is_conditional_command("else") is True
        assert executor._is_conditional_command("endif") is True
        assert executor._is_conditional_command("command1") is False
    
    def test_is_stop_command(self, executor):
        """Тест определения stop команд"""
        assert executor._is_stop_command("stop_if_not flag1") is True
        assert executor._is_stop_command("command1") is False
    
    def test_handle_if_command_true(self, executor):
        """Тест обработки if команды с true условием"""
        executor.flag_manager.set_flag("test_flag", True)
        result = executor._handle_if_command("if test_flag")
        assert result is True
        assert executor.conditional_state.in_conditional_block is True
        assert executor.conditional_state.skip_until_endif is False
        assert len(executor.conditional_state.condition_stack) == 1
        assert executor.conditional_state.condition_stack[0] is True
    
    def test_handle_if_command_false(self, executor):
        """Тест обработки if команды с false условием"""
        executor.flag_manager.set_flag("test_flag", False)
        result = executor._handle_if_command("if test_flag")
        assert result is True
        assert executor.conditional_state.in_conditional_block is True
        assert executor.conditional_state.skip_until_endif is True
        assert len(executor.conditional_state.condition_stack) == 1
        assert executor.conditional_state.condition_stack[0] is False
    
    def test_handle_if_command_invalid(self, executor):
        """Тест обработки некорректной if команды"""
        result = executor._handle_if_command("if")
        assert result is False
    
    def test_handle_else_command(self, executor):
        """Тест обработки else команды"""
        # Сначала входим в условный блок
        executor.flag_manager.set_flag("test_flag", True)
        executor._handle_if_command("if test_flag")
        
        # Теперь обрабатываем else
        result = executor._handle_else_command("else")
        assert result is True
        assert executor.conditional_state.skip_until_endif is True
    
    def test_handle_else_command_without_if(self, executor):
        """Тест обработки else без if"""
        result = executor._handle_else_command("else")
        assert result is False
    
    def test_handle_endif_command(self, executor):
        """Тест обработки endif команды"""
        # Сначала входим в условный блок
        executor.flag_manager.set_flag("test_flag", True)
        executor._handle_if_command("if test_flag")
        
        # Теперь выходим
        result = executor._handle_endif_command("endif")
        assert result is True
        assert executor.conditional_state.in_conditional_block is False
        assert executor.conditional_state.skip_until_endif is False
        assert len(executor.conditional_state.condition_stack) == 0
    
    def test_handle_endif_command_without_if(self, executor):
        """Тест обработки endif без if"""
        result = executor._handle_endif_command("endif")
        assert result is False
    
    def test_handle_stop_command_true(self, executor):
        """Тест обработки stop_if_not с true условием"""
        executor.flag_manager.set_flag("test_flag", True)
        result = executor._handle_stop_command("stop_if_not test_flag")
        assert result is True
    
    def test_handle_stop_command_false(self, executor):
        """Тест обработки stop_if_not с false условием"""
        executor.flag_manager.set_flag("test_flag", False)
        result = executor._handle_stop_command("stop_if_not test_flag")
        assert result is False
    
    def test_handle_stop_command_invalid(self, executor):
        """Тест обработки некорректной stop_if_not команды"""
        result = executor._handle_stop_command("stop_if_not")
        assert result is False
    
    def test_handle_wait_command(self, executor):
        """Тест обработки wait команды"""
        with patch('time.sleep') as mock_sleep:
            result = executor._handle_wait_command("wait 0.1")
            assert result is True
            mock_sleep.assert_called()
    
    def test_handle_wait_command_invalid(self, executor):
        """Тест обработки некорректной wait команды"""
        result = executor._handle_wait_command("wait")
        assert result is False
    
    def test_handle_wait_command_cancelled(self, executor):
        """Тест обработки wait команды с отменой"""
        executor.cancellation_token.cancel()
        result = executor._handle_wait_command("wait 1")
        assert result is False
    
    def test_send_and_wait_command_success(self, executor):
        """Тест успешной отправки команды"""
        with patch.object(executor, '_wait_for_completion', return_value=True):
            result = executor._send_and_wait_command("test_command")
            assert result is True
            executor.serial_manager.send_command.assert_called_with("test_command")
    
    def test_send_and_wait_command_failure(self, executor):
        """Тест неудачной отправки команды"""
        executor.serial_manager.send_command.return_value = False
        result = executor._send_and_wait_command("test_command")
        assert result is False
    
    def test_wait_for_completion_success(self, executor):
        """Тест успешного ожидания завершения"""
        # Симулируем получение ответа с ключевым словом завершения
        executor.keywords.complete_line = ["complete"]
        executor.add_response("complete")
        
        result = executor._wait_for_completion("test_command", timeout=0.1)
        assert result is True
    
    def test_wait_for_completion_timeout(self, executor):
        """Тест таймаута ожидания завершения"""
        result = executor._wait_for_completion("test_command", timeout=0.1)
        assert result is False
    
    def test_wait_for_completion_error(self, executor):
        """Тест ошибки при ожидании завершения"""
        executor.keywords.error = ["error"]
        executor.add_response("error occurred")
        
        result = executor._wait_for_completion("test_command", timeout=0.1)
        assert result is False
    
    def test_wait_for_completion_cancelled(self, executor):
        """Тест отмены при ожидании завершения"""
        executor.cancellation_token.cancel()
        result = executor._wait_for_completion("test_command", timeout=0.1)
        assert result is False
    
    def test_set_flag(self, executor):
        """Тест установки флага"""
        with patch.object(executor, 'flag_changed') as mock_signal:
            executor.set_flag("test_flag", True)
            assert executor.flag_manager.get_flag("test_flag") is True
            mock_signal.emit.assert_called_with("test_flag", True)
    
    def test_get_flag(self, executor):
        """Тест получения флага"""
        executor.flag_manager.set_flag("test_flag", True)
        assert executor.get_flag("test_flag") is True
        assert executor.get_flag("unknown_flag", False) is False
    
    def test_get_all_flags(self, executor):
        """Тест получения всех флагов"""
        executor.flag_manager.set_flag("flag1", True)
        executor.flag_manager.set_flag("flag2", False)
        flags = executor.get_all_flags()
        assert flags["flag1"] is True
        assert flags["flag2"] is False
    
    def test_add_response(self, executor):
        """Тест добавления ответа"""
        with patch.object(executor, 'response_received') as mock_signal:
            executor.add_response("test response")
            mock_signal.emit.assert_called_with("test response")
    
    def test_stop(self, executor):
        """Тест остановки выполнения"""
        executor.stop()
        assert executor.cancellation_token.is_cancelled() is True


class TestConditionalExecution:
    """Тесты условного выполнения"""
    
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
    
    def test_conditional_execution_if_true(self, mock_serial_manager, flag_manager):
        """Тест условного выполнения с if true"""
        flag_manager.set_flag("test_flag", True)
        commands = ["if test_flag", "command1", "command2", "endif"]
        
        executor = CommandSequenceExecutor(
            mock_serial_manager, commands, flag_manager=flag_manager
        )
        
        with patch.object(executor, '_send_and_wait_command', return_value=True) as mock_send:
            executor.run()
            
            # Команды должны быть выполнены
            assert mock_send.call_count == 2
            mock_send.assert_any_call("command1")
            mock_send.assert_any_call("command2")
    
    def test_conditional_execution_if_false(self, mock_serial_manager, flag_manager):
        """Тест условного выполнения с if false"""
        flag_manager.set_flag("test_flag", False)
        commands = ["if test_flag", "command1", "command2", "endif"]
        
        executor = CommandSequenceExecutor(
            mock_serial_manager, commands, flag_manager=flag_manager
        )
        
        with patch.object(executor, '_send_and_wait_command', return_value=True) as mock_send:
            executor.run()
            
            # Команды не должны быть выполнены
            assert mock_send.call_count == 0
    
    def test_conditional_execution_if_else_true(self, mock_serial_manager, flag_manager):
        """Тест условного выполнения с if-else (true)"""
        flag_manager.set_flag("test_flag", True)
        commands = ["if test_flag", "command1", "else", "command2", "endif"]
        
        executor = CommandSequenceExecutor(
            mock_serial_manager, commands, flag_manager=flag_manager
        )
        
        with patch.object(executor, '_send_and_wait_command', return_value=True) as mock_send:
            executor.run()
            
            # Должна выполниться только command1
            assert mock_send.call_count == 1
            mock_send.assert_called_with("command1")
    
    def test_conditional_execution_if_else_false(self, mock_serial_manager, flag_manager):
        """Тест условного выполнения с if-else (false)"""
        flag_manager.set_flag("test_flag", False)
        commands = ["if test_flag", "command1", "else", "command2", "endif"]
        
        executor = CommandSequenceExecutor(
            mock_serial_manager, commands, flag_manager=flag_manager
        )
        
        with patch.object(executor, '_send_and_wait_command', return_value=True) as mock_send:
            executor.run()
            
            # Должна выполниться только command2
            assert mock_send.call_count == 1
            mock_send.assert_called_with("command2")
    
    def test_stop_if_not_true(self, mock_serial_manager, flag_manager):
        """Тест stop_if_not с true условием"""
        flag_manager.set_flag("test_flag", True)
        commands = ["stop_if_not test_flag", "command1", "command2"]
        
        executor = CommandSequenceExecutor(
            mock_serial_manager, commands, flag_manager=flag_manager
        )
        
        with patch.object(executor, '_send_and_wait_command', return_value=True) as mock_send:
            executor.run()
            
            # Все команды должны быть выполнены
            assert mock_send.call_count == 2
    
    def test_stop_if_not_false(self, mock_serial_manager, flag_manager):
        """Тест stop_if_not с false условием"""
        flag_manager.set_flag("test_flag", False)
        commands = ["stop_if_not test_flag", "command1", "command2"]
        
        executor = CommandSequenceExecutor(
            mock_serial_manager, commands, flag_manager=flag_manager
        )
        
        with patch.object(executor, '_send_and_wait_command', return_value=True) as mock_send:
            with patch.object(executor, 'sequence_finished') as mock_finished:
                executor.run()
                
                # Команды не должны быть выполнены
                assert mock_send.call_count == 0
                mock_finished.emit.assert_called_with(False, "Выполнение остановлено: флаг test_flag = false")
    
    def test_nested_conditionals(self, mock_serial_manager, flag_manager):
        """Тест вложенных условных блоков"""
        flag_manager.set_flag("flag1", True)
        flag_manager.set_flag("flag2", False)
        commands = [
            "if flag1",
            "command1",
            "if flag2",
            "command2",
            "else",
            "command3",
            "endif",
            "command4",
            "endif"
        ]
        
        executor = CommandSequenceExecutor(
            mock_serial_manager, commands, flag_manager=flag_manager
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
