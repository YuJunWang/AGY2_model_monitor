# AGY Fuel Gauge 🚀

**Simplicity is the ultimate sophistication.** While most telemetry tools bombard you with complex dashboards, bloated graphs, and endless configuration files, AGY Fuel Gauge does exactly one thing perfectly: it keeps your AI quotas visible without pulling you out of your flow state.

A minimalist, zero-config widget that just works.

The trick is surprisingly simple: Antigravity already runs a local background daemon (`language_server.exe`) that handles all your token traffic. We eavesdrop on it. This widget hooks directly into that internal gRPC-Web API, giving you an accurate, real-time view of your Gemini and External model usage—no credentials required, no bloated UI, no config files to maintain.

<p align="center">
  <img src="./assets/widget_v5_5h.png" alt="Vertical Fuel Gauge 5H View" />
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="./assets/widget_v5_wk.png" alt="Vertical Fuel Gauge Weekly View" />
</p>

## ✨ How it actually works

- **Zero Auth Setup**: The widget scans for your active `language_server.exe` process to dynamically locate its listening port, then reads the `x-codeium-csrf-token` straight from the startup logs. Nothing to configure.
- **Cyber-Stick UI**: An irregular L-shaped floating glass interface with vertical fluid gauges designed for OLED black backgrounds. Uses native Windows GDI region APIs (`SetWindowRgn`) for a frameless, perfectly rounded asymmetrical shape.
- **Pixel-Perfect Equalizer Chart**: The history chart is rendered as a pixel-perfect, zero-gap equalizer. Each data row is perfectly mapped to exactly 1 pixel, capturing 3-minute increments with absolute precision.
- **Overdrive Gradient System**: The history equalizer features a dynamic RGB color interpolation engine. Gemini (Green → Yellow) and External (Orange → Red) colors shift smoothly based on usage intensity. If consumption exceeds the physical scale (5.0%), the row engages "Overdrive mode"—glowing with intense, overexposed neon highlights.
- **Micro-Animations**: A subtle green scanline sweeps across the data panel during background syncs, confirming telemetry without breaking your flow.

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

**把「極簡」發揮到極致。** 當現今大多數的監控工具都在向你轟炸複雜的數據看板、臃腫的圖表與無止盡的設定檔時，AGY Fuel Gauge 只專注於把一件事情做到完美：讓你能隨時瞥見 AI 剩餘額度，卻絕不打斷你的心流。

這是一款主打零設定、沒有多餘視覺負擔的極簡小工具。

做法其實很直觀：既然 Antigravity 已經在你的電腦裡跑了一支負責通訊的背景精靈（`language_server.exe`），我們直接在它的內部通道（gRPC-Web）上「旁聽」就好。不需要帳號憑證，不需要臃腫的介面，更不需要維護任何設定檔，安裝好就能在背景安靜地回報即時用量。

## ✨ 它是怎麼運作的？

- **自動找 Port 與 Token**：程式會找到 `language_server.exe` 的進程來定位目前監聽的 Port，並從啟動日誌直接取出 `x-codeium-csrf-token`。你什麼都不用設定。
- **Cyber-Stick 賽博龐克介面**：採用不規則 L 型的懸浮玻璃面板與垂直能量條設計。底層呼叫 Windows 原生 GDI Region API，實現無邊框且具有完美不對稱圓角的幾何外觀。
- **像素級無縫等化器 (Pixel-Perfect Equalizer)**：下方的歷史消耗圖表採用了像素級渲染引擎。每 3 分鐘一筆的資料被精準映射到絕對的 1 像素高度，徹底消除了任何 Sub-pixel 渲染導致的粗細不一，呈現出完美均勻且連續的等化器視覺。
- **過載發光漸層 (Overdrive Gradient)**：等化器內建動態 RGB 色彩內插引擎，Gemini 側從底部「賽博綠」漸變至頂峰「警告黃」，EXT 側則由「活力橘」漸變至「玫瑰紅」。當單次消耗突破物理刻度上限（5.0%）時，整排等化器會瞬間切換成「過載發光模式」，注入高亮度白光營造霓虹燈過載般的視覺衝擊。
- **掃描線微動畫**：每當背景成功抓取新資料時，圖表區會低調地掃過一條微光掃描線，提供「系統正在運作」的明確動態回饋，同時絕不干擾你的寫程式心流。

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