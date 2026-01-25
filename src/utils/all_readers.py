import os
os.chdir(".")
print(f"📂 Execution path set to: {os.getcwd()}")
import sys
import yaml
from box import ConfigBox
from pathlib import Path

def read_yaml(path_to_yaml: str) -> ConfigBox:
    """
    Reads a YAML file and returns a ConfigBox.
    Args:
        path_to_yaml (str): Path like "config.yaml"
    Returns:
        ConfigBox: A dictionary-like object accessible via dot notation.
    """
    try:
        with open(path_to_yaml, 'r') as yaml_file:
            content = yaml.safe_load(yaml_file)
            print(f"yaml file: {path_to_yaml} loaded successfully")
            return ConfigBox(content)
    except Exception as e:
        print(f"Error reading yaml file: {e}")
        raise e


# --- USAGE ---
if __name__ == "__main__":
    # 1. Load the config
    config = read_yaml("configs/DB_configs.yaml")
    # 2. Access values using Dot Notation (The power of ConfigBox)
    print(f"App Name: {config}")       # instead of config['app_name']
    print(f"DB Port:  {config}")  # instead of config['database']['port']

