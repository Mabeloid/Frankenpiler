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


## requirements for running code in specific languages:

- C: cppcheck, gdb, gcc

- JavaScript: node.js

- Lua: lua 5.3 or later

- Python: python (shouldn't be an issue)

## type conversion chart:

| lang |    type   |        C         |    JS   |      Lua      |   Python  |
|:----:|:---------:|:----------------:|:-------:|:-------------:|:---------:|
|  C   |    char   |        -         |  Number |    integer    |    int    |
|  C   |   char *  |        -         |  String |     string    |    str    |
|  C   |   double  |        -         |  Number |     float     |   float   |
|  C   |   float   |        -         |  Number |     float     |   float   |
|  C   |    int    |        -         |  Number |    integer    |    int    |
|  C   |    long   |        -         |  Number |    integer    |    int    |
|  C   | long long |        -         |  Number |    integer    |    int    |
|  C   |   U _[]   |        -         | Array[U]|    table[U]   |  list[U]  |
|  JS  |  Array[U] |      U _[]       |    -    |    table[U]   |  list[U]  |
|  JS  |   BigInt  |    long long     |    -    |    integer    |    int    |
|  JS  |  Boolean  |       int        |    -    |    boolean    |    bool   |
|  JS  |    Date   |      double      |    -    |     float     |  datetime |
|  JS  | Map[U, V] |      V _(U)      |    -    |  table[U, V]  | dict[U, V]|
|  JS  |    Null   |   void * NULL    |    -    |      nil      |  NoneType |
|  JS  |   Number  |long long / double|    -    |integer / float|int / float|
|  JS  |   Set[U]  |      U _[]       |    -    |    table[U]   |   set[U]  |
|  JS  |   String  |      char *      |    -    |     string    |    str    |
| Lua  |  boolean  |       int        | Boolean |       -       |    bool   |
| Lua  |   float   |      double      |  Number |       -       |   float   |
| Lua  |  integer  |    long long     |  Number |       -       |    int    |
| Lua  |    nil    |        X         |    X    |       -       |     X     |
| Lua  |   string  |      char *      |  String |       -       |    str    |
| Lua  |table[U, V]|      V _(U)      |Map[U, V]|       -       | dict[U, V]|
| Lua  |  table[U] |      U _[]       | Array[U]|       -       |  list[U]  |
|Python|    bool   |       int        | Boolean |    boolean    |     -     |
|Python| dict[U, V]|      V _(U)      |Map[U, V]|  table[U, V]  |     -     |
|Python|   float   |      double      |  Number |     float     |     -     |
|Python|    int    |    long long     |  Number |    integer    |     -     |
|Python|  list[U]  |      U _[]       | Array[U]|    table[U]   |     -     |
|Python|  NoneType |   void * NULL    |   Null  |      nil      |     -     |
|Python|   set[U]  |      U _[]       |  Set[U] |    table[U]   |     -     |
|Python|    str    |      char *      |  String |     string    |     -     |