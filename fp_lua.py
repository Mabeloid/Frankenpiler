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


def gen_code(code: str, var_vals: dict[str, dict[str, Any]]) -> str:
    lines = []
    for vname, info in var_vals.items():
        lines += [declare(vname, info)]
    assert not (r'\"' in code)
    print_G = """
print("%s")
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
        _ = _:sub(1, -2) .. "]"
    elseif type(value) == "number" then
        _ = math.type(value) .. "%s" .. name .. "%s" .. tostring(value)
    else
        _ = type(value) .. "%s" .. name .. "%s" .. tostring(value)
    end
    if name ~= "_" then print(_) end
end
"""
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
    print(stderr, end="")
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

        match vtype:
            case "integer":
                data = int(data)
            case "float":
                data = float(data)
            case "string":
                data = data
            case "nil":
                data = None
            case "boolean":
                data = data == "true"
            case "table[number]" | "table[string]":
                data = ast.literal_eval(data)
            case _:
                raise NotImplementedError(line.split(sep))
        vtype = ["", vtype, ""]
        var_vals[vname] = {"lang": "lua", "type": vtype, "value": data}
    return var_vals


def full_eval(code: str, var_vals: dict[str, dict[str, Any]]):
    sep = gen_code(code, var_vals)
    new_var_vals = vars_eval(sep)
    update_vars(var_vals, new_var_vals)
    return var_vals
