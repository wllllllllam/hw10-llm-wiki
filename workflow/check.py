"""LLM Wiki 的兩個檢查節點（不用 AI、不用網路，規則寫死）。

用法：
  python3 workflow/check.py wiki     # 節點 3：Wiki 檢查（lint）
  python3 workflow/check.py slides   # 節點 6：簡報檢查

規則：
  wiki   W1 內容頁的每一條重點（- 開頭）都要標來源 [S1]~[S6]
         W2 重點裡的每個數字，都要出現在它標的 raw 原文裡
         W3 [[頁面]] 連結要連得到
         W4 每篇 raw 資料至少被引用一次
  slides P1 每一頁 <section> 都要有 data-wiki，而且頁面存在
         P2 簡報裡的每個數字，都要出現在這頁標的 Wiki 頁裡
         P3（提醒）沒被任何一頁簡報用到的 Wiki 頁
結果同時存一份到 workflow/runs/，當作檢查紀錄。
"""
import re, sys, datetime, pathlib, html

ROOT = pathlib.Path(__file__).resolve().parent.parent
WIKI, RAW, SLIDES = ROOT / "wiki", ROOT / "raw", ROOT / "slides" / "index.html"
NOT_CONTENT = {"index.md", "log.md", "sources.md"}
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve".split())}
MONTHS = {m: i for i, m in enumerate("January February March April May June July "
                                     "August September October November December".split(), 1)}


def nums(text):
    return {n.replace(",", "").rstrip(".") for n in NUM.findall(text)}


def raw_nums(text):
    """原文的數字，加上英文寫法換成阿拉伯數字、億／萬換算後的值（第一次執行後加的）。"""
    out = nums(text)
    out |= {str(v) for w, v in WORDS.items() if re.search(rf"\b{w}\b", text, re.I)}
    out |= {str(v) for m, v in MONTHS.items() if re.search(rf"\b{m}\b", text)}
    for n, unit in re.findall(r"(\d[\d,.]*)\s*(billion|million)", text, re.I):
        x = float(n.replace(",", ""))
        out.add(f"{x * (10 if unit.lower() == 'billion' else 100):g}")  # 億、萬
    if re.search(r"half a million", text, re.I):
        out.add("50")  # 50 萬
    return out


def strip_refs(line):
    line = re.sub(r"\[S\d\]", "", line)
    return re.sub(r"\[\[[^\]]+\]\]", "", line)


def check_wiki():
    errors, cited = [], set()
    rawn = {p.stem: raw_nums(p.read_text()) for p in RAW.glob("S*.md")}
    pages = {p.name for p in WIKI.glob("*.md")}
    for p in sorted(WIKI.glob("*.md")):
        for i, line in enumerate(p.read_text().splitlines(), 1):
            for link in re.findall(r"\[\[([^\]]+)\]\]", line):
                if link + ".md" not in pages:
                    errors.append(f"W3 {p.name}:{i} 連結 [[{link}]] 找不到頁面")
            if p.name in NOT_CONTENT or not line.startswith("- "):
                continue
            if not re.sub(r"^- [^：]*：", "", strip_refs(line)).strip(" -、"):
                continue  # 只放連結的「相關頁面」行（第一次執行後加的）
            srcs = re.findall(r"\[(S\d)\]", line)
            cited.update(srcs)
            if not srcs:
                errors.append(f"W1 {p.name}:{i} 沒標來源：{line[:40]}")
                continue
            pool = set().union(*(rawn.get(s, set()) for s in srcs))
            for n in nums(strip_refs(line)) - pool:
                errors.append(f"W2 {p.name}:{i} 數字 {n} 不在 {'/'.join(srcs)} 原文裡")
    for s in sorted(set(rawn) - cited):
        errors.append(f"W4 {s} 沒有被任何 Wiki 頁引用")
    return errors, []


def check_slides():
    errors, warns, used = [], [], set()
    doc = SLIDES.read_text()
    sections = re.findall(r"<section([^>]*)>(.*?)</section>", doc, re.S)
    for k, (attrs, body) in enumerate(sections, 1):
        m = re.search(r'data-wiki="([^"]*)"', attrs)
        if not m:
            errors.append(f"P1 第 {k} 頁沒有 data-wiki")
            continue
        refs = m.group(1).split()
        missing = [r for r in refs if not (WIKI / r).exists()]
        if missing:
            errors.append(f"P1 第 {k} 頁標的 Wiki 頁不存在：{missing}")
            continue
        used.update(refs)
        # 章節編號（kicker、step）不是事實，不檢查（第一次執行後加的）
        body = re.sub(r'<(div|span) class="(kicker|step)">.*?</\1>', " ", body)
        text = html.unescape(re.sub(r"<[^>]+>", " ", body))
        pool = set().union(*(nums((WIKI / r).read_text()) for r in refs))
        for n in sorted(nums(text) - pool):
            errors.append(f"P2 第 {k} 頁 數字 {n} 不在 {refs} 裡")
    for p in sorted(WIKI.glob("*.md")):
        if p.name not in NOT_CONTENT and p.name not in used:
            warns.append(f"P3（提醒）{p.name} 沒被任何一頁簡報用到")
    return errors, warns


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "wiki"
    errors, warns = check_wiki() if mode == "wiki" else check_slides()
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    lines = [f"# check.py {mode}  {stamp}"] + errors + warns
    lines.append(f"結果：{'通過' if not errors else '不通過'}（錯誤 {len(errors)}，提醒 {len(warns)}）")
    out = "\n".join(lines)
    print(out)
    runs = ROOT / "workflow" / "runs"
    runs.mkdir(exist_ok=True)
    (runs / f"{stamp}-{mode}.txt").write_text(out + "\n")
    sys.exit(1 if errors else 0)
