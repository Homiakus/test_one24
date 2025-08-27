"""
Тесты для типов DI системы.
"""

import pytest
from unittest.mock import Mock
from typing import Dict, Any

from core.di.types import ServiceLifecycle, ServiceRegistration, ServiceInstance


class MockInterface:
    """Мок интерфейс для тестирования"""
    pass


class MockImplementation(MockInterface):
    """Мок реализация для тестирования"""
    pass


class TestServiceLifecycle:
    """Тесты для перечисления жизненных циклов"""
    
    def test_lifecycle_values(self):
        """Проверка значений жизненных циклов"""
        assert ServiceLifecycle.SINGLETON.value == "singleton"
        assert ServiceLifecycle.TRANSIENT.value == "transient"
        assert ServiceLifecycle.SCOPED.value == "scoped"
    
    def test_lifecycle_enumeration(self):
        """Проверка перечисления жизненных циклов"""
        lifecycles = list(ServiceLifecycle)
        assert len(lifecycles) == 3
        assert ServiceLifecycle.SINGLETON in lifecycles
        assert ServiceLifecycle.TRANSIENT in lifecycles
        assert ServiceLifecycle.SCOPED in lifecycles


class TestServiceRegistration:
    """Тесты для регистрации сервиса"""
    
    def test_valid_registration(self):
        """Проверка валидной регистрации"""
        registration = ServiceRegistration(
            interface=MockInterface,
            implementation=MockImplementation
        )
        
        assert registration.interface == MockInterface
        assert registration.implementation == MockImplementation
        assert registration.lifecycle == ServiceLifecycle.SINGLETON
        assert registration.factory is None
        assert registration.dependencies is None
        assert registration.metadata == {}
    
    def test_registration_with_factory(self):
        """Проверка регистрации с фабричной функцией"""
        def mock_factory():
            return MockImplementation()
        
        registration = ServiceRegistration(
            interface=MockInterface,
            implementation=MockImplementation,
            factory=mock_factory
        )
        
        assert registration.factory == mock_factory
    
    def test_registration_with_dependencies(self):
        """Проверка регистрации с зависимостями"""
        dependencies = {"param1": MockInterface}
        
        registration = ServiceRegistration(
            interface=MockInterface,
            implementation=MockImplementation,
            dependencies=dependencies
        )
        
        assert registration.dependencies == dependencies
    
    def test_registration_with_metadata(self):
        """Проверка регистрации с метаданными"""
        metadata = {"version": "1.0", "author": "test"}
        
        registration = ServiceRegistration(
            interface=MockInterface,
            implementation=MockImplementation,
            metadata=metadata
        )
        
        assert registration.metadata == metadata
    
    def test_registration_transient_lifecycle(self):
        """Проверка регистрации с transient жизненным циклом"""
        registration = ServiceRegistration(
            interface=MockInterface,
            implementation=MockImplementation,
            lifecycle=ServiceLifecycle.TRANSIENT
        )
        
        assert registration.lifecycle == ServiceLifecycle.TRANSIENT
    
    def test_invalid_registration_same_interface_implementation(self):
        """Проверка ошибки при одинаковых интерфейсе и реализации"""
        with pytest.raises(ValueError, match="не могут быть одинаковыми"):
            ServiceRegistration(
                interface=MockInterface,
                implementation=MockInterface
            )
    
    def test_invalid_registration_invalid_factory(self):
        """Проверка ошибки при невалидной фабричной функции"""
        with pytest.raises(ValueError, match="должна быть вызываемой"):
            ServiceRegistration(
                interface=MockInterface,
                implementation=MockImplementation,
                factory="not_callable"
            )
    
    def test_invalid_registration_invalid_dependencies(self):
        """Проверка ошибки при невалидных зависимостях"""
        with pytest.raises(ValueError, match="должны быть словарем"):
            ServiceRegistration(
                interface=MockInterface,
                implementation=MockImplementation,
                dependencies="not_dict"
            )


class TestServiceInstance:
    """Тесты для экземпляра сервиса"""
    
    def test_service_instance_creation(self):
        """Проверка создания экземпляра сервиса"""
        registration = ServiceRegistration(
            interface=MockInterface,
            implementation=MockImplementation
        )
        
        instance = ServiceInstance(registration=registration)
        
        assert instance.registration == registration
        assert instance.instance is None
        assert instance.factory_instance is None
        assert instance.created_at is not None
        assert instance.last_accessed is None
        assert instance.access_count == 0
    
    def test_has_instance_false(self):
        """Проверка has_instance когда экземпляр не создан"""
        registration = ServiceRegistration(
            interface=MockInterface,
            implementation=MockImplementation
        )
        
        instance = ServiceInstance(registration=registration)
        
        assert not instance.has_instance()
    
    def test_has_instance_true(self):
        """Проверка has_instance когда экземпляр создан"""
        registration = ServiceRegistration(
            interface=MockInterface,
            implementation=MockImplementation
        )
        
        mock_obj = Mock()
        instance = ServiceInstance(
            registration=registration,
            instance=mock_obj
        )
        
        assert instance.has_instance()
        assert instance.instance == mock_obj
    
    def test_is_singleton_true(self):
        """Проверка is_singleton для singleton сервиса"""
        registration = ServiceRegistration(
            interface=MockInterface,
            implementation=MockImplementation,
            lifecycle=ServiceLifecycle.SINGLETON
        )
        
        instance = ServiceInstance(registration=registration)
        
        assert instance.is_singleton()
    
    def test_is_singleton_false(self):
        """Проверка is_singleton для transient сервиса"""
        registration = ServiceRegistration(
            interface=MockInterface,
            implementation=MockImplementation,
            lifecycle=ServiceLifecycle.TRANSIENT
        )
        
        instance = ServiceInstance(registration=registration)
        
        assert not instance.is_singleton()
    
    def test_can_reuse_instance_singleton_with_instance(self):
        """Проверка can_reuse_instance для singleton с экземпляром"""
        registration = ServiceRegistration(
            interface=MockInterface,
            implementation=MockImplementation,
            lifecycle=ServiceLifecycle.SINGLETON
        )
        
        mock_obj = Mock()
        instance = ServiceInstance(
            registration=registration,
            instance=mock_obj
        )
        
        assert instance.can_reuse_instance()
    
    def test_can_reuse_instance_singleton_without_instance(self):
        """Проверка can_reuse_instance для singleton без экземпляра"""
        registration = ServiceRegistration(
            interface=MockInterface,
            implementation=MockImplementation,
            lifecycle=ServiceLifecycle.SINGLETON
        )
        
        instance = ServiceInstance(registration=registration)
        
        assert not instance.can_reuse_instance()
    
    def test_can_reuse_instance_transient(self):
        """Проверка can_reuse_instance для transient сервиса"""
        registration = ServiceRegistration(
            interface=MockInterface,
            implementation=MockImplementation,
            lifecycle=ServiceLifecycle.TRANSIENT
        )
        
        mock_obj = Mock()
        instance = ServiceInstance(
            registration=registration,
            instance=mock_obj
        )
        
        assert not instance.can_reuse_instance()

