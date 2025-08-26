#!/usr/bin/env python3
"""Generate reference inventory from selected modules."""
import ast
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGET_DIRS = [ROOT / "core" / "communication", ROOT / "core" / "sequences"]

modules = []
classes = []
functions = []


def parse_file(path: pathlib.Path) -> None:
    module_name = ".".join(path.relative_to(ROOT).with_suffix("").parts)
    tree = ast.parse(path.read_text())
    module_doc = ast.get_docstring(tree) or ""
    modules.append(
        {"name": module_name, "path": str(path.relative_to(ROOT)), "doc": module_doc}
    )
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(
                {
                    "name": node.name,
                    "module": module_name,
                    "path": f"{path.relative_to(ROOT)}:{node.lineno}",
                    "doc": ast.get_docstring(node) or "",
                }
            )
        elif isinstance(node, ast.FunctionDef):
            functions.append(
                {
                    "name": node.name,
                    "module": module_name,
                    "path": f"{path.relative_to(ROOT)}:{node.lineno}",
                    "doc": ast.get_docstring(node) or "",
                }
            )


for directory in TARGET_DIRS:
    for file in directory.rglob("*.py"):
        parse_file(file)

inventory = {
    "reference_inventory": {
        "modules": modules,
        "classes": classes,
        "functions": functions,
        "endpoints": [],
        "events": [],
        "schemas": [
            {"name": "config", "path": "config.toml"},
            {"name": "serial_settings", "path": "serial_settings.json"},
            {"name": "update_settings", "path": "update_settings.json"},
        ],
    }
}

with open(ROOT / "reference_inventory.yaml", "w", encoding="utf-8") as fh:
    json.dump(inventory, fh, indent=2)
    fh.write("\n")
