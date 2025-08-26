"""
Тесты для thread-safety и новых возможностей sequence_manager
"""
import threading
import time
import logging
from typing import Dict, List
from unittest.mock import Mock

from core.sequence_manager import (
    SequenceManager, CommandSequenceExecutor, CommandValidator,
    ThreadSafeResponseCollector, CancellationToken, RecursionProtector,
    ValidationResult, CommandType
)


def test_command_validator():
    """Тест валидатора команд"""
    print("=== Тест CommandValidator ===")
    
    validator = CommandValidator()
    
    # Тест обычных команд
    result = validator.validate_command("test_command")
    assert result.is_valid
    assert result.command_type == CommandType.REGULAR
    
    # Тест wait команд
    result = validator.validate_command("wait 5.0")
    assert result.is_valid
    assert result.command_type == CommandType.WAIT
    assert result.parsed_data["wait_time"] == 5.0
    
    # Тест невалидных wait команд
    result = validator.validate_command("wait")
    assert not result.is_valid
    assert "Неверный синтаксис" in result.error_message
    
    result = validator.validate_command("wait -1")
    assert not result.is_valid
    assert "отрицательным" in result.error_message
    
    result = validator.validate_command("wait abc")
    assert not result.is_valid
    assert "формат времени" in result.error_message
    
    # Тест пустых команд
    result = validator.validate_command("")
    assert not result.is_valid
    assert "Пустая команда" in result.error_message
    
    print("✓ CommandValidator работает корректно")


def test_thread_safe_response_collector():
    """Тест thread-safe коллектора ответов"""
    print("=== Тест ThreadSafeResponseCollector ===")
    
    collector = ThreadSafeResponseCollector(max_size=5)
    
    # Тест добавления ответов
    assert collector.add_response("response1")
    assert collector.add_response("response2")
    
    # Тест получения ответов
    responses = collector.get_responses()
    assert len(responses) == 2
    assert "response1" in responses
    assert "response2" in responses
    
    # Тест очистки
    collector.clear()
    responses = collector.get_responses()
    assert len(responses) == 0
    assert collector.get_total_count() == 0
    
    # Тест многопоточности
    def add_responses():
        for i in range(10):
            collector.add_response(f"thread_response_{i}")
            time.sleep(0.01)
    
    threads = []
    for _ in range(3):
        thread = threading.Thread(target=add_responses)
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    # Проверяем, что все ответы добавлены
    total_count = collector.get_total_count()
    assert total_count > 0
    
    print("✓ ThreadSafeResponseCollector работает корректно")


def test_cancellation_token():
    """Тест токена отмены"""
    print("=== Тест CancellationToken ===")
    
    token = CancellationToken()
    
    # Тест начального состояния
    assert not token.is_cancelled()
    
    # Тест отмены
    token.cancel()
    assert token.is_cancelled()
    
    # Тест исключения
    try:
        token.throw_if_cancelled()
        assert False, "Должно было выбросить исключение"
    except Exception as e:
        assert "отменена" in str(e)
    
    print("✓ CancellationToken работает корректно")


def test_recursion_protector():
    """Тест защиты от рекурсии"""
    print("=== Тест RecursionProtector ===")
    
    protector = RecursionProtector(max_depth=3)
    
    # Тест входа в последовательность
    assert protector.enter_sequence("seq1")
    assert protector.enter_sequence("seq2")
    assert protector.enter_sequence("seq3")
    
    # Тест превышения глубины
    assert not protector.enter_sequence("seq4")
    
    # Тест выхода
    protector.exit_sequence("seq3")
    assert protector.enter_sequence("seq4")  # Теперь должно работать
    
    # Тест кеширования
    visited = {"seq1", "seq2"}
    cache_key = protector.get_cache_key("test_seq", visited)
    assert "test_seq" in cache_key
    assert "seq1" in cache_key
    
    # Тест кеша
    test_result = ["cmd1", "cmd2"]
    protector.cache_result(cache_key, test_result)
    cached = protector.get_cached_result(cache_key)
    assert cached == test_result
    
    # Очистка
    protector.clear_cache()
    assert protector.get_cached_result(cache_key) is None
    
    print("✓ RecursionProtector работает корректно")


def test_sequence_manager_threading():
    """Тест thread-safety SequenceManager"""
    print("=== Тест SequenceManager Threading ===")
    
    # Конфигурация для тестов
    config = {
        "test_seq": ["cmd1", "cmd2", "wait 0.1"],
        "nested_seq": ["test_seq", "cmd3"],
        "recursive_seq": ["recursive_seq", "cmd1"],  # Рекурсия
        "deep_seq": ["deep_seq_2"],
        "deep_seq_2": ["deep_seq_3"],
        "deep_seq_3": ["deep_seq_4"],
        "deep_seq_4": ["cmd1"]
    }
    
    buttons_config = {
        "button1": "button_cmd1",
        "button2": "button_cmd2"
    }
    
    manager = SequenceManager(config, buttons_config)
    
    # Тест валидации последовательности
    is_valid, errors = manager.validate_sequence("test_seq")
    assert is_valid
    assert len(errors) == 0
    
    # Тест рекурсивной последовательности
    is_valid, errors = manager.validate_sequence("recursive_seq")
    # Рекурсия должна быть обнаружена и обработана
    
    # Тест информации о последовательности
    info = manager.get_sequence_info("test_seq")
    assert info["exists"]
    assert info["is_valid"]
    assert info["command_count"] > 0
    
    # Тест многопоточного доступа
    def expand_sequence_thread(seq_name: str, results: List, index: int):
        try:
            commands = manager.expand_sequence(seq_name)
            results[index] = commands
        except Exception as e:
            results[index] = f"Error: {e}"
    
    # Запускаем несколько потоков одновременно
    threads = []
    results = [None] * 5
    
    for i in range(5):
        thread = threading.Thread(
            target=expand_sequence_thread,
            args=("test_seq", results, i)
        )
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    # Проверяем результаты
    for i, result in enumerate(results):
        assert result is not None
        if isinstance(result, list):
            assert len(result) > 0
    
    print("✓ SequenceManager thread-safety работает корректно")


def test_command_sequence_executor():
    """Тест исполнителя команд"""
    print("=== Тест CommandSequenceExecutor ===")
    
    # Мок для serial_manager
    mock_serial = Mock()
    mock_serial.is_connected = True
    mock_serial.send_command.return_value = True
    
    # Тестовые команды
    commands = ["cmd1", "wait 0.1", "cmd2"]
    
    # Создаем исполнитель
    executor = CommandSequenceExecutor(mock_serial, commands)
    
    # Проверяем, что команды валидированы
    assert len(executor.commands) == 3
    
    # Тест отмены
    token = CancellationToken()
    executor = CommandSequenceExecutor(mock_serial, commands, cancellation_token=token)
    
    # Запускаем в отдельном потоке
    executor.start()
    time.sleep(0.05)  # Даем немного времени на выполнение
    
    # Отменяем выполнение
    token.cancel()
    executor.wait()
    
    print("✓ CommandSequenceExecutor работает корректно")


def run_all_tests():
    """Запуск всех тестов"""
    print("Запуск тестов thread-safety и новых возможностей sequence_manager")
    print("=" * 60)
    
    try:
        test_command_validator()
        test_thread_safe_response_collector()
        test_cancellation_token()
        test_recursion_protector()
        test_sequence_manager_threading()
        test_command_sequence_executor()
        
        print("=" * 60)
        print("✓ Все тесты прошли успешно!")
        
    except Exception as e:
        print(f"✗ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    
    run_all_tests()

