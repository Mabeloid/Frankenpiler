import ast
import subprocess
from typing import Any

from config import PYTHON_PATH
from fp_update_vars import update_vars


def formatvar(types: list[str], value: Any) -> str:
    _type, *subtypes = types
    match _type:
        case "int" |  "signed int" | "integer" | "float" |  "double" | "signed char" |  \
            "bool" | "boolean" | "NoneType" | "nil":
            return str(value)
        case "signed char *" | "string" | "str":
            return f"'{value}'"
        case "table" | "list":
            pieces = [formatvar(subtypes, v) for v in value]
            return "[" + ", ".join(pieces) + "]"
        case "dict":
            pieces = [formatvar(subtypes[0:1], k) + ": " + formatvar(subtypes[1:2], v) for k,v in value.items()]
            return "{" + ", ".join(pieces) + "}"
        case _:
            raise NotImplementedError("unknown type:", types, _type)


def declare(vname: str, info: dict[str, Any]):
    return f"{vname} = {formatvar(info["type"], info["value"])}"


def gen_code(code: str, var_vals: dict[str, dict[str, Any]]) -> str:
    lines = []
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
    print(stderr, end="")

    stdout = result.stdout.decode(errors='ignore').replace("\r\n", "\n")
    stdout, _, _globals = stdout.partition(sep)
    _globals = _globals.split("\n")
    print(stdout, end="")

    var_vals = {}
    for line in _globals:
        if not line: continue
        vtype, vname, data = line.split(sep)
        if vname in {
                "__name__", "__doc__", "__package__", "__loader__", "__spec__",
                "__annotations__", "__builtins__", "__file__", "__cached__"
        }:
            continue

        vtype = vtype.split("|")
        if not all(
            t in ["int",
                  "str", "float", "bool", "NoneType", "list", "dict"]
            for t in vtype):
                raise NotImplementedError(vtype)
        if vtype != ["str"]: data = ast.literal_eval(data)
        var_vals[vname] = {"lang": "python", "type": vtype, "value": data}
    return var_vals


def full_eval(code: str, var_vals: dict[str, dict[str, Any]]):
    sep = gen_code(code, var_vals)
    new_var_vals = vars_eval(sep)
    update_vars(var_vals, new_var_vals)
    return var_vals
