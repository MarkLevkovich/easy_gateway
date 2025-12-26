from pathlib import Path
from typing import Any, Dict

import yaml


def read_config(config_path: str) -> Dict[str, Any]:
    if Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            return data or {}
    else:
        print("Check config-file path!")
        return {}
