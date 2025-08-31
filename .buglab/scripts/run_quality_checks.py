#!/usr/bin/env python3
"""
Quality Check Runner for Fixer & Orchestrator v3.0
Automatically runs all quality checks and generates reports.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.buglab/logs/quality_checks.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class QualityChecker:
    """Main class for running quality checks."""
    
    def __init__(self, config_dir: str = ".buglab/configs"):
        self.config_dir = Path(config_dir)
        self.logs_dir = Path(".buglab/logs")
        self.results: Dict[str, Dict] = {}
        self.start_time = time.time()
        
        # Ensure directories exist
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def run_command(self, command: List[str], timeout: int = 300) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, and stderr."""
        try:
            logger.info(f"Running command: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path.cwd()
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout} seconds: {' '.join(command)}")
            return -1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            logger.error(f"Error running command {' '.join(command)}: {e}")
            return -1, "", str(e)
    
    def check_mypy(self) -> Dict:
        """Run MyPy type checking."""
        logger.info("Running MyPy type checking...")
        
        command = ["mypy", ".", "--config-file", "mypy.ini", "--show-error-codes"]
        exit_code, stdout, stderr = self.run_command(command, timeout=120)
        
        # Count errors
        error_count = stdout.count("error:")
        warning_count = stdout.count("warning:")
        
        result = {
            "tool": "mypy",
            "exit_code": exit_code,
            "error_count": error_count,
            "warning_count": warning_count,
            "output": stdout,
            "error_output": stderr,
            "success": exit_code == 0,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"MyPy completed: {error_count} errors, {warning_count} warnings")
        return result
    
    def check_ruff(self) -> Dict:
        """Run Ruff linting."""
        logger.info("Running Ruff linting...")
        
        command = ["ruff", "check", ".", "--output-format=json"]
        exit_code, stdout, stderr = self.run_command(command, timeout=60)
        
        try:
            issues = json.loads(stdout) if stdout else []
            error_count = len([i for i in issues if i.get("code", "").startswith("E")])
            warning_count = len([i for i in issues if i.get("code", "").startswith("W")])
        except json.JSONDecodeError:
            error_count = warning_count = 0
            issues = []
        
        result = {
            "tool": "ruff",
            "exit_code": exit_code,
            "error_count": error_count,
            "warning_count": warning_count,
            "issues": issues,
            "output": stdout,
            "error_output": stderr,
            "success": exit_code == 0,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Ruff completed: {error_count} errors, {warning_count} warnings")
        return result
    
    def check_black(self) -> Dict:
        """Run Black formatting check."""
        logger.info("Running Black formatting check...")
        
        command = ["black", "--check", "--line-length=100", "."]
        exit_code, stdout, stderr = self.run_command(command, timeout=60)
        
        result = {
            "tool": "black",
            "exit_code": exit_code,
            "output": stdout,
            "error_output": stderr,
            "success": exit_code == 0,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Black completed: {'✓' if exit_code == 0 else '✗'}")
        return result
    
    def check_bandit(self) -> Dict:
        """Run Bandit security scanning."""
        logger.info("Running Bandit security scan...")
        
        command = ["bandit", "-r", ".", "-f", "json", "-o", ".buglab/logs/bandit-results.json"]
        exit_code, stdout, stderr = self.run_command(command, timeout=120)
        
        try:
            with open(".buglab/logs/bandit-results.json", "r") as f:
                bandit_results = json.load(f)
            issues = bandit_results.get("results", [])
            high_issues = len([i for i in issues if i.get("issue_severity") == "HIGH"])
            medium_issues = len([i for i in issues if i.get("issue_severity") == "MEDIUM"])
            low_issues = len([i for i in issues if i.get("issue_severity") == "LOW"])
        except (FileNotFoundError, json.JSONDecodeError):
            high_issues = medium_issues = low_issues = 0
            issues = []
        
        result = {
            "tool": "bandit",
            "exit_code": exit_code,
            "high_issues": high_issues,
            "medium_issues": medium_issues,
            "low_issues": low_issues,
            "total_issues": len(issues),
            "issues": issues,
            "output": stdout,
            "error_output": stderr,
            "success": exit_code == 0,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Bandit completed: {high_issues} high, {medium_issues} medium, {low_issues} low issues")
        return result
    
    def check_tests(self) -> Dict:
        """Run pytest with coverage."""
        logger.info("Running pytest with coverage...")
        
        command = [
            "pytest", 
            "--cov=.", 
            "--cov-report=json:.buglab/logs/coverage.json",
            "--cov-report=html:.buglab/logs/htmlcov",
            "--cov-fail-under=80"
        ]
        exit_code, stdout, stderr = self.run_command(command, timeout=300)
        
        # Parse coverage from JSON
        try:
            with open(".buglab/logs/coverage.json", "r") as f:
                coverage_data = json.load(f)
            total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
        except (FileNotFoundError, json.JSONDecodeError):
            total_coverage = 0
        
        result = {
            "tool": "pytest",
            "exit_code": exit_code,
            "coverage_percent": total_coverage,
            "output": stdout,
            "error_output": stderr,
            "success": exit_code == 0,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Pytest completed: {total_coverage:.1f}% coverage")
        return result
    
    def check_semgrep(self) -> Dict:
        """Run Semgrep security scanning."""
        logger.info("Running Semgrep security scan...")
        
        config_file = self.config_dir / "semgrep.yml"
        if not config_file.exists():
            logger.warning("Semgrep config file not found, skipping...")
            return {
                "tool": "semgrep",
                "exit_code": -1,
                "output": "",
                "error_output": "Config file not found",
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
        
        command = ["semgrep", "--config", str(config_file), "--json", "--output", ".buglab/logs/semgrep-results.json"]
        exit_code, stdout, stderr = self.run_command(command, timeout=180)
        
        try:
            with open(".buglab/logs/semgrep-results.json", "r") as f:
                semgrep_results = json.load(f)
            findings = semgrep_results.get("results", [])
            high_findings = len([f for f in findings if f.get("extra", {}).get("severity") == "ERROR"])
            medium_findings = len([f for f in findings if f.get("extra", {}).get("severity") == "WARNING"])
            low_findings = len([f for f in findings if f.get("extra", {}).get("severity") == "INFO"])
        except (FileNotFoundError, json.JSONDecodeError):
            high_findings = medium_findings = low_findings = 0
            findings = []
        
        result = {
            "tool": "semgrep",
            "exit_code": exit_code,
            "high_findings": high_findings,
            "medium_findings": medium_findings,
            "low_findings": low_findings,
            "total_findings": len(findings),
            "findings": findings,
            "output": stdout,
            "error_output": stderr,
            "success": exit_code == 0,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Semgrep completed: {high_findings} high, {medium_findings} medium, {low_findings} low findings")
        return result
    
    def run_all_checks(self) -> Dict:
        """Run all quality checks."""
        logger.info("Starting quality checks...")
        
        checks = [
            ("mypy", self.check_mypy),
            ("ruff", self.check_ruff),
            ("black", self.check_black),
            ("bandit", self.check_bandit),
            ("pytest", self.check_tests),
            ("semgrep", self.check_semgrep)
        ]
        
        for name, check_func in checks:
            try:
                self.results[name] = check_func()
            except Exception as e:
                logger.error(f"Error running {name}: {e}")
                self.results[name] = {
                    "tool": name,
                    "exit_code": -1,
                    "output": "",
                    "error_output": str(e),
                    "success": False,
                    "timestamp": datetime.now().isoformat()
                }
        
        return self.results
    
    def generate_report(self) -> str:
        """Generate a comprehensive quality report."""
        logger.info("Generating quality report...")
        
        total_time = time.time() - self.start_time
        
        # Calculate summary statistics
        total_errors = sum(r.get("error_count", 0) for r in self.results.values())
        total_warnings = sum(r.get("warning_count", 0) for r in self.results.values())
        successful_checks = sum(1 for r in self.results.values() if r.get("success", False))
        total_checks = len(self.results)
        
        # Get coverage
        coverage = self.results.get("pytest", {}).get("coverage_percent", 0)
        
        # Get security issues
        bandit_high = self.results.get("bandit", {}).get("high_issues", 0)
        semgrep_high = self.results.get("semgrep", {}).get("high_findings", 0)
        total_security_high = bandit_high + semgrep_high
        
        report = {
            "summary": {
                "timestamp": datetime.now().isoformat(),
                "total_time_seconds": total_time,
                "total_checks": total_checks,
                "successful_checks": successful_checks,
                "success_rate": (successful_checks / total_checks * 100) if total_checks > 0 else 0,
                "total_errors": total_errors,
                "total_warnings": total_warnings,
                "test_coverage_percent": coverage,
                "security_high_issues": total_security_high
            },
            "results": self.results,
            "quality_gates": {
                "coverage_threshold": 80,
                "coverage_met": coverage >= 80,
                "security_threshold": 0,
                "security_met": total_security_high == 0,
                "mypy_threshold": 0,
                "mypy_met": self.results.get("mypy", {}).get("error_count", 0) == 0
            }
        }
        
        # Save report
        report_file = self.logs_dir / "quality-report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        # Generate human-readable summary
        summary_file = self.logs_dir / "quality-summary.txt"
        with open(summary_file, "w") as f:
            f.write(f"Quality Check Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Total time: {total_time:.2f} seconds\n")
            f.write(f"Checks run: {total_checks}\n")
            f.write(f"Successful: {successful_checks}\n")
            f.write(f"Success rate: {report['summary']['success_rate']:.1f}%\n\n")
            f.write(f"Total errors: {total_errors}\n")
            f.write(f"Total warnings: {total_warnings}\n")
            f.write(f"Test coverage: {coverage:.1f}%\n")
            f.write(f"High security issues: {total_security_high}\n\n")
            f.write("Quality Gates:\n")
            f.write(f"  Coverage ≥80%: {'✓' if coverage >= 80 else '✗'}\n")
            f.write(f"  Security issues =0: {'✓' if total_security_high == 0 else '✗'}\n")
            f.write(f"  MyPy errors =0: {'✓' if self.results.get('mypy', {}).get('error_count', 0) == 0 else '✗'}\n")
        
        logger.info(f"Report generated: {report_file}")
        return str(report_file)
    
    def print_summary(self):
        """Print a summary to console."""
        print("\n" + "=" * 60)
        print("QUALITY CHECK SUMMARY")
        print("=" * 60)
        
        for tool, result in self.results.items():
            status = "✓" if result.get("success", False) else "✗"
            print(f"{tool.upper():<12} {status}")
            
            if tool == "mypy":
                errors = result.get("error_count", 0)
                warnings = result.get("warning_count", 0)
                print(f"  {'':<12} Errors: {errors}, Warnings: {warnings}")
            elif tool == "pytest":
                coverage = result.get("coverage_percent", 0)
                print(f"  {'':<12} Coverage: {coverage:.1f}%")
            elif tool in ["bandit", "semgrep"]:
                high = result.get("high_issues", result.get("high_findings", 0))
                print(f"  {'':<12} High issues: {high}")
        
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run quality checks for Fixer & Orchestrator v3.0")
    parser.add_argument("--config-dir", default=".buglab/configs", help="Configuration directory")
    parser.add_argument("--check", choices=["mypy", "ruff", "black", "bandit", "pytest", "semgrep", "all"], 
                       default="all", help="Specific check to run")
    parser.add_argument("--no-report", action="store_true", help="Skip report generation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    checker = QualityChecker(args.config_dir)
    
    if args.check == "all":
        checker.run_all_checks()
    else:
        check_func = getattr(checker, f"check_{args.check}")
        checker.results[args.check] = check_func()
    
    if not args.no_report:
        report_file = checker.generate_report()
        print(f"\nReport saved to: {report_file}")
    
    checker.print_summary()
    
    # Exit with error code if any checks failed
    failed_checks = sum(1 for r in checker.results.values() if not r.get("success", False))
    sys.exit(failed_checks)


if __name__ == "__main__":
    main()