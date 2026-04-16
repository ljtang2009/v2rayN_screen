import os

def load_env(env_path: str = None) -> dict:
    if env_path is None:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")
    return env_vars

def get_env_or_default(key: str, default: str = None) -> str:
    env_vars = load_env()
    return env_vars.get(key, default)

DB_PATH = get_env_or_default('DB_PATH', r"D:\APP\v2rayN-windows-64-SelfContained\guiConfigs\guiNDB.db")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SQL_FILE_PATH = os.path.join(SCRIPT_DIR, 'sql', 'query_top_performing_nodes.sql')
