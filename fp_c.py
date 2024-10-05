import ast
from typing import Any
from lxml import etree
import subprocess

from config import CPPCHECK_PATH, GCC_PATH, GDB_PATH
from fp_update_vars import update_vars


def formatvar(lang: str, types: list[str], value: Any) -> tuple[str, Any]:
    _type, *subtypes = types
    match _type:
        case "char" | "double" | "long" | "long long":
            return _type, value
        case "int":
            if lang in ["python"]:
                _type = "long long"
            return _type, value
        case "integer":
            return "long long", value
        case "float":
            if lang in ["python", "lua"]:
                _type = "double"
            return _type, value
        case "bool" | "boolean":
            return "int", int(value)
        case "NoneType" | "nil":
            return "void *", "NULL"

        case "char *" | "string" | "str":
            return "char *", '"' + value + '"'
        case "list" | "table":
            raise NotImplementedError("lists or tables!")
        case "dict":
            raise NotImplementedError("dictionaries!")
        case _:
            raise NotImplementedError("unknown type:", types, value)


def declare(vname: str, info: dict[str, Any]):
    _type, value = formatvar(info["lang"], info["type"], info["value"])
    return f"{_type} {vname} = {value};"


def gen_code(code: str, var_vals: dict[str, dict[str, Any]]) -> str:
    lines = ["#include <stdio.h>", "#include <string.h>", "int main(){"]
    for vname, info in var_vals.items():
        lines += [declare(vname, info)]
    assert not (r'\"' in code)
    lines += [code, "}"]
    outcode = "\n".join(lines)
    with open("tmpcode/tmp.c", "w", encoding="utf-8") as f:
        f.write(outcode)
    return outcode


def parsegdb(vtype: str, line: str) -> Any:

    def gcd_repeatstimes(line: str) -> str:
        if not line.endswith(" times>"):
            return line[1:-1]
        line = line.split(" times>")[:-1]
        data = line[0].rpartition('"')[0][1:]
        for part in line:
            L, _, R = part.rpartition("' <repeats ")
            L = part.split("'")[-2]
            count = int(R.split(" ")[0])
            if len(L) == 1: data += L * count
            elif len(L) == 4: data += chr(int(L[1:], 8)) * count
            else: raise NotImplementedError(part)
        return data

    match vtype:
        case "signed char":
            data = int(line.split(" ")[0])
        case "signed char *":
            if line[:2] == "0x": data = line.split(" ")[1][1:-1]
            else: data = gcd_repeatstimes(line)
        case "signed char **":
            line = line[1:-1]
            data = []
            for element in line.split(', '):
                if element[:2] == "0x":
                    data.append(element.split(" ")[1][1:-1])
                else:
                    raise NotImplementedError(
                        f"signed char ** contains too long string: {element}")
        case "float" | "double":
            data = float(line)
        case "signed long long" | "signed long" | "signed int":
            data = int(line)
        case "void *":
            if line == "(void *) 0x0": data = None
            else: raise NotImplementedError(vtype, line)
        case "signed int *" | "signed long *" | "signed long long *" | "double *" | "float *":
            data = ast.literal_eval("[" + line[1:-1] + "]")
        case _:
            raise NotImplementedError(vtype, line)
    return data


def findvars() -> dict[str, list[str]]:
    #find variables using cppcheck
    subprocess.run([CPPCHECK_PATH, "--dump", "--debug", "tmpcode/tmp.c"],
                   capture_output=True)
    tree = etree.parse('tmpcode/tmp.c.dump', parser=None)
    tokens = tree.getroot().find("dump").find("tokenlist")
    mainscope = [*tokens][-1].attrib["scope"]

    _vars = {}
    bracketing = -1
    for token in tokens:
        a: dict[str, str] = token.attrib
        vname = a["str"]
        if vname in "({": bracketing += 1
        elif vname in "})": bracketing -= 1

        if not (a["scope"] == mainscope and a.get("variable")): continue
        if (bracketing != 0) or _vars.get(vname): continue
        type_fields = [
            a.get("valueType-sign", ""), a["valueType-type"],
            int(a.get("valueType-pointer", "0")) * "*"
        ]
        type_fields = [f for f in type_fields if f]
        _vars[vname] = [" ".join(type_fields)]
    return _vars


def compile_eval(outcode: str, _vars: dict[str, dict[str, Any]]):
    #compile without debug flags
    result = subprocess.run(
        [GCC_PATH, "-g", "-O0", "tmpcode/tmp.c", "-o", "tmpcode/tmp.exe"],
        capture_output=True)
    stderr = result.stderr.decode(errors='ignore').replace("\r\n", "\n")
    print(stderr, end="")
    if result.returncode:
        raise SystemError(f"GCC return code {result.returncode}")

    #run compiled to extract stdout and stderr
    result = subprocess.run("tmpcode/tmp.exe", capture_output=True)
    stderr = result.stderr.decode(errors='ignore').replace("\r\n", "\n")
    print(stderr, end="")
    stdout = result.stdout.decode(errors='ignore').replace("\r\n", "\n")
    print(stdout, end="")

    #run again in gdb to evaluate variables
    commands = [f"b {outcode.count('\n') + 1}", "run"]
    commands += [f"p {vname}" for vname in _vars.keys()]
    _input = "\n".join(commands).encode("utf-8")
    result = subprocess.run([GDB_PATH, "tmpcode/tmp.exe"],
                            input=_input,
                            capture_output=True)
    stderr = result.stderr.decode(errors='ignore').replace("\r\n", "\n")
    if result.returncode:
        raise SystemError(f"GDB return code {result.returncode}")

    stdout = result.stdout.decode(errors='ignore')
    outputs = [l for l in stdout.split("\n") if l.startswith("(gdb) ")]
    var_vals = {}
    for line, (vname, vtype) in zip(outputs[2:], _vars.items()):
        line = line.partition(" = ")[2]
        data = parsegdb(vtype[0], line)
        var_vals[vname] = {"lang": "c", "type": vtype, "value": data}
    return var_vals


def full_eval(code: str, var_vals: dict[str, dict[str, Any]]):
    outcode = gen_code(code, var_vals)
    _vars = findvars()
    new_var_vals = compile_eval(outcode, _vars)
    update_vars(var_vals, new_var_vals)
    return var_vals
