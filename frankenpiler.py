import os
from typing import Optional
import fp_c, fp_js, fp_lua, fp_python


class FrankenPiler:

    full_evals = {
        "c": fp_c.full_eval,
        "js": fp_js.full_eval,
        "lua": fp_lua.full_eval,
        "python": fp_python.full_eval,
    }

    def readcode(self, filepath: str) -> list[list[str]]:
        with open(filepath, "r", encoding="utf-8") as f:
            sourcelines = f.read().split("\n")

        lines: list[list[str]] = []
        for line in sourcelines:
            if not line: continue
            lang, _, code = line.partition("§")
            lang = lang.rstrip("\t ").lower()
            lines.append([lang, code])

        #merge same-language code
        codes = lines[0:1]
        for prev, line in zip(lines, lines[1:]):
            [prevlang, prevcode] = prev
            [lang, code] = line
            if lang == prevlang:
                codes[-1][1] = codes[-1][1] + "\n" + code
            else:
                codes.append([lang, code])

        return codes

    def __init__(self,
                 filepath: str,
                 args: Optional[str | list[str]] = None) -> None:

        if args: raise NotImplementedError("args")

        codes = self.readcode(filepath)
        os.makedirs("tmpcode", exist_ok=True)

        var_vals = {}
        for lang, code in codes:
            if not lang in self.full_evals: raise NotImplementedError(lang)
            var_vals = self.full_evals[lang](code, var_vals)
            if not True:
                print("-" * 50)
                print(lang)
                print(code)
                if not var_vals:
                    print("no vars!".center(50, "."))
                else:
                    print("vars".center(50, "."))
                    for k, v in var_vals.items():
                        print(f"{k} = {v}")
                print("-" * 50)

        if False:
            #delete tmp files
            for f in os.listdir("tmpcode"):
                os.remove("tmpcode/" + f)


if __name__ == "__main__":
    os.system("cls")
    for i in range(11, 12):
        FrankenPiler("examples/example_%d.txt" % i)
    exit()
    for i in range(0, 11):
        print((" " + str(i) + " ").center(50, "="))
        FrankenPiler("examples/example_%d.txt" % i)
