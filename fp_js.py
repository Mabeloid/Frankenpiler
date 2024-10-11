import ast
import subprocess
from typing import Any
from datetime import datetime

from config import JS_PATH
from fp_update_vars import update_vars


def formatvar(lang, types: list[str], value: Any) -> str:
    _type, *subtypes = types

    match _type:
        case "signed int" | "signed long" | "signed long long" | "int" | "integer" | \
            "Number" | "float" |  "double" | "signed char":
            return str(value)
        case "BigInt":
            return f"{value}n"
        case "bool" | "boolean" | "Boolean":
            return str(value).lower()
        case "NoneType" | "nil" | "Null":
            return "null"
        case "signed char *" | "string" | "String" | "str":
            return f"'{value}'"
        case "Date":
            return f"new Date({value * 1000})"
        case "table":
            _type = ["list", "dict"][isinstance(value, dict)]
            return formatvar(lang, [_type, *subtypes], value)
        case "list" | "Array":
            pieces = [formatvar(lang, subtypes, v) for v in value]
            return "[" + ", ".join(pieces) + "]"
        case "set" | "Set":
            pieces = [formatvar(lang, subtypes, v) for v in value]
            return "new Set([" + ", ".join(pieces) + "])"
        case "Map" | "dict":
            pieces = [
                f"[{formatvar(lang, subtypes[0:1], k)}, {formatvar(lang, subtypes[1:2], v)}]"
                for k, v in value.items()
            ]
            return "new Map([ " + ", ".join(pieces) + "])"
        case _:
            if _type.endswith("*"):
                _type = _type[:-1].rstrip(" ")
                pieces = [formatvar(lang, [_type], v) for v in value]
                return "[" + ", ".join(pieces) + "]"

            raise NotImplementedError("unknown type:", types, _type)


def declare(vname: str, info: dict[str, Any]):
    return f"{vname} = {formatvar(info['lang'], info['type'], info['value'])}"


def gen_code(code: str, var_vals: dict[str, dict[str, Any]]) -> str:
    lines = []
    for vname, info in var_vals.items():
        lines += [declare(vname, info)]
    assert not (r'\"' in code)
    with open("code_inserts/fp_insert.js", "r") as f:
        print_globals = f.read()
    sep = hex(hash(code))
    print_globals = print_globals.replace("%s", sep)
    lines += [code, print_globals]
    outcode = "\n".join(lines)
    with open("tmpcode/tmp.js", "w", encoding="utf-8") as f:
        f.write(outcode)
    return sep


def vars_eval(sep: str):
    result = subprocess.run([JS_PATH, "tmpcode/tmp.js"], capture_output=True)
    stderr = result.stderr.decode(errors='ignore').replace("\r\n", "\n")
    if result.returncode:
        print(stderr)
        print(f"JavaScript return code {result.returncode}")
        exit()

    stdout = result.stdout.decode(errors='ignore').replace("\r\n", "\n")
    stdout, _, _globals = stdout.partition(sep)
    print(stdout, end="")
    var_vals = {}
    for line in _globals.split("\n"):
        if not line: continue
        vtype, vname, data = line.split(sep)
        if vname in [
                "global", "clearImmediate", "setImmediate", "clearInterval",
                "clearTimeout", "setInterval", "setTimeout", "queueMicrotask",
                "structuredClone", "atob", "btoa", "performance", "fetch",
                "crypto"
        ]:
            continue
        vtype = vtype.split("|")
        if not all(t in [
                "Number", "BigInt", "String", "Null", "Boolean", "Array",
                "Set", "Map", "Date"
        ] for t in vtype):
            raise NotImplementedError(
                f"var '{vname}' has unknown type: {vtype}\nlooks like this: {data}"
            )
        data = ast.literal_eval(data)
        var_vals[vname] = {"lang": "js", "type": vtype, "value": data}
    return var_vals


def full_eval(code: str, var_vals: dict[str, dict[str, Any]]):
    sep = gen_code(code, var_vals)
    new_var_vals = vars_eval(sep)
    update_vars("python", var_vals, new_var_vals)
    return var_vals
