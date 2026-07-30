# AGY Fuel Gauge 🚀

AGY Fuel Gauge is a background telemetry widget that keeps your AI quotas visible without pulling you out of your flow state.

The trick is surprisingly simple: Antigravity IDE already runs a local background daemon (`language_server.exe`) that handles all your token traffic. We eavesdrop on it. This widget hooks directly into that internal gRPC-Web API, giving you an accurate, real-time view of your Gemini and External model usage—no credentials required, no config files to maintain.

<p align="center">
  <img src="./assets/preview_5h.png" alt="5-Hour Quota View" width="45%" />
  &nbsp;&nbsp;
  <img src="./assets/preview_weekly.png" alt="Weekly Quota View" width="45%" />
</p>

## ✨ How it actually works

- **Zero Auth Setup**: The widget scans for your active `language_server.exe` process to dynamically locate its listening port, then reads the `x-codeium-csrf-token` straight from the startup logs. Nothing to configure.
- **Custom UI**: A 270-degree arc gauge designed for OLED black backgrounds, with an exact quota reset countdown.
- **Hourly Burn Rate**: Local snapshots every 3 minutes let it calculate your exact `🔥 %/h` consumption rate, so you can pace yourself.

> [!NOTE]
> **Why not a standard line chart?**  
> 1% of Gemini represents vastly more tokens than 1% of an external model. On a shared Y-axis, the external model line gets completely flattened—unreadable.
>
> **The fix**: a Self-Normalized Mirrored Chart. Each dataset scales to its own local maximum. Gemini plots upward, External plots downward. Two clear trends, zero interference.

## 💻 Compatibility
- **Antigravity 2.0 (Desktop App)**: 100% supported — run it as a Sidecar.
- **Antigravity IDE**: 100% supported.
- **Antigravity CLI (`agy`)**: Not supported. The CLI doesn't maintain the background server this widget taps into.

## 🛠️ Get Started

1. **Clone the repo**
   ```bash
   git clone https://github.com/YuJunWang/AGY_Fuel_Gauge.git
   cd AGY_Fuel_Gauge
   ```

2. **Install dependencies**
   Make sure Python is installed, then:
   ```bash
   pip install pystray Pillow
   ```

3. **Set it up as a background daemon (Recommended)**
   The cleanest way to run this is via Antigravity's Sidecar mechanism, which handles auto-start and crash recovery automatically.

   1. Open your Antigravity config directory (usually `C:\Users\<YourUsername>\.gemini\config\sidecars\`).
   2. Create a new folder named `agy-fuel-gauge`.
   3. Inside it, create a `sidecar.json` with the following content (update the `args` path to your clone location):
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

Restart your Antigravity IDE. A blue AGY icon should appear in your Windows system tray. (The `✕` button hides it to the tray and keeps logging in the background; right-click the icon to bring it back.)

---

# AGY Fuel Gauge（中文說明）🚀

寫程式時若要隨時關注 AI 額度，頻繁切換視窗往往會打斷心流，這正是 AGY Fuel Gauge 誕生的原因。

做法其實很直觀：既然 Antigravity IDE 已經在你的電腦裡跑了一支負責通訊的背景精靈（`language_server.exe`），我們直接在它的內部通道（gRPC-Web）上「旁聽」就好。不需要你的帳號憑證，也不需要維護任何設定檔，安裝好就能在背景持續回報 Gemini 與外部模型的即時用量。

## ✨ 它是怎麼運作的？

- **自動找 Port 與 Token**：程式會找到 `language_server.exe` 的進程來定位目前監聽的 Port，並從啟動日誌直接取出 `x-codeium-csrf-token`。你什麼都不用設定。
- **270 度弧形儀表板**：專為 OLED 黑底設計的 UI，同時顯示配額重新發放的倒數時間。
- **燃燒速率**：每 3 分鐘在背景存一次快照，藉此計算出你的 `🔥 %/h` 消耗速率，讓你可以調整使用節奏。

> [!NOTE]
> **為什麼不用一般的折線圖？**  
> Gemini 消耗 1% 的運算量，遠大於 Claude 等外部模型的 1%。如果強行畫在同一個 Y 軸上，外部模型的那條線會完全被壓平，根本看不出趨勢。
>
> **解法**：自我正規化的倒影圖（Mirrored Area Chart）。兩邊各自以自己的最大值為上限縮放——Gemini 往上長，外部模型往下長。兩條趨勢線清晰可讀，互不干擾。

## 💻 支援環境
- **Antigravity 2.0（桌面版）**：100% 支援，建議搭配 Sidecar 機制使用。
- **Antigravity IDE**：100% 支援。
- **Antigravity CLI（`agy`）**：不支援。指令列環境沒有這支工具需要旁聽的背景服務。

## 🛠️ 安裝方式

1. **把專案 Clone 下來**
   ```bash
   git clone https://github.com/YuJunWang/AGY_Fuel_Gauge.git
   cd AGY_Fuel_Gauge
   ```

2. **裝好必備套件**
   確認 Python 已安裝，接著執行：
   ```bash
   pip install pystray Pillow
   ```

3. **掛載成背景守護進程（建議）**
   透過 Antigravity 的 Sidecar 機制來管理，可以自動啟動與崩潰復原，省去手動執行的麻煩。

   1. 打開 Antigravity 設定檔目錄（通常在 `C:\Users\<你的帳號>\.gemini\config\sidecars\`）。
   2. 在裡面建立一個叫做 `agy-fuel-gauge` 的新資料夾。
   3. 在資料夾內新增 `sidecar.json`，內容如下（記得把路徑換成你實際 clone 的位置）：
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

重新啟動 Antigravity IDE 後，右下角的 Windows 系統匣應該就會出現藍色的 AGY 小圖示。按右上角的 `✕` 只是把它收進系統匣繼續背景記錄，對著圖示點右鍵就可以再次喚醒它。