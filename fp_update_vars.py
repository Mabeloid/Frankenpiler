from typing import Any


def cast_var(oldinfo: dict[str, Any], info: dict[str, Any]) -> Any:
    val = info["value"]
    lang = info["lang"]
    vtype = " ".join(f for f in oldinfo["type"] if f)
    match vtype:

    #   # c
        case "unsigned char":
            return int(val) % 256
        case "signed char":
            val = int(val) % 256
            return val - 256 * (val > 127)
        case "unsigned int":
            return int(val) % 2**32
        case "signed int":
            val = int(val) % 2**32
            return val - 2**32 * (val > (2**31 - 1))

        case "float":
            if lang in ["c"]:
                import struct
                return struct.unpack("f", struct.pack("f", val))[0]
            return float(val)
        case "double":
            return float(val)
        case "signed char *":
            return str(val)

        # python
        case "int":
            return int(val)
        case "str":
            return str(val)
        case "bool":
            return bool(val)
        case "NoneType":
            return None
        case "list[float]":
            return [float(v) for v in val]
        case "list[int]":
            return [int(v) for v in val]

        # lua
        case "number":
            return val
            if isinstance(val, int): return int(val)
            else: return float(val)
        case "string":
            return str(val)
        case "boolean":
            return bool(val)
        case "nil":
            return None
        case "table[string]":
            return [str(v) for v in val]
        case "table[number]":
            return [v for v in val]

        # other
        case _:
            raise NotImplementedError(vtype)


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
