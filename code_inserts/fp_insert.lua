function Print_G()
    local function Type(v) return math.type(v) or type(v) end
    local function formatvar(v)
        local s = tostring(v)
        if Type(v) == "string" then
            return '"' .. s .. '"'
        elseif Type(v) == "boolean" then
            return s:sub(1, 1):upper() .. s:sub(2)
        elseif Type(v) == "nil" then
            return "None"
        else
            return s
        end
    end

    for name, value in pairs(_G) do
        local _Gstr = Type(value)
        if _Gstr == "table" then
            _Gstr = _Gstr .. "|" .. Type(value[1]) .. "%s" .. name .. "%s"
            _Gstr = _Gstr .. "[ "
            for k, v in ipairs(value) do
                _Gstr = _Gstr .. formatvar(v) .. ","
            end
            _Gstr = _Gstr:sub(1, -2) .. "]"
        else
            _Gstr = _Gstr .. "%s" .. name .. "%s" .. formatvar(value)
        end
        if name ~= "Print_G" then print(_Gstr) end
    end
end

print("%s")
Print_G()
