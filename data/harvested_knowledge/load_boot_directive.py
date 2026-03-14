import os
import sys
from dotenv import load_dotenv
import importlib.util

# Setup the base path and environment (run only once during import)
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE not in sys.path:
    sys.path.insert(0, BASE)
load_dotenv(os.path.join(BASE, ".env"))

def load_boot_directive(name="default", path=None):
    """
    Dynamically loads and returns a boot directive by its name and (optionally) from an external path.

    :param name: Name of the directive to load (default is "default").
    :type name: str
    :param path: External directory to load directive from (default None: package's own boot_directives).
    :type path: str or Path or None
    :return: The `matrix_directive` dictionary from the requested module.
    """
    try:
        # If an external path is given, load the .py file from there
        if path:
            directive_path = os.path.join(path, f"{name}.py")
            if not os.path.isfile(directive_path):
                raise ModuleNotFoundError(f"Directive file '{directive_path}' does not exist.")

            spec = importlib.util.spec_from_file_location(f"custom_directive_{name}", directive_path)
            if not spec:
                raise ImportError(f"Failed to load spec for '{directive_path}'")
            directive_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(directive_mod)
        else:
            # Built-in/package fallback
            module_path = os.path.join(BASE, "boot_directives", f"{name}.py")
            if not os.path.isfile(module_path):
                raise ModuleNotFoundError(f"Directive file '{module_path}' does not exist.")
            mod_path = f"boot_directives.{name}"
            directive_mod = __import__(mod_path, fromlist=["matrix_directive"])

        if not hasattr(directive_mod, "matrix_directive"):
            raise AttributeError(f"Directive module '{name}' does not contain 'matrix_directive'.")

        return directive_mod.matrix_directive

    except ModuleNotFoundError as e:
        print(f"[BOOTLOADER][ERROR] Could not find directive '{name}': {e}")
        sys.exit(1)
    except AttributeError as e:
        print(f"[BOOTLOADER][ERROR] Invalid directive '{name}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[BOOTLOADER][ERROR] Unexpected error while loading directive '{name}': {e}")
        sys.exit(1)