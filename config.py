from pathlib import Path
from typing import Any, Dict

import yaml


def load_config(config_path: str):
    pass


path = "config.yaml"
if Path(path).exists():
    load_config(path)
else:
    print("No file!")
