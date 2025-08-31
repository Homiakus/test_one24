#!/usr/bin/env python3
"""
Technical Debt Analyzer for Fixer & Orchestrator v3.0
Analyzes code complexity, maintainability, and technical debt indicators.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.buglab/logs/tech_debt_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TechnicalDebtAnalyzer:
    """Analyzer for technical debt indicators."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.logs_dir = Path(".buglab/logs")
        self.results: Dict[str, Dict] = {}
        
        # Ensure logs directory exists
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_file_complexity(self, file_path: Path) -> Dict:
        """Analyze complexity of a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            total_lines = len(lines)
            code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
            comment_lines = len([l for l in lines if l.strip().startswith('#')])
            blank_lines = len([l for l in lines if not l.strip()])
            
            # Count functions and classes
            functions = content.count('def ')
            classes = content.count('class ')
            
            # Estimate cyclomatic complexity (simplified)
            complexity_indicators = [
                content.count('if '),
                content.count('elif '),
                content.count('for '),
                content.count('while '),
                content.count('except '),
                content.count('and '),
                content.count('or '),
                content.count('?')  # ternary operators
            ]
            estimated_complexity = sum(complexity_indicators) + 1
            
            return {
                "file": str(file_path),
                "total_lines": total_lines,
                "code_lines": code_lines,
                "comment_lines": comment_lines,
                "blank_lines": blank_lines,
                "functions": functions,
                "classes": classes,
                "estimated_complexity": estimated_complexity,
                "comment_ratio": comment_lines / total_lines if total_lines > 0 else 0,
                "blank_ratio": blank_lines / total_lines if total_lines > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return {
                "file": str(file_path),
                "error": str(e)
            }
    
    def analyze_project_structure(self) -> Dict:
        """Analyze overall project structure."""
        logger.info("Analyzing project structure...")
        
        python_files = list(self.project_root.rglob("*.py"))
        test_files = [f for f in python_files if "test" in f.name.lower()]
        source_files = [f for f in python_files if "test" not in f.name.lower()]
        
        # Analyze directories
        directories = {}
        for file_path in python_files:
            dir_name = file_path.parent.name
            if dir_name not in directories:
                directories[dir_name] = {"files": 0, "lines": 0}
            directories[dir_name]["files"] += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    directories[dir_name]["lines"] += len(f.readlines())
            except:
                pass
        
        return {
            "total_python_files": len(python_files),
            "source_files": len(source_files),
            "test_files": len(test_files),
            "test_ratio": len(test_files) / len(python_files) if python_files else 0,
            "directories": directories,
            "largest_directories": sorted(
                directories.items(), 
                key=lambda x: x[1]["files"], 
                reverse=True
            )[:5]
        }
    
    def analyze_code_quality_indicators(self) -> Dict:
        """Analyze code quality indicators."""
        logger.info("Analyzing code quality indicators...")
        
        python_files = list(self.project_root.rglob("*.py"))
        indicators = {
            "total_files": len(python_files),
            "files_with_todos": 0,
            "files_with_fixmes": 0,
            "files_with_hacks": 0,
            "files_with_xxx": 0,
            "long_functions": 0,
            "complex_functions": 0,
            "duplicate_code_suspicious": 0
        }
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for TODO comments
                if 'TODO' in content.upper():
                    indicators["files_with_todos"] += 1
                
                if 'FIXME' in content.upper():
                    indicators["files_with_fixmes"] += 1
                
                if 'HACK' in content.upper():
                    indicators["files_with_hacks"] += 1
                
                if 'XXX' in content.upper():
                    indicators["files_with_xxx"] += 1
                
                # Analyze functions
                lines = content.split('\n')
                in_function = False
                function_start = 0
                
                for i, line in enumerate(lines):
                    if line.strip().startswith('def '):
                        if in_function:
                            # Previous function analysis
                            function_length = i - function_start
                            if function_length > 50:
                                indicators["long_functions"] += 1
                        
                        in_function = True
                        function_start = i
                
                # Check for potential duplicate code patterns
                if content.count('def ') > 10:  # Many functions might indicate duplication
                    indicators["duplicate_code_suspicious"] += 1
                
            except Exception as e:
                logger.error(f"Error analyzing quality indicators in {file_path}: {e}")
        
        return indicators
    
    def analyze_dependencies(self) -> Dict:
        """Analyze project dependencies."""
        logger.info("Analyzing dependencies...")
        
        requirements_file = self.project_root / "requirements.txt"
        pyproject_file = self.project_root / "pyproject.toml"
        
        dependencies = {
            "requirements_txt": [],
            "pyproject_toml": [],
            "total_dependencies": 0,
            "development_dependencies": 0,
            "runtime_dependencies": 0
        }
        
        # Parse requirements.txt
        if requirements_file.exists():
            try:
                with open(requirements_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            dependencies["requirements_txt"].append(line)
                            dependencies["total_dependencies"] += 1
                            if any(dev_tool in line.lower() for dev_tool in ['test', 'pytest', 'mypy', 'black', 'flake8', 'lint']):
                                dependencies["development_dependencies"] += 1
                            else:
                                dependencies["runtime_dependencies"] += 1
            except Exception as e:
                logger.error(f"Error parsing requirements.txt: {e}")
        
        # Parse pyproject.toml (simplified)
        if pyproject_file.exists():
            try:
                with open(pyproject_file, 'r') as f:
                    content = f.read()
                    # Simple parsing for dependencies
                    if '[tool.poetry.dependencies]' in content or '[project.dependencies]' in content:
                        dependencies["pyproject_toml"] = ["Found dependencies section"]
            except Exception as e:
                logger.error(f"Error parsing pyproject.toml: {e}")
        
        return dependencies
    
    def analyze_test_coverage_gaps(self) -> Dict:
        """Analyze test coverage gaps."""
        logger.info("Analyzing test coverage gaps...")
        
        python_files = list(self.project_root.rglob("*.py"))
        test_files = [f for f in python_files if "test" in f.name.lower()]
        source_files = [f for f in python_files if "test" not in f.name.lower()]
        
        # Find source files without corresponding tests
        untested_files = []
        for source_file in source_files:
            # Skip __init__.py and other special files
            if source_file.name in ['__init__.py', 'setup.py', 'conftest.py']:
                continue
            
            # Look for corresponding test file
            test_file = source_file.parent / f"test_{source_file.name}"
            if not test_file.exists():
                # Check in tests directory
                test_file = self.project_root / "tests" / f"test_{source_file.name}"
                if not test_file.exists():
                    untested_files.append(str(source_file))
        
        return {
            "total_source_files": len(source_files),
            "total_test_files": len(test_files),
            "untested_files": untested_files,
            "untested_count": len(untested_files),
            "test_coverage_ratio": (len(source_files) - len(untested_files)) / len(source_files) if source_files else 0
        }
    
    def calculate_technical_debt_score(self) -> Dict:
        """Calculate overall technical debt score."""
        logger.info("Calculating technical debt score...")
        
        # Get all analysis results
        structure = self.results.get("structure", {})
        quality = self.results.get("quality", {})
        coverage = self.results.get("coverage", {})
        
        # Calculate debt factors
        debt_factors = {
            "complexity_debt": 0,
            "quality_debt": 0,
            "coverage_debt": 0,
            "maintainability_debt": 0
        }
        
        # Complexity debt (based on file sizes and complexity)
        total_files = structure.get("total_python_files", 0)
        if total_files > 100:
            debt_factors["complexity_debt"] += 20
        elif total_files > 50:
            debt_factors["complexity_debt"] += 10
        
        # Quality debt (based on TODO, FIXME, etc.)
        todos = quality.get("files_with_todos", 0)
        fixmes = quality.get("files_with_fixmes", 0)
        hacks = quality.get("files_with_hacks", 0)
        
        debt_factors["quality_debt"] += todos * 2
        debt_factors["quality_debt"] += fixmes * 3
        debt_factors["quality_debt"] += hacks * 5
        
        # Coverage debt
        coverage_ratio = coverage.get("test_coverage_ratio", 0)
        if coverage_ratio < 0.5:
            debt_factors["coverage_debt"] += 30
        elif coverage_ratio < 0.8:
            debt_factors["coverage_debt"] += 15
        
        # Maintainability debt
        long_functions = quality.get("long_functions", 0)
        debt_factors["maintainability_debt"] += long_functions * 2
        
        # Calculate total score (0-100, higher = more debt)
        total_debt = sum(debt_factors.values())
        total_debt = min(100, total_debt)  # Cap at 100
        
        # Categorize debt level
        if total_debt >= 80:
            debt_level = "Critical"
        elif total_debt >= 60:
            debt_level = "High"
        elif total_debt >= 40:
            debt_level = "Medium"
        elif total_debt >= 20:
            debt_level = "Low"
        else:
            debt_level = "Minimal"
        
        return {
            "total_debt_score": total_debt,
            "debt_level": debt_level,
            "debt_factors": debt_factors,
            "recommendations": self.generate_recommendations(debt_factors, structure, quality, coverage)
        }
    
    def generate_recommendations(self, debt_factors: Dict, structure: Dict, quality: Dict, coverage: Dict) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Complexity recommendations
        if debt_factors["complexity_debt"] > 10:
            recommendations.append("Consider breaking down large modules into smaller, focused components")
        
        # Quality recommendations
        if quality.get("files_with_todos", 0) > 5:
            recommendations.append("Address TODO comments - create tickets for technical debt items")
        
        if quality.get("files_with_fixmes", 0) > 0:
            recommendations.append("Fix FIXME comments - these indicate broken or incomplete code")
        
        if quality.get("files_with_hacks", 0) > 0:
            recommendations.append("Refactor HACK comments - these indicate temporary workarounds")
        
        # Coverage recommendations
        coverage_ratio = coverage.get("test_coverage_ratio", 0)
        if coverage_ratio < 0.8:
            recommendations.append(f"Increase test coverage from {coverage_ratio:.1%} to at least 80%")
        
        # Maintainability recommendations
        if quality.get("long_functions", 0) > 10:
            recommendations.append("Break down long functions into smaller, more focused functions")
        
        if not recommendations:
            recommendations.append("Code quality is good - maintain current standards")
        
        return recommendations
    
    def run_analysis(self) -> Dict:
        """Run complete technical debt analysis."""
        logger.info("Starting technical debt analysis...")
        
        self.results = {
            "structure": self.analyze_project_structure(),
            "quality": self.analyze_code_quality_indicators(),
            "dependencies": self.analyze_dependencies(),
            "coverage": self.analyze_test_coverage_gaps(),
            "debt_score": self.calculate_technical_debt_score()
        }
        
        return self.results
    
    def generate_report(self) -> str:
        """Generate technical debt report."""
        logger.info("Generating technical debt report...")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "project": str(self.project_root),
            "analysis": self.results
        }
        
        # Save JSON report
        report_file = self.logs_dir / "tech-debt-report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate human-readable summary
        summary_file = self.logs_dir / "tech-debt-summary.txt"
        with open(summary_file, 'w') as f:
            f.write(f"Technical Debt Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            # Structure summary
            structure = self.results.get("structure", {})
            f.write("PROJECT STRUCTURE:\n")
            f.write(f"  Total Python files: {structure.get('total_python_files', 0)}\n")
            f.write(f"  Source files: {structure.get('source_files', 0)}\n")
            f.write(f"  Test files: {structure.get('test_files', 0)}\n")
            f.write(f"  Test ratio: {structure.get('test_ratio', 0):.1%}\n\n")
            
            # Quality summary
            quality = self.results.get("quality", {})
            f.write("CODE QUALITY:\n")
            f.write(f"  Files with TODO: {quality.get('files_with_todos', 0)}\n")
            f.write(f"  Files with FIXME: {quality.get('files_with_fixmes', 0)}\n")
            f.write(f"  Files with HACK: {quality.get('files_with_hacks', 0)}\n")
            f.write(f"  Long functions: {quality.get('long_functions', 0)}\n\n")
            
            # Coverage summary
            coverage = self.results.get("coverage", {})
            f.write("TEST COVERAGE:\n")
            f.write(f"  Coverage ratio: {coverage.get('test_coverage_ratio', 0):.1%}\n")
            f.write(f"  Untested files: {coverage.get('untested_count', 0)}\n\n")
            
            # Debt score
            debt_score = self.results.get("debt_score", {})
            f.write("TECHNICAL DEBT SCORE:\n")
            f.write(f"  Total score: {debt_score.get('total_debt_score', 0)}/100\n")
            f.write(f"  Debt level: {debt_score.get('debt_level', 'Unknown')}\n\n")
            
            # Recommendations
            recommendations = debt_score.get("recommendations", [])
            f.write("RECOMMENDATIONS:\n")
            for i, rec in enumerate(recommendations, 1):
                f.write(f"  {i}. {rec}\n")
        
        logger.info(f"Report generated: {report_file}")
        return str(report_file)
    
    def print_summary(self):
        """Print analysis summary to console."""
        debt_score = self.results.get("debt_score", {})
        structure = self.results.get("structure", {})
        quality = self.results.get("quality", {})
        coverage = self.results.get("coverage", {})
        
        print("\n" + "=" * 60)
        print("TECHNICAL DEBT ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Project: {self.project_root}")
        print(f"Python files: {structure.get('total_python_files', 0)}")
        print(f"Test coverage: {coverage.get('test_coverage_ratio', 0):.1%}")
        print(f"TODO comments: {quality.get('files_with_todos', 0)}")
        print(f"FIXME comments: {quality.get('files_with_fixmes', 0)}")
        print(f"Technical debt score: {debt_score.get('total_debt_score', 0)}/100")
        print(f"Debt level: {debt_score.get('debt_level', 'Unknown')}")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze technical debt for Fixer & Orchestrator v3.0")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--no-report", action="store_true", help="Skip report generation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    analyzer = TechnicalDebtAnalyzer(args.project_root)
    analyzer.run_analysis()
    
    if not args.no_report:
        report_file = analyzer.generate_report()
        print(f"\nReport saved to: {report_file}")
    
    analyzer.print_summary()


if __name__ == "__main__":
    main()