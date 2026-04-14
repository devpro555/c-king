import yaml
import os

def load_settings(path=None):
    if path is None:
        # Try multiple possible locations
        possible_paths = [
            "config/settings.yaml",
            "../config/settings.yaml",
            os.path.join(os.path.dirname(__file__), "../config/settings.yaml")
        ]
        for p in possible_paths:
            if os.path.exists(p):
                path = p
                break
        if path is None:
            raise FileNotFoundError("Could not find settings.yaml in any expected location")
    
    with open(path, "r") as f:
        return yaml.safe_load(f)