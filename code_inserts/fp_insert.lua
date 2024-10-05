function Print_G()
    local function Type(v) return tostring(math.type(v) or type(v)) end
    local function formatvar(v)
        local s = tostring(v):gsub("\n", "\\n")
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
            local ktype, vtype
            for k, v in pairs(value) do
                ktype, vtype = Type(k), Type(v)
                break
            end
            if ktype then
                _Gstr = "table|" .. ktype .. "|" .. vtype .. "%s" .. name .. "%s"
            else
                _Gstr = "table|integer|nil" .. "%s" .. name .. "%s"
            end
            _Gstr = _Gstr .. "{"
            for k, v in pairs(value) do
                _Gstr = _Gstr .. formatvar(k) .. ":" .. formatvar(v) .. ", "
            end

            if _Gstr:sub(-2) == ", " then
                _Gstr = _Gstr:sub(1, -3)
            else
                _Gstr = _Gstr .. "1:None"
            end
            _Gstr = _Gstr .. "}"
        else
            _Gstr = _Gstr .. "%s" .. name .. "%s" .. formatvar(value)
        end
        if name ~= "Print_G" then print(_Gstr) end
    end
end

print("%s")
Print_G()
