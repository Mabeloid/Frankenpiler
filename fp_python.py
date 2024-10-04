import ast
import subprocess
from typing import Any

from config import PYTHON_PATH
from fp_update_vars import update_vars


def declare(vname: str, info: dict[str, Any]):
    dtype = " ".join(f for f in info["type"] if f)
    matchtype = " ".join(f for f in info["type"][1:] if f)
    match matchtype:
        case "int" | "integer" | "float" |  "double" | "char" |  \
            "bool" |"boolean" | "NoneType" | "nil" | "table[number]" | \
            "table[string]" | "list[str]" | "list[int]" | "list[float]":
            return f"{vname} = {info['value']}"
        case "char *" | "string" | "str":
            return f"{vname} = '{info['value']}'"
        case _:
            raise NotImplementedError(matchtype, dtype, vname, info)
    return line


def gen_code(code: str, var_vals: dict[str, dict[str, Any]]) -> str:
    lines = []
    for vname, info in var_vals.items():
        lines += [declare(vname, info)]
    assert not (r'\"' in code)
    print_globals = """
print("%s")
for __, ___ in globals().copy().items():
    if isinstance(___, list): _ = f"list[{type(___[1]).__name__}]"
    else: _ = type(___).__name__
    _ += "%s" + __ + "%s" + str(___)
    print(_)
"""
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
        match vtype:
            case "int":
                data = int(data)
            case "str":
                data = data
            case "bool":
                data = data == "True"
            case "NoneType":
                data = None
            case "list[int]" | "list[str]" | "list[float]":
                data = ast.literal_eval(data)
            case _:
                raise NotImplementedError(line.split(sep))
        vtype = ["", vtype, ""]
        var_vals[vname] = {"lang": "python", "type": vtype, "value": data}
    return var_vals


def full_eval(code: str, var_vals: dict[str, dict[str, Any]]):
    sep = gen_code(code, var_vals)
    new_var_vals = vars_eval(sep)
    update_vars(var_vals, new_var_vals)
    return var_vals
