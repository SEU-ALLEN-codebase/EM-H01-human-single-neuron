import yaml

def load_config():
    with open('src/config.yaml', 'r') as file:
        return yaml.safe_load(file)

CONFIG = load_config()

def get_config(key, default=None):
    keys = key.split('.')
    value = CONFIG
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            return default
    return value if value is not None else default
