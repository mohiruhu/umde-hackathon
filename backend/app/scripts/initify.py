from pathlib import Path

folders = [
    "backend/app",
    "backend/app/routes",
    "backend/app/rules",
    "backend/app/services",
    "backend/app/tests"
]

for folder in folders:
    path = Path(folder)
    path.mkdir(parents=True, exist_ok=True)
    init_file = path / "__init__.py"
    init_file.touch(exist_ok=True)
