from datetime import datetime
from typing import Any

from config import LONG_IS_64BIT


def cast_c(_type: str, val: Any) -> Any:
    match _type:
        case "unsigned char":
            return int(val) % 256
        case "signed char":
            if isinstance(val, str):
                assert len(val) == 1
                val = ord(val)
            val = int(val) % 256
            return val - 256 * (val > 127)
        case "unsigned int":
            return int(val) % 2**32
        case "signed int":
            val = int(val) % 2**32
            return val - 2**32 * (val > (2**31 - 1))
        case "signed long":
            _type = ["signed int", "signed long long"][LONG_IS_64BIT]
            return cast_c(_type, val)
        case "signed long long":
            val = int(val) % 2**64
            return val - 2**64 * (val > (2**63 - 1))
        case "float":
            import struct
            return struct.unpack("f", struct.pack("f", val))[0]
        case "double":
            return float(val)
        case "signed char *":
            return str(val)
        case _:
            if _type[-1] == "*":
                _type = _type[:-1]
                return [cast_c(_type.rstrip(" "), v) for v in val]
            raise NotImplementedError(_type)


def cast_js(types: list[str], val: Any) -> Any:
    _type, *subtypes = types
    match _type:
        case "Number":
            return float(val) if "." in str(val) else int(val)
        case "BigInt":
            return int(val)
        case "String":
            return str(val)
        case "Boolean":
            return bool(val)
        case "Null":
            return None
        case "Date":
            return float(val)
        case "Array":
            return [cast_js(subtypes, v) for v in val]
        case "Set":
            return {cast_js(subtypes, v) for v in val}
        case "Map":
            return {
                cast_js(subtypes[0:1], k): cast_js(subtypes[1:2], v)
                for k, v in val.items()
            }
        case _:
            raise NotImplementedError(_type, val)


def cast_lua(types: list[str], val: Any) -> Any:
    _type, *subtypes = types
    match _type:
        case "integer":
            return int(val)
        case "float":
            return float(val)
        case "string":
            return str(val)
        case "boolean":
            return bool(val)
        case "nil":
            return None
        case "table":
            return [cast_lua(subtypes, v) for v in val]
        case _:
            raise NotImplementedError(_type)


def cast_python(types: list[str], val: Any) -> Any:
    _type, *subtypes = types
    match _type:
        case "int":
            return int(val)
        case "float":
            return float(val)
        case "str":
            return str(val)
        case "bool":
            return bool(val)
        case "NoneType":
            return None
        case "list":
            return [cast_python(subtypes[0:1], v) for v in val]
        case "dict":
            return {
                cast_python(subtypes[0:1], k): cast_python(subtypes[1:2], v)
                for k, v in val.items()
            }
            raise NotImplementedError("cast dict", subtypes)
        case _:
            raise NotImplementedError(types[0])


def cast_var(info: dict[str, Any], newinfo: dict[str, Any]) -> Any:
    val = newinfo["value"]
    match info["lang"]:
        case "c":
            return cast_c(info["type"][0], val)
        case "js":
            return cast_js(info["type"], val)
        case "lua":
            return cast_lua(info["type"], val)
        case "python":
            return cast_python(info["type"], val)
        case _:
            raise NotImplementedError(f'unknown language: {info["lang"]}')


def update_vars(lang: str, var_vals: dict[str, dict[str, Any]],
                new_var_vals: dict[str, dict[str, Any]]) -> None:
    for vname, newinfo in new_var_vals.items():
        if not vname in var_vals:
            var_vals[vname] = newinfo
            continue
        info = var_vals[vname]
        #variable was created in current lang, no casting required
        if newinfo["lang"] == info["lang"]:
            info["value"] = newinfo["value"]
            continue
        info["value"] = cast_var(info, newinfo)
    deleted = {k: v for k, v in var_vals.items() if not k in new_var_vals}
    for k, v in deleted.items():
        #dict/Map is converted to a C function, undetectable but not actually deleted
        if (lang == "c") and (v["type"][0] in ["dict", "Map"]): continue
        #lua uses nil to delete variables, override if it got nil from other lang
        if (lang == "lua") and (v["type"][0] in ["NoneType", "nil", "Null"]):
            continue
        del var_vals[k]
