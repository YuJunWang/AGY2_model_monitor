# AGY Fuel Gauge 🚀

Take control of your AI quota burn rate right now.

AGY Fuel Gauge hooks directly into Antigravity's internal gRPC-Web API to give you accurate token telemetry for both Gemini and External models. We didn't build a fragile browser scraper. You don't have to manually hunt for auth tokens. Just install it and it runs itself.

<p align="center">
  <img src="./assets/preview_5h.png" alt="5-Hour Quota View" width="45%" />
  &nbsp;&nbsp;
  <img src="./assets/preview_weekly.png" alt="Weekly Quota View" width="45%" />
</p>

## ✨ How it actually works

- **Zero Auth Setup**: The script automatically scans for your `language_server.exe` process and rips the `x-codeium-csrf-token` straight from the startup logs. You never have to touch a config file.
- **Custom UI**: We built a 270-degree arc gauge specifically optimized for OLED black backgrounds, and it calculates the exact time your quota resets.
- **Hourly Burn Rate**: It saves a local snapshot every 3 minutes so it can calculate your exact `🔥 %/h` consumption speed.

> [!NOTE]
> **To be honest, standard line charts are useless here.**  
> 1% of Gemini represents a massive amount of tokens compared to 1% of an external model. If we plotted them on the same Y-axis, the external line would just get flattened into a pancake.
> 
> **In other words, they need independent scales.** We built a Self-Normalized Mirrored Chart. Both datasets scale to their own local maximums. Gemini plots upwards, External plots downwards. You get side-by-side trends without the math getting in the way.

## 💻 Compatibility
- **Antigravity 2.0 (Desktop App)**: 100% supported (Run it as a Sidecar).
- **Antigravity IDE**: 100% supported.
- **Antigravity CLI (`agy`)**: No. The CLI doesn't spawn the persistent background server we need to hijack.

## 🛠️ Get Started

1. **Clone the repo**
   ```bash
   git clone https://github.com/YuJunWang/AGY_Fuel_Gauge.git
   cd AGY_Fuel_Gauge
   ```

2. **Install dependencies**
   ```bash
   pip install pystray Pillow
   ```

3. **Set it up as a background daemon (The right way)**
   Don't run this manually. Let Antigravity manage the lifecycle of this widget via Sidecars.
   
   1. Open your Antigravity config directory: `C:\Users\<YourUsername>\.gemini\config\sidecars\`
   2. Create a folder named `agy-fuel-gauge`.
   3. Create a `sidecar.json` file inside with the following content (update the `args` path to match your clone directory):
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

Now, restart your Antigravity IDE and look for the blue AGY icon in your Windows system tray. (Closing the window hides it in the tray; right-click the tray icon to show it again).

---

# AGY Fuel Gauge (中文說明) 🚀

馬上掌控你的 AI 額度消耗速度。

AGY Fuel Gauge 是一個直接掛載在 Antigravity 底層 (透過 gRPC-Web) 的監控小工具。我們沒有寫難維護的網頁爬蟲，你也不用手動去挖 Token 憑證。把這工具裝上去，它自己就會跑起來，並即時回報 Gemini 與其他外部模型的剩餘用量。

## ✨ 它是怎麼運作的？

- **自動找 Port 與 Token**：這支程式會自己去系統裡找 `language_server.exe` 這個 Process，並從啟動日誌直接把 `x-codeium-csrf-token` 抽出來。你不需要設定任何設定檔。
- **270 度弧形儀表板**：我們寫了一個專門配對 OLED 黑底的 UI 介面，順便幫你算好下一次配額重新發放的精準時間。
- **燃燒速率**：每 3 分鐘存一次檔，用來算出你現在每小時噴掉多少額度 (`🔥 %/h`)。

> [!NOTE]
> **老實說，用一般的折線圖根本看不出所以然。**  
> Gemini 只要消耗 1%，背後跑的運算量就遠大於 Claude 等外部模型。如果硬把它們塞進同一個座標軸，外部模型的那條線絕對會被壓成平的。
>
> **換句話說，圖表必須分開算。** 我們實作了自我正規化的「倒影圖 (Mirrored Area Chart)」。兩邊的數據會各自找出自己的最大值來當作天花板，Gemini 往上長，外部模型往下長。這樣趨勢就不會互打。

## 💻 支援環境
- **Antigravity 2.0 (桌面版應用程式)**：100% 支援（強烈建議你搭配 Sidecar 使用）。
- **Antigravity IDE**：100% 支援。
- **Antigravity CLI (`agy`)**：不支援。因為純指令列環境沒有常駐的背景服務可以讓我們抓取資料。

## 🛠️ 馬上開始設定

1. **把專案 Clone 下來**
   ```bash
   git clone https://github.com/YuJunWang/AGY_Fuel_Gauge.git
   cd AGY_Fuel_Gauge
   ```

2. **裝好必備套件**
   ```bash
   pip install pystray Pillow
   ```

3. **掛載成系統守護進程 (強烈建議)**
   不要手動去點兩下執行它。請讓 Antigravity 的 Sidecar 機制來管理這個工具的生殺大權。
   
   1. 打開你的 Antigravity 設定檔目錄（通常在 `C:\Users\<你的帳號>\.gemini\config\sidecars\`）。
   2. 建立一個叫做 `agy-fuel-gauge` 的新資料夾。
   3. 在裡面新增一個 `sidecar.json` 檔案，內容如下（記得把 `args` 裡面的路徑換成你剛剛 clone 的地方）：
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

現在，請直接重新啟動你的 Antigravity IDE，並檢查右下角 Windows 系統匣是不是出現了藍色的 AGY 小圖示！(按右上角 `✕` 會收進系統匣繼續背景記錄，點圖示右鍵可以再次喚醒它)

