"""把下載的網頁轉成純文字（raw 資料），給 check.py 比對用。"""
import sys, re, html
from html.parser import HTMLParser

class P(HTMLParser):
    skip = {"script", "style", "nav", "footer", "header", "noscript", "svg"}
    def __init__(self):
        super().__init__(); self.out = []; self.depth = 0
    def handle_starttag(self, t, a):
        if t in self.skip: self.depth += 1
        if t in {"p", "li", "h1", "h2", "h3", "h4", "br", "tr", "div"}: self.out.append("\n")
    def handle_endtag(self, t):
        if t in self.skip and self.depth: self.depth -= 1
    def handle_data(self, d):
        if not self.depth: self.out.append(d)

p = P(); p.feed(open(sys.argv[1], encoding="utf-8", errors="ignore").read())
text = re.sub(r"[ \t]+", " ", "".join(p.out))
text = re.sub(r"\n\s*\n+", "\n\n", text)
open(sys.argv[2], "w").write(html.unescape(text).strip())
