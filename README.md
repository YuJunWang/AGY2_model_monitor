# AGY Fuel Gauge 🚀

Stop guessing your quotas. 

AGY Fuel Gauge hooks directly into Antigravity's internal gRPC-Web API to give you real-time, accurate token telemetry for both Gemini and External models. No browser scraping. No manual authentication. It just works.

<p align="center">
  <img src="./assets/preview_5h.png" alt="5-Hour Quota View" width="45%" />
  &nbsp;&nbsp;
  <img src="./assets/preview_weekly.png" alt="Weekly Quota View" width="45%" />
</p>

## ✨ Why this exists

- **Zero Auth Setup**: We automatically bind to your `language_server.exe` process and rip the `x-codeium-csrf-token` straight from the startup logs. You never have to touch a config file.
- **Real-Time Telemetry**: Directly queries the internal quota API.
- **Segmented Control**: Switch between 5-Hour and Weekly limits instantly without resizing the window.
- **Hourly Burn Rate**: Calculates your exact `🔥 %/h` consumption speed, logged locally every 3 minutes.

> [!NOTE]
> **The Mirrored Area Chart**  
> Gemini and Claude/GPT quotas aren't 1:1. 1% of Gemini represents a massive amount of tokens compared to 1% of an external model. If we plotted them on the same axis, the Gemini line would completely flatten the other. 
> 
> **The fix:** A Self-Normalized Mirrored Chart. We scale both datasets to their own local maximums, plotting Gemini upwards and External downwards. You get a perfect side-by-side trend analysis without the math getting in the way.

## 💻 Compatibility
- **Antigravity 2.0 (Desktop App)**: 100% supported.
- **Antigravity IDE**: 100% supported.
- **Antigravity CLI (`agy`)**: No. The CLI doesn't spawn the persistent background language server we need to hijack.

## 🛠️ Get Started

1. **Clone it**
   ```bash
   git clone https://github.com/YuJunWang/AGY_Fuel_Gauge.git
   cd AGY_Fuel_Gauge
   ```

2. **Dependencies**
   ```bash
   pip install pystray Pillow
   ```

3. **Automate it (The right way to use this)**
   Don't run this manually. Set it up as an [Antigravity Sidecar](https://antigravity.google/docs/sidecars). It will launch when you open your workspace and stay alive as a background daemon.
   
   - Go to your Antigravity config: `C:\Users\<YourUsername>\.gemini\config\sidecars\`
   - Create a folder named `agy-fuel-gauge`.
   - Drop a `sidecar.json` file inside:
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
   - Restart Antigravity IDE. That's it. You'll see a blue `AGY` icon in your system tray. Click the `✕` to hide the window (it keeps logging in the background). Right-click the tray icon to bring it back.

---

# AGY Fuel Gauge (中文說明) 🚀

不用再盲猜你還剩多少額度了。

AGY Fuel Gauge 透過 gRPC-Web 直接掛載在 Antigravity 底層，給你最精準的 Gemini 與外部模型用量數據。沒有難用的網頁爬蟲，不用手動抓 Token，裝上去就能跑。

## ✨ 核心特色

- **零設定認證**：我們直接鎖定 `language_server.exe` 進程找 Port，並從系統日誌把 `x-codeium-csrf-token` 挖出來。你不需要做任何麻煩的設定。
- **原生的 270 度儀表**：專為 OLED 深色模式設計的 UI，精確換算下次配額重置時間。
- **燃燒率追蹤**：每 3 分鐘自動記錄一次，精準計算你現在每小時的消耗速率 (`🔥 %/h`)。

> [!NOTE]
> **為什麼不用一般的折線圖？**  
> Gemini 1% 的運算量遠大於 Claude 或 GPT 等外部模型，如果把它們放在同一個座標軸，其中一條線絕對會被壓平。
>
> **我們的解法**：自我正規化的「倒影圖 (Mirrored Area Chart)」。雙方數據各自根據自己的最大值縮放，把 Gemini 往上畫，External 往下畫。趨勢一目了然，互不打架。

## 💻 相容性
- **Antigravity 2.0 (桌面版應用程式)**：完全支援（強烈建議搭配 Sidecar 使用）。
- **Antigravity IDE**：完全支援。
- **Antigravity CLI (`agy`)**：不支援。因為純命令列沒有我們需要的常駐背景伺服器。

## 🛠️ 安裝方式

1. **Clone 專案**
   ```bash
   git clone https://github.com/YuJunWang/AGY_Fuel_Gauge.git
   cd AGY_Fuel_Gauge
   ```

2. **安裝套件**
   ```bash
   pip install pystray Pillow
   ```

3. **設定 Sidecar 自動啟動 (強烈建議)**
   把它當作一個系統守護進程，讓 Antigravity 來管理它的生殺大權。
   
   - 到你的 Antigravity 設定檔目錄（通常在 `C:\Users\<你的使用者名稱>\.gemini\config\sidecars\`）。
   - 建一個資料夾叫 `agy-fuel-gauge`。
   - 在裡面放一個 `sidecar.json`（記得改路徑）：
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
   - 重新啟動 IDE。完成。系統列會出現一個藍色小圖示。按 `✕` 可以把視窗收進背景，點右鍵選 `Show Widget` 就能叫出來。

