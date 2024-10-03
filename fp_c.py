import ast
from typing import Any
from lxml import etree
import subprocess

from config import CPPCHECK_PATH, GCC_PATH, GDB_PATH
from fp_update_vars import update_vars


def findvars(outcode: str) -> dict[str, list[str]]:
    with open("tmpcode/tmp.c", "w", encoding="utf-8") as f:
        f.write(outcode)
    #find variables using cppcheck
    subprocess.run([CPPCHECK_PATH, "--dump", "--debug", "tmpcode/tmp.c"],
                   capture_output=True)
    tree = etree.parse('tmpcode/tmp.c.dump')
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
        vtype = [
            a.get("valueType-sign"), a["valueType-type"],
            int(a.get("valueType-pointer", "0")) * "*"
        ]
        _vars[vname] = vtype
    return _vars


def declare(vname: str, info: dict[str, Any]):
    dtype = " ".join(f for f in info["type"] if f)
    matchtype = " ".join(f for f in info["type"][1:] if f)
    lang = info["lang"]
    match matchtype:

        case "char" | "double" | "long" | "long long":
            line = f"{dtype} {vname} = {info['value']};"
        case "int":
            if lang in ["python", "lua"]:
                dtype = "long long"
            line = f"{dtype} {vname} = {info['value']};"

        case "float":
            if lang in ["python"]:
                dtype = "double"
            line = f"{dtype} {vname} = {info['value']};"

        case "bool" | "boolean":
            line = f"int {vname} = {int(info['value'])};"
        case "NoneType" | "nil":
            line = f"void * {vname} = NULL;"

        case "char *" | "string" | "str":
            size = len(info['value'].encode('utf-8')) + 1
            line = f"char {vname}[{size}] = \"{info['value']}\";"

        case "float *" | "int *":
            arrstr = "{" + str(info['value'])[1:-1] + "}"
            line = f"{dtype} {vname}[{len(info['value'])}] = {arrstr};"

        case "list[float]":
            arrstr = "{" + str(info['value'])[1:-1] + "}"
            line = f"double {vname}[{len(info['value'])}] = {arrstr};"

        case "list[int]":
            arrstr = "{" + str(info['value'])[1:-1] + "}"
            line = f"long long {vname}[{len(info['value'])}] = {arrstr};"

        case "table[number]":
            is_ints = all(x == round(x) for x in info['value'])
            dtype = ["double", "long long"][is_ints]
            arrstr = "{" + str(info['value'])[1:-1] + "}"
            line = f"{dtype} {vname}[{len(info['value'])}] = {arrstr};"

        case "char **" | "table[string]" | "list[str]":
            raise TypeError("arrays of strings do not " +
                            "show up in gdb due to having " +
                            "double pointers so their value " +
                            "can't be read by the program")
            arrstr = "{" + str(info['value'])[1:-1] + "}"
            line = f"char * {vname}[] = {arrstr};"

        case _:
            raise NotImplementedError(dtype, vname, info)
    return line


def formatcode(code: str, var_vals: dict[str, dict[str, Any]]) -> str:
    lines = ["#include <stdio.h>", "#include <string.h>", "int main(){"]
    for vname, info in var_vals.items():
        lines += [declare(vname, info)]
    assert not (r'\"' in code)
    lines += [code, "}"]
    return "\n".join(lines)


def parsegdb(vtype: list[str], line: str) -> Any:

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

    #dtype = " ".join(f for f in vtype if f)
    matchtype = " ".join(f for f in vtype[1:] if f)
    match matchtype:
        case "char":
            data = int(line.split(" ")[0])
        case "char *":
            if line[:2] == "0x": data = line.split(" ")[1][1:-1]
            else: data = gcd_repeatstimes(line)
        case "float" | "double":
            data = float(line)
        case "long long" | "long" | "int":
            data = int(line)
        case "void *":
            if line == "(void *) 0x0": data = None
            else: raise NotImplementedError(matchtype, line)
        case "int *":
            data = ast.literal_eval("[" + line[1:-1] + "]")
        case "long long *":
            data = ast.literal_eval("[" + line[1:-1] + "]")
        case "float *" | "double *":
            data = [float(v) for v in ast.literal_eval("[" + line[1:-1] + "]")]
        case _:
            raise NotImplementedError(vtype, line)
    return data


def compile_eval(outcode: str, _vars: dict[str, dict[str, Any]]):
    #compile without debug flags
    subprocess.run(
        [GCC_PATH, "-g", "-O0", "tmpcode/tmp.c", "-o", "tmpcode/tmp.exe"],
        capture_output=True)
    commands = [f"b {outcode.count('\n')+1}", "run"]
    commands += [f"p {vname}" for vname in _vars.keys()]
    _input = "\n".join(commands).encode("utf-8")

    #run compiled to extract stdout and stderr
    result = subprocess.run("tmpcode/tmp.exe", capture_output=True)
    stderr = result.stderr.decode(errors='ignore').replace("\r\n", "\n")
    print(stderr, end="")
    stdout = result.stdout.decode(errors='ignore').replace("\r\n", "\n")
    print(stdout, end="")

    #run again in gdb to evaluate variables
    result = subprocess.run([GDB_PATH, "tmpcode/tmp.exe"],
                            input=_input,
                            capture_output=True)
    stderr = result.stderr.decode(errors='ignore').replace("\r\n", "\n")
    if False: print(stderr, end="")

    stdout = result.stdout.decode(errors='ignore')
    outputs = [l for l in stdout.split("\n") if l.startswith("(gdb) ")]
    var_vals = {}
    for line, (vname, vtype) in zip(outputs[2:], _vars.items()):
        line = line.partition(" = ")[2]
        data = parsegdb(vtype, line)
        var_vals[vname] = {"lang": "c", "type": vtype, "value": data}
    return var_vals


def full_eval(code: str, var_vals: dict[str, dict[str, Any]]):
    outcode = formatcode(code, var_vals)
    _vars = findvars(outcode)
    new_var_vals = compile_eval(outcode, _vars)
    update_vars(var_vals, new_var_vals)
    return var_vals
