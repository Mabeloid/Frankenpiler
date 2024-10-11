console.log("%s")
function Type(value) { return Object.prototype.toString.call(value).slice(8, -1) }
function formatvar(value) {
    if (Type(value) == "Null") return "None"
    if (Type(value) == "BigInt") { let s = value.toString(); return s[-1] == "n" ? s.slice(0, -1) : s }
    if (Type(value) == "Date") return (value.getTime() / 1000).toString()
    if (Type(value) == "Boolean") { let s = value.toString(); return s[0].toUpperCase() + s.slice(1) }
    try { return JSON.stringify(value) }
    catch (TypeError) { return "..." }
}
for (const [name, value] of Object.entries(global)) {
    let s = Type(value)
    if (s == "Array") {
        s += "|" + Type(value[0]) + "%s" + name + "%s"
        s += "[" + value.map(v => formatvar(v)).join(", ") + "]"
    }
    else if (s == "Set") {
        let _value = [...value]
        s += "|" + Type(_value[0]) + "%s" + name + "%s"
        s += "{" + _value.map(v => formatvar(v)).join(", ") + "}"
    }
    else if (s == "Map") {
        let _value = [...value.entries()]
        s += "|" + Type(_value[0][0]) + "|" + Type(_value[0][1]) + "%s" + name + "%s"
        s += "{" + _value.map(([k, v]) => formatvar(k) + ": " + formatvar(v)).join(", ") + "}"
    }
    else { s += "%s" + name + "%s" + formatvar(value) }
    console.log(s)
}