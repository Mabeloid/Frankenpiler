```
c       §char text[] = "!dlrow";
lua     §text = text .. " olleH"
python  §text = text[::-1]
js      §console.log(text)

>>> Hello world!
```

works for python versions 3.12 or later


to install the required python library:
`pip install -r requirements.txt`


requirements for running code in specific languages:

- C: cppcheck, gdb, gcc

- JavaScript: node.js

- Lua: lua 5.3 or later

- Python: python (shouldn't be an issue)