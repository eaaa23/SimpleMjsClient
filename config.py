import os
import json
from base64 import b64encode, b64decode
from dataclasses import dataclass, field, asdict
from json import JSONDecodeError
from typing import Any

from language import get_available_languages


CONFIG_PATH = "./config.json"


class SensitiveStr:
    def __init__(self):
        self._raw: str = ""
        self._encoded: str = ""

    def __getattr__(self, item):
        if item == "raw":
            return self._raw
        elif item == "encoded":
            return self._encoded
        raise AttributeError(f"{type(self).__name__} has no attribute {item}")

    def __setattr__(self, key, value):
        if key == "raw":
            object.__setattr__(self, "_raw", value)
            object.__setattr__(self, "_encoded", b64encode(bytes(value, encoding="utf-8")).decode(encoding="utf-8"))
        elif key == "encoded":
            object.__setattr__(self, "_encoded", value)
            object.__setattr__(self, "_raw", b64decode(value).decode(encoding="utf-8"))
        elif key in ("_raw", "_encoded"):
            object.__setattr__(self, key, value)
        else:
            raise AttributeError(f"Invalid attribute {key} for {type(self).__name__}")

    def to_dict(self):
        return {"encoded": self._encoded}


@dataclass
class Config:
    lang: str = field(default_factory=lambda: get_available_languages()[0])
    username: SensitiveStr = field(default_factory=SensitiveStr)
    password: SensitiveStr = field(default_factory=SensitiveStr)
    preserve_login: bool = False

    def save(self, config_path: str = CONFIG_PATH):
        with open(config_path, 'w') as fp:
            json.dump(asdict(self, dict_factory=lambda data: {key: value.to_dict() if hasattr(value, "to_dict") else value
                                                              for key, value in data}), fp)



def copy_json_to_dataclass(json_obj: dict[str, Any], dst):
    for key, value in json_obj.items():
        if isinstance(value, dict):
            copy_json_to_dataclass(value, getattr(dst, key))
        else:
            setattr(dst, key, value)


def get_config(config_path: str = CONFIG_PATH) -> Config:
    retval = Config()
    if os.path.isfile(config_path):
        with open(config_path) as fp:
            try:
                json_obj = json.load(fp)
            except (JSONDecodeError, UnicodeDecodeError):
                return retval
        copy_json_to_dataclass(json_obj, retval)

    return retval


# Global singleton
config = get_config()
