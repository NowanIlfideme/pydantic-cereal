"""Utility functions."""

import inspect
import warnings
from typing import Any

from pydantic_cereal.errors import CerealRegistrationError


def import_object(dotted_path: str) -> Any:
    """Import the object from the string. Supports nested classes.

    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import fails.

    Stolen from Pydantic, who stole it approximately from django, and then improved.
    """
    from importlib import import_module
    from types import ModuleType

    parts = dotted_path.strip(" ").split(".")
    module: ModuleType = None  # type: ignore

    if len(parts) == 1:
        raise ImportError(f"{dotted_path!r} doesn't look like a module path")

    # Iterate through parts, which could be a module or a (possibly nested) class/object/whatever
    for rhs in range(1, len(parts)):
        class_parts = parts[-rhs:]
        module_path = ".".join(parts[:-rhs])
        try:
            module = import_module(module_path)
        except ImportError:
            # this is maybe not a module, but rather a package, e.g. namespace package
            continue

        try:
            obj: Any = module
            for clp in class_parts:
                obj = getattr(obj, clp)
        except AttributeError as e:
            raise ImportError(f"Could not import {dotted_path!r}, though module exists.") from e
        break
    else:
        raise ImportError(f"Could not import {dotted_path!r}, likely no such module exists.")
    return obj


def get_import_string(obj: Any) -> str:
    """Try to get an 'import string' for the given object."""
    module = inspect.getmodule(obj)
    if module is None:
        raise CerealRegistrationError(f"Couldn't infer module from object {obj!r}")

    # Try to get from qualified name?
    qn = getattr(obj, "__qualname__", None)
    if qn is not None:
        return f"{module.__name__}.{qn}"

    # Try to get from module members?
    module_members = {k: v for (k, v) in inspect.getmembers(module)}
    found_members = [k for k in module_members if module_members[k] is obj]
    if len(found_members) == 0:
        raise CerealRegistrationError(f"Object {obj!r} has no name, and not found in {module}.")
    elif len(found_members) > 1:
        warnings.warn(f"Found multiple name for the object, taking first: {found_members}")
    obj_name = found_members[0]
    return f"{module.__name__}.{obj_name}"
