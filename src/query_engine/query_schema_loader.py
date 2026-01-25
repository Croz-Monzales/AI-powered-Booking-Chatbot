import os
import sys

# 1. Get the absolute path of the directory containing THIS script
# Let's assume this script is in src/query_engine/
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Find the project root (going up levels as needed)
# If script is in Langgraph_project/src/query_engine/test.py, go up twice:
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))

# 3. Add project root to sys.path so 'from src...' always works
if project_root not in sys.path:
    sys.path.append(project_root)

# 4. Change directory to root so relative paths for files work
os.chdir(project_root)
print(f"📂 Execution path anchored to: {os.getcwd()}")

from src.utils.all_readers import read_yaml

# Now this path is relative to the PROJECT ROOT, not the script location
db_schemas = read_yaml('configs/DB_configs.yaml')
print(db_schemas)