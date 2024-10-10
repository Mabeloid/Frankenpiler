console.log("%s")
function Type(value) { return Object.prototype.toString.call(value).slice(8, -1); }
function formatvar(value) {
    let s
    try { s = JSON.stringify(value) }
    catch (TypeError) { return "..." }
    if (Type(value) == "Null") return "None"
    if (Type(value) == "Boolean") return s[0].toUpperCase() + s.slice(1)
    return s
}
for (const [name, value] of Object.entries(global)) {
    let s = Type(value)
    if (s == "Array") s += "|" + Type(value[0]);
    s += "%s" + name + "%s" + formatvar(value)
    console.log(s)
}