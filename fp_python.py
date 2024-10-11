import ast
import subprocess
from typing import Any

from config import PYTHON_PATH
from fp_update_vars import update_vars


def formatvar(lang, types: list[str], value: Any) -> str:
    _type, *subtypes = types
    match _type:
        case "signed int" | "signed long" | "signed long long" | "int" | "integer" | \
            "Number" | "BigInt" | "float" |  "double" | "signed char" | \
            "bool" | "boolean" | "Boolean" | "NoneType" | "nil" | "Null":
            return str(value)
        case "signed char *" | "string" | "String" | "str":
            return f"'{value}'"
        case "Date":
            return f"datetime.fromtimestamp({value})"
        case "table":
            _type = ["list", "dict"][isinstance(value, dict)]
            return formatvar(lang, [_type, *subtypes], value)
        case "list" | "Array":
            pieces = [formatvar(lang, subtypes, v) for v in value]
            return "[" + ", ".join(pieces) + "]"
        case "set" | "Set":
            pieces = [formatvar(lang, subtypes, v) for v in value]
            return "{" + ", ".join(pieces) + "}"
        case "dict" | "Map":
            pieces = [
                formatvar(lang, subtypes[0:1], k) + ": " +
                formatvar(lang, subtypes[1:2], v) for k, v in value.items()
            ]
            return "{" + ", ".join(pieces) + "}"
        case _:
            if _type.endswith("*"):
                _type = _type[:-1].rstrip(" ")
                pieces = [formatvar(lang, [_type], v) for v in value]
                return "[" + ", ".join(pieces) + "]"

            raise NotImplementedError("unknown type:", types, _type)


def declare(vname: str, info: dict[str, Any]):
    return f"{vname} = {formatvar(info['lang'], info['type'], info['value'])}"


def gen_code(code: str, var_vals: dict[str, dict[str, Any]]) -> str:
    lines = ["from datetime import datetime"]
    for vname, info in var_vals.items():
        lines += [declare(vname, info)]
    assert not (r'\"' in code)
    with open("code_inserts/fp_insert.py", "r") as f:
        print_globals = f.read()
    sep = hex(hash(code))
    print_globals = print_globals.replace("%s", sep)
    lines += [code, print_globals]
    outcode = "\n".join(lines)
    with open("tmpcode/tmp.py", "w", encoding="utf-8") as f:
        f.write(outcode)
    return sep


def vars_eval(sep: str):
    result = subprocess.run([PYTHON_PATH, "tmpcode/tmp.py"],
                            capture_output=True)
    stderr = result.stderr.decode(errors='ignore').replace("\r\n", "\n")
    if result.returncode:
        print(stderr)
        print(f"Python return code {result.returncode}")
        exit()

    stdout = result.stdout.decode(errors='ignore').replace("\r\n", "\n")
    stdout, _, _globals = stdout.partition(sep)
    print(stdout, end="")

    var_vals = {}
    for line in _globals.split("\n"):
        if not line: continue
        vtype, vname, data = line.split(sep)
        if vname in [
                "__name__", "__doc__", "__package__", "__loader__", "__spec__",
                "__annotations__", "__builtins__", "__file__", "__cached__"
        ]:
            continue

        vtype = vtype.split("|")
        if not all(t in
                   ["int", "str", "float", "bool", "NoneType",  "datetime", "list", "dict", "set"]
                   for t in vtype):
            raise NotImplementedError(f"unknown type: {vtype}")
        if vtype != ["str"]: data = ast.literal_eval(data)
        var_vals[vname] = {"lang": "python", "type": vtype, "value": data}
    return var_vals


def full_eval(code: str, var_vals: dict[str, dict[str, Any]]):
    sep = gen_code(code, var_vals)
    new_var_vals = vars_eval(sep)
    update_vars("python", var_vals, new_var_vals)
    return var_vals
