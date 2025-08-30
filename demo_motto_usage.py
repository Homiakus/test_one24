#!/usr/bin/env python3
"""
Демонстрация использования MOTTO конфигурации

Показывает, как использовать новую MOTTO конфигурацию для вызова функций,
меню и последовательностей
"""

import tomli
from core.motto import MOTTOParser


class MOTTOController:
    """Контроллер для работы с MOTTO конфигурацией"""
    
    def __init__(self, config_file='config_motto_fixed.toml'):
        """Инициализация контроллера"""
        self.parser = MOTTOParser()
        self.config = self.parser.parse_config(config_file)
        
        # Загружаем также как обычный TOML для совместимости
        with open(config_file, 'rb') as f:
            self.toml_config = tomli.load(f)
        
        print(f"✅ MOTTO контроллер инициализирован (версия {self.config.version})")
    
    def get_serial_settings(self):
        """Получение настроек Serial"""
        serial = self.toml_config['serial_default']
        return {
            'port': serial['port'],
            'baudrate': serial['baudrate'],
            'timeout': serial['timeout']
        }
    
    def get_wizard_menu(self, step_id=1):
        """Получение меню wizard"""
        wizard = self.toml_config['wizard']
        for step in wizard['step']:
            if step['id'] == step_id:
                return {
                    'title': step['title'],
                    'buttons': step['buttons'],
                    'sequence': step['sequence'],
                    'autoNext': step['autoNext']
                }
        return None
    
    def execute_command(self, command_name):
        """Выполнение команды"""
        commands = self.toml_config['commands']
        if command_name in commands:
            command = commands[command_name]
            print(f"🔧 Выполняю команду '{command_name}': {command}")
            # Здесь была бы реальная отправка команды на UART
            return True
        else:
            print(f"❌ Команда '{command_name}' не найдена")
            return False
    
    def execute_sequence(self, sequence_name):
        """Выполнение последовательности"""
        sequences = self.toml_config['sequences']
        if sequence_name in sequences:
            sequence = sequences[sequence_name]
            steps = sequence['steps']
            policy = sequence['policy']
            guards = sequence['guards']
            
            print(f"🚀 Выполняю последовательность '{sequence_name}'")
            print(f"   Политика: {policy}")
            print(f"   Гварды: {guards}")
            print(f"   Шаги: {len(steps)}")
            
            # Проверяем гварды (в реальности здесь была бы проверка условий)
            print("   🔒 Проверка гвардов...")
            for guard in guards:
                print(f"     ✅ {guard}: OK")
            
            # Выполняем шаги
            for i, step in enumerate(steps, 1):
                print(f"   📋 Шаг {i}: {step}")
                if step.startswith('wait '):
                    wait_time = int(step.split()[1])
                    print(f"     ⏳ Ожидание {wait_time} секунд...")
                else:
                    self.execute_command(step)
            
            print(f"✅ Последовательность '{sequence_name}' завершена")
            return True
        else:
            print(f"❌ Последовательность '{sequence_name}' не найдена")
            return False
    
    def show_main_menu(self):
        """Показать главное меню"""
        menu = self.get_wizard_menu(1)
        if menu:
            print(f"\n📋 {menu['title']}")
            print("=" * 50)
            for i, button in enumerate(menu['buttons'], 1):
                print(f"{i}. {button['text']}")
            print("0. Выход")
            return menu
        return None
    
    def handle_menu_choice(self, choice, menu):
        """Обработка выбора в меню"""
        if choice == 0:
            print("👋 До свидания!")
            return False
        
        if 1 <= choice <= len(menu['buttons']):
            button = menu['buttons'][choice - 1]
            next_step = button['next']
            
            print(f"🎯 Выбрано: {button['text']}")
            
            # Получаем следующий шаг
            next_menu = self.get_wizard_menu(next_step)
            if next_menu and next_menu['sequence']:
                # Выполняем последовательность
                self.execute_sequence(next_menu['sequence'])
            
            return True
        
        print("❌ Неверный выбор")
        return True
    
    def list_available_commands(self):
        """Список доступных команд"""
        commands = self.toml_config['commands']
        print(f"\n📋 Доступные команды ({len(commands)}):")
        print("=" * 50)
        for name, command in commands.items():
            print(f"  {name}: {command}")
    
    def list_available_sequences(self):
        """Список доступных последовательностей"""
        sequences = self.toml_config['sequences']
        print(f"\n📋 Доступные последовательности ({len(sequences)}):")
        print("=" * 50)
        for name, sequence in sequences.items():
            steps = sequence['steps']
            policy = sequence['policy']
            print(f"  {name}: {len(steps)} шагов, политика: {policy}")
    
    def get_system_info(self):
        """Информация о системе"""
        print(f"\n📊 Информация о системе:")
        print("=" * 50)
        print(f"  Версия MOTTO: {self.config.version}")
        print(f"  Команд: {len(self.toml_config['commands'])}")
        print(f"  Последовательностей: {len(self.toml_config['sequences'])}")
        print(f"  Условий: {len(self.config.conditions)}")
        print(f"  Гвардов: {len(self.config.guards)}")
        print(f"  Политик: {len(self.config.policies)}")
        print(f"  Ресурсов: {len(self.config.resources)}")
        print(f"  Событий: {len(self.config.events)}")
        print(f"  Обработчиков: {len(self.config.handlers)}")
        
        # Serial настройки
        serial = self.get_serial_settings()
        print(f"  Serial порт: {serial['port']}")
        print(f"  Скорость: {serial['baudrate']}")
        print(f"  Таймаут: {serial['timeout']}с")


