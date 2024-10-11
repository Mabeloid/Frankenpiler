print("%s")
frozenglobals = globals().copy().items()


def formatvar(value):
    if type(value).__name__ == "datetime": return str(value.timestamp())
    return str(value)


for name, value in frozenglobals:
    s = type(value).__name__
    if s == "type": continue
    if isinstance(value, list):
        value = value or [None]
        s += "|" + type(value[0]).__name__
    elif isinstance(value, dict):
        dkey, dval = ([*value.items()] or [[None, None]])[0]
        s += "|" + type(dkey).__name__
        s += "|" + type(dval).__name__
    s += "%s" + name + "%s" + formatvar(value)
    print(s)
