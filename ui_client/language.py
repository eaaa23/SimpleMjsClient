import os
import json
from json import JSONDecodeError

TEXT_FOLDER = "text"

_languages: dict[str, dict] = {}
_current_lang = ""
_name_to_lang: dict[str, str] = {}


def load_languages():
    global _languages, _name_to_lang
    for filename in os.listdir(TEXT_FOLDER):
        file_loc = os.path.join(TEXT_FOLDER, filename)
        if filename.endswith('.json') and os.path.isfile(os.path.join(TEXT_FOLDER, filename)):
            try:
                with open(file_loc, encoding="utf-8") as fp:
                    data = json.load(fp)
                    lang = filename.strip('.json')
                    _languages[lang] = data
                    _name_to_lang[data["name"]] = lang
            except (JSONDecodeError, UnicodeDecodeError, AttributeError):
                pass

load_languages()
if not _languages:
    raise FileNotFoundError("No valid language file found!")

def get_available_languages() -> list[str]:
    return list(_languages.keys())

def get_language_from_name(name: str) -> str:
    return _name_to_lang[name]

def get_language() -> str:
    return _current_lang

def set_language(lang: str):
    global _current_lang
    _current_lang = lang


def tr(key: str, lang=None) -> str:
    if lang is None:
        lang = _current_lang
    text_data = _languages[lang]
    for key_segment in key.split('.'):
        if key_segment in text_data:
            text_data = text_data[key_segment]
        else:
            return key
    if isinstance(text_data, str):
        return text_data
    return key

