#!/usr/bin/env python3
"""
Скрипт для проверки типизации в проекте.
"""
import ast
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Union


class TypeChecker:
    """
    Простой проверщик типизации на основе AST.
    """
    
    def __init__(self) -> None:
        """Инициализация проверщика."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def check_file(self, file_path: Path) -> None:
        """
        Проверка типизации в файле.
        
        Args:
            file_path: Путь к файлу для проверки
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            self._check_ast(tree, file_path)
            
        except SyntaxError as e:
            self.errors.append(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            self.errors.append(f"Error parsing {file_path}: {e}")
    
    def _check_ast(self, tree: ast.AST, file_path: Path) -> None:
        """
        Проверка AST дерева.
        
        Args:
            tree: AST дерево
            file_path: Путь к файлу
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._check_function(node, file_path)
            elif isinstance(node, ast.AsyncFunctionDef):
                self._check_function(node, file_path)
            elif isinstance(node, ast.ClassDef):
                self._check_class(node, file_path)
    
    def _check_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], file_path: Path) -> None:
        """
        Проверка функции.
        
        Args:
            node: Узел функции
            file_path: Путь к файлу
        """
        # Проверяем наличие docstring
        if not self._has_docstring(node):
            self.warnings.append(f"Function {node.name} in {file_path} has no docstring")
        
        # Проверяем type hints
        if node.returns is None:
            self.warnings.append(f"Function {node.name} in {file_path} has no return type hint")
        
        # Проверяем параметры
        for arg in node.args.args:
            if arg.annotation is None:
                self.warnings.append(f"Parameter {arg.arg} in function {node.name} in {file_path} has no type hint")
    
    def _check_class(self, node: ast.ClassDef, file_path: Path) -> None:
        """
        Проверка класса.
        
        Args:
            node: Узел класса
            file_path: Путь к файлу
        """
        # Проверяем наличие docstring
        if not self._has_docstring(node):
            self.warnings.append(f"Class {node.name} in {file_path} has no docstring")
        
        # Проверяем методы
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self._check_function(item, file_path)
    
    def _has_docstring(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]) -> bool:
        """
        Проверка наличия docstring.
        
        Args:
            node: Узел для проверки
            
        Returns:
            True если есть docstring
        """
        if not node.body:
            return False
        
        first_item = node.body[0]
        return (isinstance(first_item, ast.Expr) and 
                isinstance(first_item.value, ast.Constant) and
                isinstance(first_item.value.value, str))
    
    def print_report(self) -> None:
        """Вывод отчета о проверке."""
        print("=" * 60)
        print("ОТЧЕТ О ПРОВЕРКЕ ТИПИЗАЦИИ")
        print("=" * 60)
        
        if self.errors:
            print(f"\n❌ ОШИБКИ ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        else:
            print("\n✅ Ошибок не найдено")
        
        if self.warnings:
            print(f"\n⚠️  ПРЕДУПРЕЖДЕНИЯ ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
        else:
            print("\n✅ Предупреждений не найдено")
        
        print(f"\n📊 ИТОГО: {len(self.errors)} ошибок, {len(self.warnings)} предупреждений")


def main() -> None:
    """Главная функция."""
    checker = TypeChecker()
    
    # Проверяем основные модули
    modules = ["core", "ui", "utils"]
    
    for module in modules:
        module_path = Path(module)
        if module_path.exists():
            for py_file in module_path.rglob("*.py"):
                if not py_file.name.startswith("__"):
                    checker.check_file(py_file)
    
    # Проверяем main.py
    main_file = Path("main.py")
    if main_file.exists():
        checker.check_file(main_file)
    
    checker.print_report()
    
    # Возвращаем код ошибки если есть ошибки
    sys.exit(1 if checker.errors else 0)


if __name__ == "__main__":
    main()