def interactive_demo():
    """Интерактивная демонстрация"""
    print("🎯 ДЕМОНСТРАЦИЯ MOTTO КОНТРОЛЛЕРА")
    print("=" * 60)
    
    controller = MOTTOController()
    
    while True:
        print("\n" + "=" * 60)
        print("📋 ВЫБЕРИТЕ ДЕЙСТВИЕ:")
        print("1. Показать главное меню")
        print("2. Выполнить команду")
        print("3. Выполнить последовательность")
        print("4. Список команд")
        print("5. Список последовательностей")
        print("6. Информация о системе")
        print("0. Выход")
        
        try:
            choice = int(input("\nВаш выбор: "))
            
            if choice == 0:
                print("👋 До свидания!")
                break
            elif choice == 1:
                menu = controller.show_main_menu()
                if menu:
                    try:
                        menu_choice = int(input("Выберите пункт меню: "))
                        controller.handle_menu_choice(menu_choice, menu)
                    except ValueError:
                        print("❌ Неверный ввод")
            elif choice == 2:
                command = input("Введите имя команды: ")
                controller.execute_command(command)
            elif choice == 3:
                sequence = input("Введите имя последовательности: ")
                controller.execute_sequence(sequence)
            elif choice == 4:
                controller.list_available_commands()
            elif choice == 5:
                controller.list_available_sequences()
            elif choice == 6:
                controller.get_system_info()
            else:
                print("❌ Неверный выбор")
                
        except ValueError:
            print("❌ Неверный ввод")
        except KeyboardInterrupt:
            print("\n👋 До свидания!")
            break


def quick_demo():
    """Быстрая демонстрация"""
    print("🚀 БЫСТРАЯ ДЕМОНСТРАЦИЯ MOTTO")
    print("=" * 50)
    
    controller = MOTTOController()
    
    # Показываем информацию о системе
    controller.get_system_info()
    
    # Показываем главное меню
    print("\n" + "=" * 50)
    controller.show_main_menu()
    
    # Выполняем несколько команд
    print("\n" + "=" * 50)
    print("🔧 ДЕМОНСТРАЦИЯ КОМАНД:")
    controller.execute_command('multi_og')
    controller.execute_command('pump_on')
    controller.execute_command('kl1_on')
    
    # Выполняем последовательность
    print("\n" + "=" * 50)
    print("🚀 ДЕМОНСТРАЦИЯ ПОСЛЕДОВАТЕЛЬНОСТИ:")
    controller.execute_sequence('load_tubes')
    
    print("\n✅ Демонстрация завершена!")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        interactive_demo()
    else:
        quick_demo()