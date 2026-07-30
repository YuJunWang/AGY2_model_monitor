# AGY Fuel Gauge 🚀

AGY Fuel Gauge is a background telemetry widget built to solve a simple problem: keeping track of your AI quotas without breaking your flow state. 

It hooks directly into Antigravity's internal gRPC-Web API to give you an accurate, real-time look at your token usage for both Gemini and External models. We avoided building a fragile browser scraper, and you don't have to manually hunt for auth tokens. Just install it, and it quietly does its job in the background.

<p align="center">
  <img src="./assets/preview_5h.png" alt="5-Hour Quota View" width="45%" />
  &nbsp;&nbsp;
  <img src="./assets/preview_weekly.png" alt="Weekly Quota View" width="45%" />
</p>

## ✨ How it actually works

- **Zero Auth Setup**: The script automatically scans for your active `language_server.exe` process to dynamically find its listening Port, and simply rips the `x-codeium-csrf-token` straight from the startup logs. You never have to touch a config file or deal with logins.
- **Custom UI**: We built a custom 270-degree arc gauge specifically optimized to look good on OLED black backgrounds. Plus, it calculates the exact time your quota will reset.
- **Hourly Burn Rate**: To help you pace yourself, it saves a local snapshot every 3 minutes so it can calculate your exact `🔥 %/h` consumption speed.

> [!NOTE]
> **Why not use a standard line chart?**  
> 1% of Gemini represents a massive amount of tokens compared to 1% of an external model. If we plotted them on the exact same Y-axis, the external line would just get flattened into a pancake and you wouldn't be able to read it.
> 
> **To solve this**, we built a Self-Normalized Mirrored Chart. Both datasets scale to their own local maximums. Gemini plots upwards, External plots downwards. This way, you get clear, side-by-side trends without the math getting in the way.

## 💻 Compatibility
- **Antigravity 2.0 (Desktop App)**: 100% supported (Run it as a Sidecar).
- **Antigravity IDE**: 100% supported.
- **Antigravity CLI (`agy`)**: Not supported. The CLI doesn't spawn the persistent background server we need to hijack for data.

## 🛠️ Get Started

1. **Clone the repo**
   ```bash
   git clone https://github.com/YuJunWang/AGY_Fuel_Gauge.git
   cd AGY_Fuel_Gauge
   ```

2. **Install dependencies**
   Make sure you have Python installed, then run:
   ```bash
   pip install pystray Pillow
   ```

3. **Set it up as a background daemon (Highly Recommended)**
   While you could run this manually, it's highly recommended to let Antigravity manage the lifecycle of this widget via Sidecars.
   
   1. Open up your Antigravity config directory (usually around `C:\Users\<YourUsername>\.gemini\config\sidecars\`).
   2. Create a new folder in there named `agy-fuel-gauge`.
   3. Create a `sidecar.json` file inside with the following content (remember to update the `args` path to match where you cloned the repo):
      ```json
      {
        "description": "AGY Fuel Gauge",
        "command": "pythonw",
        "args": [
          "E:\\Path\\To\\AGY_Fuel_Gauge\\widget.py"
        ],
        "restart_policy": "always"
      }
      ```

Once that's done, just restart your Antigravity IDE. You should see a little blue AGY icon pop up in your Windows system tray. (Closing the window just hides it in the tray while it keeps logging; right-click the tray icon to show it again).

---

# AGY Fuel Gauge (中文說明) 🚀

寫程式時若要隨時關注 AI 額度，頻繁切換視窗往往會打斷心流，這正是 AGY Fuel Gauge 誕生的原因。

它是一個直接掛載在 Antigravity 底層 (透過 gRPC-Web) 的背景監控工具。我們捨棄了容易失效的網頁爬蟲，也不需要手動撈取 Token 憑證。安裝後，它就能在背景穩定運行，即時回報 Gemini 與外部模型的剩餘用量。

## ✨ 它是怎麼運作的？

- **自動找 Port 與 Token**：這支程式會去系統裡找 `language_server.exe` 這個 Process 來定位目前本機端監聽的 Port，並從啟動日誌直接把 `x-codeium-csrf-token` 抽出來。這意味著你不需要去設定任何麻煩的設定檔。
- **270 度弧形儀表板**：為了讓畫面看起來更有質感，我們寫了一個專門配對 OLED 黑底的 UI 介面，而且還會幫你算好下一次配額重新發放的精準時間。
- **燃燒速率**：它每 3 分鐘會在背景存一次檔，藉此來算出你現在每小時消耗了多少額度 (`🔥 %/h`)，讓你可以稍微控制一下使用節奏。

> [!NOTE]
> **為什麼不使用一般的折線圖？**  
> 因為 Gemini 只要消耗 1%，背後跑的運算量就遠大於 Claude 等外部模型。如果我們硬把它們塞進同一個座標軸，外部模型的那條線絕對會被壓成平的，根本看不出趨勢。
>
> **為了解決這個問題**，我們實作了自我正規化的「倒影圖 (Mirrored Area Chart)」。兩邊的數據會各自找出自己的最大值來當作天花板進行縮放，Gemini 往上長，外部模型往下長。這樣兩邊的趨勢清晰可見，也不會互相打架。

## 💻 支援環境
- **Antigravity 2.0 (桌面版應用程式)**：100% 支援（強烈建議搭配 Sidecar 機制使用）。
- **Antigravity IDE**：100% 支援。
- **Antigravity CLI (`agy`)**：不支援。純指令列環境沒有常駐的背景服務可以讓我們抓取資料。

## 🛠️ 安裝方式

1. **把專案 Clone 下來**
   ```bash
   git clone https://github.com/YuJunWang/AGY_Fuel_Gauge.git
   cd AGY_Fuel_Gauge
   ```

2. **裝好必備套件**
   確認你有裝好 Python 之後，執行：
   ```bash
   pip install pystray Pillow
   ```

3. **掛載成系統守護進程 (強烈建議)**
   雖然你可以手動執行它，但強烈建議讓 Antigravity 的 Sidecar 機制來自動管理這個工具。
   
   1. 打開你的 Antigravity 設定檔目錄（通常在 `C:\Users\<你的帳號>\.gemini\config\sidecars\`）。
   2. 在裡面建立一個叫做 `agy-fuel-gauge` 的新資料夾。
   3. 接著新增一個 `sidecar.json` 檔案，貼上以下內容（記得把 `args` 裡面的路徑換成你實際 clone 的地方）：
      ```json
      {
        "description": "AGY Fuel Gauge",
        "command": "pythonw",
        "args": [
          "E:\\你的\\路徑\\AGY_Fuel_Gauge\\widget.py"
        ],
        "restart_policy": "always"
      }
      ```

設定好之後，只要重新啟動你的 Antigravity IDE，就可以檢查右下角 Windows 系統匣是不是出現藍色的 AGY 小圖示了！(按右上角的 `✕` 只是把它收進系統匣繼續背景記錄，對著圖示點右鍵就可以再次喚醒它)。