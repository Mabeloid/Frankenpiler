print("%s")
for name, value in globals().copy().items():
    s = type(value).__name__
    if isinstance(value, list): s += "|" + type(value[0]).__name__
    elif isinstance(value, dict):
        dkey, dval = ([*value.items()] + [[None, None]])[0]
        s += "|" + type(dkey).__name__
        s += "|" + type(dval).__name__
    s += "%s" + name + "%s" + str(value)
    print(s)