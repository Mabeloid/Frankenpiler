import os
from typing import Optional
import fp_c, fp_lua, fp_python


class FrankenPiler:

    full_evals = {
        "c": fp_c.full_eval,
        "lua": fp_lua.full_eval,
        "python": fp_python.full_eval
    }

    def readcode(self, filepath: str) -> list[list[str]]:
        with open(filepath, "r", encoding="utf-8") as f:
            sourcelines = f.read().split("\n")

        lines: list[list[str]] = []
        for line in sourcelines:
            if not line: continue
            lang, code = line.split("§")
            lang = lang.rstrip("\t ")
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
        if True: os.system("cls")

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
                for k, v in var_vals.items():
                    print(f"{k} = {v}")
                print("-" * 50)

        #delete tmp files
        for f in os.listdir("tmpcode"):
            os.remove("tmpcode/" + f)


if __name__ == "__main__":
    FrankenPiler("example_1.txt")
