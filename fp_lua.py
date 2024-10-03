
import ast
import subprocess
from typing import Any

from config import LUA_PATH
from fp_update_vars import update_vars


def declare(vname: str, info: dict[str, Any]):
    dtype = " ".join(f for f in info["type"] if f)
    matchtype = " ".join(f for f in info["type"][1:] if f)
    match matchtype:
        case "char" | "int" | "float" | "number":
            line = f"{vname} = {info['value']}"
        case "NoneType" | "nil":
            line = f"{vname} = nil"
        case "bool":
            b = ["false", "true"][info["value"]]
            line = f"{vname} = {b}"
        case "char *" | "string" | "str":
            line = f"{vname} = '{info['value']}'"
        case "table[string]" | "table[number]" | "list[str]" | "list[float]" | "list[int]":
            tablestr = "{" + str(info['value'])[1:-1] + "}"
            line = f"{vname} = {tablestr}"
        case _:
            raise NotImplementedError(matchtype, dtype, vname, info)
    return line


def formatcode(code: str, var_vals: dict[str, dict[str, Any]],
               sep: str) -> str:
    lines = []
    for vname, info in var_vals.items():
        lines += [declare(vname, info)]
    assert not (r'\"' in code)
    print_G = """
print("%s")
print(_VERSION)
for name, value in pairs(_G) do
    if type(value) == "table" then
        _ = "table[" .. type(value[1]) .. "]" .. "%s" .. name .. "%s"
        _ = _ .. "["
        for __, t_value in ipairs(value) do
            if type(t_value) == "string" then
                _ = _ .. '"' .. tostring(t_value) .. '"' .. ","
            else
                _ = _ .. tostring(t_value) .. ","
            end
        end
        _ = _:sub(1,-2) .. "]"
    else
        _ = type(value) .. "%s" .. name .. "%s" .. tostring(value)
    end
    if name ~= "_" then print(_) end
end
"""
    print_G = print_G.replace("%s", sep)
    lines += [code, print_G]
    return "\n".join(lines)


def vars_eval(outcode: str, sep: str):
    with open("tmpcode/tmp.lua", "w", encoding="utf-8") as f:
        f.write(outcode)
    result = subprocess.run([LUA_PATH, "tmpcode/tmp.lua"], capture_output=True)
    stderr = result.stderr.decode(errors='ignore').replace("\r\n", "\n")
    print(stderr, end="")

    stdout = result.stdout.decode(errors='ignore').replace("\r\n", "\n")
    stdout, _, _G = stdout.partition(sep)
    _G = _G.split("\n")
    print(stdout, end="")

    _VERSION = _G.pop(1)
    var_vals = {}
    for line in _G:
        if not line: continue
        if len(line.split(sep)) != 3:
            raise NotImplementedError(line.split(sep))
        vtype, vname, data = line.split(sep)
        if vname in {
                "string", "xpcall", "package", "tostring", "print", "os",
                "unpack", "require", "getfenv", "setmetatable", "next",
                "assert", "tonumber", "io", "rawequal", "collectgarbage",
                "arg", "getmetatable", "module", "rawset", "load", "math",
                "debug", "pcall", "table", "newproxy", "type", "coroutine",
                "_G", "select", "gcinfo", "pairs", "rawget", "loadstring",
                "ipairs", "_VERSION", "dofile", "setfenv", "error", "loadfile"
        } | {"_"}:
            continue
        match vtype:
            case "number":
                if "." in data: data = float(data)
                else: data = int(data)
            case "string":
                data = data
            case "nil" :
                data = None
            case "boolean" :
                data = data == "true"
            case "table[number]" | "table[string]":
                data = ast.literal_eval(data)
            case _:
                if _VERSION >= "Lua 5.3":
                    raise NotImplementedError(
                        "new lua has actual integers and floats")
                raise NotImplementedError(line.split(sep))
        vtype = ["", vtype, ""]
        var_vals[vname] = {"lang": "lua", "type": vtype, "value": data}
    return var_vals


def full_eval(code: str, var_vals: dict[str, dict[str, Any]]):
    sep = hex(hash(code))
    outcode = formatcode(code, var_vals, sep)
    new_var_vals = vars_eval(outcode, sep)
    update_vars(var_vals, new_var_vals)
    return var_vals
