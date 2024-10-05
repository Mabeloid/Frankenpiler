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
            if LONG_IS_64BIT:
                val = int(val) % 2**64
                return val - 2**64 * (val > (2**63 - 1))
            else:
                val = int(val) % 2**32
                return val - 2**32 * (val > (2**31 - 1))

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


def cast_lua(type: list[str], val: Any) -> Any:
    match type[0]:
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
            return [cast_lua(type[1:], v) for v in val]
        case _:
            raise NotImplementedError(type[0])


def cast_python(type: list[str], val: Any) -> Any:
    match type[0]:
        case "int":
            return int(val)
        case "str":
            return str(val)
        case "bool":
            return bool(val)
        case "NoneType":
            return None
        case "list":
            return [cast_python(type[1:], v) for v in val]
        case "dict":
            raise NotImplementedError("cast dict")
        case _:
            raise NotImplementedError(type[0])


def cast_var(info: dict[str, Any], newinfo: dict[str, Any]) -> Any:
    val = newinfo["value"]
    match info["lang"]:
        case "c":
            return cast_c(info["type"][0], val)
        case "lua":
            return cast_lua(info["type"], val)
        case "python":
            return cast_python(info["type"], val)


def update_vars(var_vals: dict[str, dict[str, Any]],
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
    deleted_vars = [vname for vname in var_vals if not vname in new_var_vals]
    for vname in deleted_vars:
        del var_vals[vname]
