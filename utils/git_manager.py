"""
Менеджер Git операций
"""
import logging
import subprocess
from pathlib import Path
from typing import Optional, List


class GitManager:
    """Менеджер для работы с Git"""

    def __init__(self, repo_path: Optional[Path] = None):
        """
        Инициализация менеджера Git

        Args:
            repo_path: Путь к репозиторию
        """
        self.repo_path = repo_path or Path.cwd()
        self.logger = logging.getLogger(__name__)

    def is_git_repo(self) -> bool:
        """Проверка, является ли директория Git репозиторием"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def get_current_branch(self) -> Optional[str]:
        """Получение текущей ветки"""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None

    def get_status(self) -> List[str]:
        """Получение статуса репозитория"""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return []

    def pull(self, remote: str = 'origin', branch: str = 'main') -> bool:
        """Выполнение git pull"""
        try:
            result = subprocess.run(
                ['git', 'pull', remote, branch],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            success = result.returncode == 0
            if success:
                self.logger.info(f"Git pull выполнен успешно: {remote}/{branch}")
            else:
                self.logger.error(f"Ошибка git pull: {result.stderr}")
            return success
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.error(f"Ошибка выполнения git pull: {e}")
            return False

    def push(self, remote: str = 'origin', branch: str = 'main') -> bool:
        """Выполнение git push"""
        try:
            result = subprocess.run(
                ['git', 'push', remote, branch],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            success = result.returncode == 0
            if success:
                self.logger.info(f"Git push выполнен успешно: {remote}/{branch}")
            else:
                self.logger.error(f"Ошибка git push: {result.stderr}")
            return success
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.error(f"Ошибка выполнения git push: {e}")
            return False
