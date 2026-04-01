import importlib
import importlib.util
import logging
import shutil
from pathlib import Path
import sys
from enum import IntEnum
from dataclasses import dataclass

from script_api import AbstractScript
from .language import get_language

SCRIPT_FOLDER = "scripts"


def _get_name(obj):
    """
    obj: package | AbstractScript
    """
    return obj.NAME_LOCALIZED.get(get_language(), obj.NAME)




class ScriptClassWrapper:
    def __init__(self, script_class):
        self.script_class = script_class

    def get_name(self) -> str:
        name_config = _get_name(self.script_class)
        if name_config:
            return name_config
        else:
            return type(self.script_class).__name__

    def __call__(self, **kwargs) -> AbstractScript | None:
        try:
            return self.script_class(**kwargs)
        except:
            return None


class PackageWrapper:
    def __init__(self, package_name: str, package):
        self.name = package_name
        self.package = package
        self.is_default = package_name == "default"
        self.scripts: list[ScriptClassWrapper] = []

        if not hasattr(package, "NAME") or not isinstance(package.NAME, str):
            return

        if not hasattr(package, "NAME_LOCALIZED") or not isinstance(package.NAME_LOCALIZED, dict):
            return
        for key, value in package.NAME_LOCALIZED.items():
            if not isinstance(key, str) or not isinstance(value, str):
                return

        if not hasattr(package, "SCRIPT_CLASSES") or not isinstance(package.SCRIPT_CLASSES, list):
            return

        for script_class in package.SCRIPT_CLASSES:
            if isinstance(script_class, type) and issubclass(script_class, AbstractScript):
                try:
                    script_wrapper = ScriptClassWrapper(script_class)
                except Exception as e:
                    self.log(e)
                else:
                    self.scripts.append(script_wrapper)

    def log(self, e):
        ...

    def get_name(self):
        return _get_name(self.package)


class LoadPackageCode(IntEnum):
    SUCCESS = 0
    PACKAGE_NAME_OCCUPIED = 1
    PACKAGE_NOT_FOUND = 2
    INIT_PY_NOT_FOUND = 3
    SPEC_CREATE_FAIL = 4
    PACKAGE_LOAD_FAIL = 5
    PACKAGE_NAMESPACE_INVALID = 6

    SRC_FOLDER_NOT_FOUND = 7
    PACKAGE_FOLDER_EXISTS = 8

@dataclass
class LoadPackageRetval:
    code: LoadPackageCode
    script_count: int = 0


class PackageScriptManager:
    def __init__(self, script_folder: str = SCRIPT_FOLDER):
        self.script_folder: Path = Path(script_folder)
        self.packages: dict[str, PackageWrapper] = {}

    def load_script(self, package_name: str) -> LoadPackageRetval:
        logging.info("load_script")
        if package_name in sys.modules:
            return LoadPackageRetval(LoadPackageCode.PACKAGE_NAME_OCCUPIED)

        package_dir = self.script_folder / package_name

        if not package_dir.is_dir():
            return LoadPackageRetval(LoadPackageCode.PACKAGE_NOT_FOUND)

        init_file = package_dir / "__init__.py"
        if not init_file.is_file():
            return LoadPackageRetval(LoadPackageCode.INIT_PY_NOT_FOUND)

        spec = importlib.util.spec_from_file_location(package_name,
                                                      str(init_file),
                                                      submodule_search_locations=[str(package_dir)])

        if spec is None:
            return LoadPackageRetval(LoadPackageCode.SPEC_CREATE_FAIL)

        package = importlib.util.module_from_spec(spec)
        sys.modules[package_name] = package

        try:
            spec.loader.exec_module(package)
        except:
            sys.modules.pop(package_name)
            return LoadPackageRetval(LoadPackageCode.PACKAGE_LOAD_FAIL)

        package_wrapper = PackageWrapper(package_name, package)
        if not package_wrapper.scripts:
            return LoadPackageRetval(LoadPackageCode.PACKAGE_NAMESPACE_INVALID)

        self.packages[package_name] = package_wrapper
        return LoadPackageRetval(LoadPackageCode.SUCCESS)



    def copy_folder_and_load(self, src_folder: str, overwrite: bool = False) -> tuple[LoadPackageRetval, PackageWrapper | None]:
        folder_path = Path(src_folder)
        if not folder_path.is_dir():
            return LoadPackageRetval(LoadPackageCode.SRC_FOLDER_NOT_FOUND), None
        init_file = folder_path / "__init__.py"
        if not init_file.is_file():
            return LoadPackageRetval(LoadPackageCode.INIT_PY_NOT_FOUND), None

        package_name = folder_path.name

        dst_path = self.script_folder / package_name
        if dst_path.exists():
            if overwrite:
                shutil.rmtree(dst_path)
            else:
                return LoadPackageRetval(LoadPackageCode.PACKAGE_FOLDER_EXISTS), None

        shutil.copytree(src_folder, dst_path)
        load_script_res = self.load_script(package_name)
        if load_script_res.code == LoadPackageCode.SUCCESS:
            return load_script_res, self.packages[package_name]
        else:
            shutil.rmtree(dst_path)
            return load_script_res, None

    def remove_script(self, package_name: str):
        if package_name not in self.packages:
            return

        self.packages.pop(package_name)

        dst_path = Path(self.script_folder) / package_name
        if dst_path.exists():
            shutil.rmtree(dst_path)

    def sync_scripts_folder(self):
        for package_name in self.packages:
            if package_name in sys.modules:
                sys.modules.pop(package_name)

        self.packages.clear()

        for subpath in self.script_folder.glob("*"):
            self.load_script(subpath.name)


