import ast
import subprocess
from typing import Any

from config import LUA_PATH
from fp_update_vars import update_vars


def formatvar(lang:str, types: list[str], value: Any) -> str:
    _type, *subtypes = types
    match _type:
        case "signed int" | "signed long" | "signed long long" | \
            "signed char" | "int" | "integer" | "float" | "double" :
            return str(value)
        case "bool" | "boolean":
            return str(value).lower()
        case "NoneType" | "nil":
            return "nil"
        case "signed char *" | "string" | "str":
            return f"'{value}'"
        case "table":
            _type = ["list", "dict"][isinstance(value, dict)]
            return formatvar(lang, [_type, *subtypes], value)
        case "list":
            pieces = [formatvar(lang, subtypes, v) for v in value]
            return "{" + ", ".join(pieces) + "}"
        case "dict":
            pieces = [
                f"[{formatvar(lang, subtypes[0:1], k)}]=" +
                formatvar(lang, subtypes[1:2], v) for k, v in value.items()
            ]
            return "{" + ", ".join(pieces) + "}"
        case _:
            if _type[-1] == "*":
                _type = _type[:-1].rstrip(" ")
                pieces = [formatvar(lang, [_type], v) for v in value]
                return "{" + ", ".join(pieces) + "}"
            raise NotImplementedError("unknown type:", types)


def declare(vname: str, info: dict[str, Any]):
    return f"{vname} = {formatvar(info["lang"], info['type'], info['value'])}"


def gen_code(code: str, var_vals: dict[str, dict[str, Any]]) -> str:
    lines = []
    for vname, info in var_vals.items():
        lines += [declare(vname, info)]
    assert not (r'\"' in code)
    with open("code_inserts/fp_insert.lua", "r") as f:
        print_G = f.read()
    sep = hex(hash(code))
    print_G = print_G.replace("%s", sep)
    lines += [code, print_G]
    outcode = "\n".join(lines)
    with open("tmpcode/tmp.lua", "w", encoding="utf-8") as f:
        f.write(outcode)
    return sep


def vars_eval(sep: str):
    #run lua code, print stdout and stderr
    result = subprocess.run([LUA_PATH, "tmpcode/tmp.lua"], capture_output=True)
    stderr = result.stderr.decode(errors='ignore').replace("\r\n", "\n")
    if result.returncode:
        print(stderr)
        print(f"Lua return code {result.returncode}")
        exit()
    stdout = result.stdout.decode(errors='ignore').replace("\r\n", "\n")
    stdout, _, _G = stdout.partition(sep)
    _G = _G.split("\n")
    print(stdout, end="")

    #extract global variables
    var_vals = {}
    for line in _G:
        if not line: continue
        if len(line.split(sep)) != 3:
            raise NotImplementedError(line.split(sep))
        vtype, vname, data = line.split(sep)
        if vname in [
                "debug", "io", "xpcall", "string", "load", "os", "ipairs",
                "rawlen", "warn", "error", "math", "package", "getmetatable",
                "assert", "rawset", "dofile", "type", "arg", "next",
                "coroutine", "require", "select", "rawget", "table", "pairs",
                "loadfile", "utf8", "setmetatable", "tostring", "_G", "pcall",
                "tonumber", "_VERSION", "rawequal", "collectgarbage", "print"
        ]:
            continue

        vtype = vtype.split("|")
        data = ast.literal_eval(data)
        if (vtype[0:2] == ["table","integer"]) and all(k==i for k,i in zip(data.keys(), range(1, len(data.keys())))):
                del vtype[1]
                data = [*data.values()]
        var_vals[vname] = {"lang": "lua", "type": vtype, "value": data}
    return var_vals


def full_eval(code: str, var_vals: dict[str, dict[str, Any]]):
    sep = gen_code(code, var_vals)
    new_var_vals = vars_eval(sep)
    update_vars("lua", var_vals, new_var_vals)
    return var_vals
