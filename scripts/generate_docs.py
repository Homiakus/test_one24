#!/usr/bin/env python3
"""
Скрипт для автоматической генерации документации.

Этот скрипт генерирует документацию из исходного кода,
используя Sphinx и autodoc.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any


class DocumentationGenerator:
    """
    Генератор документации для проекта.
    
    Автоматически создает документацию из исходного кода,
    используя Sphinx и различные расширения.
    """
    
    def __init__(self, project_root: Path) -> None:
        """
        Инициализация генератора документации.
        
        Args:
            project_root: Корневая директория проекта
        """
        self.project_root = project_root
        self.docs_dir = project_root / "docs"
        self.api_dir = self.docs_dir / "api"
        
    def clean_docs(self) -> None:
        """
        Очистка старых файлов документации.
        
        Удаляет сгенерированные файлы API документации
        и временные файлы.
        """
        print("🧹 Очистка старых файлов документации...")
        
        # Удаляем старые API файлы
        if self.api_dir.exists():
            shutil.rmtree(self.api_dir)
        
        # Удаляем сгенерированные файлы
        build_dir = self.docs_dir / "_build"
        if build_dir.exists():
            shutil.rmtree(build_dir)
            
        print("✅ Очистка завершена")
    
    def create_api_structure(self) -> None:
        """
        Создание структуры API документации.
        
        Создает файлы .rst для каждого модуля проекта.
        """
        print("📁 Создание структуры API документации...")
        
        # Создаем директорию API
        self.api_dir.mkdir(exist_ok=True)
        
        # Модули для документирования
        modules = {
            "core": "Основные модули",
            "ui": "Пользовательский интерфейс",
            "utils": "Вспомогательные утилиты",
            "config": "Конфигурация"
        }
        
        for module_name, description in modules.items():
            self._create_module_doc(module_name, description)
            
        print("✅ Структура API создана")
    
    def _create_module_doc(self, module_name: str, description: str) -> None:
        """
        Создание документации для модуля.
        
        Args:
            module_name: Имя модуля
            description: Описание модуля
        """
        rst_file = self.api_dir / f"{module_name}.rst"
        
        content = f"""
{description}
{'=' * len(description)}

.. automodule:: {module_name}
   :members:
   :undoc-members:
   :show-inheritance:

"""
        
        # Добавляем подмодули
        module_path = self.project_root / module_name
        if module_path.exists() and module_path.is_dir():
            for item in module_path.iterdir():
                if item.is_file() and item.suffix == '.py' and not item.name.startswith('__'):
                    submodule_name = f"{module_name}.{item.stem}"
                    content += f"""
.. automodule:: {submodule_name}
   :members:
   :undoc-members:
   :show-inheritance:

"""
        
        rst_file.write_text(content, encoding='utf-8')
    
    def run_sphinx(self, target: str = "html") -> bool:
        """
        Запуск Sphinx для генерации документации.
        
        Args:
            target: Цель генерации (html, pdf, etc.)
            
        Returns:
            True если генерация успешна, False в противном случае
        """
        print(f"🔨 Генерация документации ({target})...")
        
        try:
            result = subprocess.run(
                ["sphinx-build", "-b", target, "docs", f"docs/_build/{target}"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            print("✅ Документация сгенерирована успешно")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка генерации документации: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            return False
        except FileNotFoundError:
            print("❌ Sphinx не найден. Установите: pip install sphinx")
            return False
    
    def run_type_check(self) -> bool:
        """
        Запуск проверки типов с помощью mypy.
        
        Returns:
            True если проверка прошла успешно, False в противном случае
        """
        print("🔍 Проверка типов...")
        
        try:
            result = subprocess.run(
                ["mypy", "core", "ui", "utils", "main.py"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                print("✅ Проверка типов прошла успешно")
                return True
            else:
                print("⚠️  Найдены ошибки типизации:")
                print(result.stdout)
                print(result.stderr)
                return False
                
        except FileNotFoundError:
            print("❌ mypy не найден. Установите: pip install mypy")
            return False
    
    def generate_coverage_report(self) -> None:
        """
        Генерация отчета о покрытии документацией.
        """
        print("📊 Генерация отчета о покрытии...")
        
        try:
            result = subprocess.run(
                ["sphinx-coverage", "-d", "docs/_build/html"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                print("✅ Отчет о покрытии сгенерирован")
            else:
                print("⚠️  Не удалось сгенерировать отчет о покрытии")
                
        except FileNotFoundError:
            print("⚠️  sphinx-coverage не найден")
    
    def generate_all(self, target: str = "html") -> bool:
        """
        Полная генерация документации.
        
        Args:
            target: Цель генерации документации
            
        Returns:
            True если все этапы прошли успешно
        """
        print("🚀 Начало генерации документации...")
        
        # Очистка
        self.clean_docs()
        
        # Создание структуры
        self.create_api_structure()
        
        # Проверка типов
        type_check_ok = self.run_type_check()
        
        # Генерация документации
        docs_ok = self.run_sphinx(target)
        
        # Отчет о покрытии
        if docs_ok:
            self.generate_coverage_report()
        
        success = docs_ok
        if not type_check_ok:
            print("⚠️  Генерация завершена с предупреждениями о типах")
        
        print(f"🎉 Генерация документации завершена: {'успешно' if success else 'с ошибками'}")
        return success


def main() -> None:
    """
    Главная функция скрипта.
    """
    project_root = Path(__file__).parent.parent
    generator = DocumentationGenerator(project_root)
    
    # Определяем цель из аргументов командной строки
    target = "html"
    if len(sys.argv) > 1:
        target = sys.argv[1]
    
    success = generator.generate_all(target)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
