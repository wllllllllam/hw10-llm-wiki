# 永續時尚 LLM Wiki：給 AI 的工作規則

這個資料夾照 Karpathy 的「LLM Wiki」做法：原始資料放 `raw/`，AI 把它整理成 `wiki/` 裡互相連結的頁面，
之後要回答問題或做簡報，都**只從 Wiki 拿內容**，不憑記憶補。

## 資料夾
- `raw/S1.md`～`raw/S6.md`：原始資料卡（網址、日期、英文原句摘錄）。**只增不改**。
- `wiki/`：AI 整理的中文頁面。`index.md` 目錄、`sources.md` 來源清單、`log.md` 每次動作的紀錄。
- `slides/index.html`：從 Wiki 產生的教學簡報。
- `workflow/check.py`：檢查腳本；`workflow/runs/`：每次檢查的輸出。

## 三個動作
1. **Ingest（收資料）**：新資料 → 存成 `raw/S7.md` → 讀過後更新相關 Wiki 頁（一篇資料常會動到好幾頁）
   → 更新 `index.md`、`sources.md` → 在 `log.md` 記一筆 → **每收完一篇就**跑 `python3 workflow/check.py wiki`
   （第一次執行是 6 篇全收完才檢查，錯誤一次冒出 20 個、分不出是哪篇造成的，所以往前移）。
2. **Query（查詢）**：回答問題或寫簡報時，先讀 `index.md` 找頁面，再讀頁面；Wiki 沒有的就說沒有，
   要補就回到 Ingest，不要直接寫進答案。
3. **Lint（檢查）**：`check.py wiki` 檢查格式；另外 AI 自己讀一遍找「來源互相矛盾」的地方，寫進 `contradictions.md`。

## 頁面格式
- 每條重點用 `- ` 開頭，結尾標來源 `[S1]`；數字一律用阿拉伯數字，照原文寫（例：2,700 公升）。
- 換算單位時把原文寫法放括號（例：930 億（93 billion））；**原文沒有的換算不准寫**（例：gallons 換公升）。
- 頁面之間用 `[[頁名]]` 連結（不含 .md）。
- 來源說法不一樣時不要挑一個，兩個都寫並連到 [[contradictions]]。

## 簡報規則
- 先列大綱：每一頁要用哪幾個 Wiki 頁，**頁面不存在就回 Ingest，不要先寫簡報**。
- 每一頁 `<section>` 加 `data-wiki="頁名.md"`，標這頁內容出自哪個 Wiki 頁。
- 章節編號放在 `class="kicker"` 或 `class="step"` 裡（檢查會略過）。
- 簡報裡出現的數字，都要在標的 Wiki 頁裡找得到（`check.py slides` 會擋）。
- 寫給不懂這個主題的人：先講是什麼，再講為什麼重要，最後講能做什麼。
