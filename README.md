# AGY Fuel Gauge 🚀

AGY Fuel Gauge is a lightweight background telemetry widget designed exclusively for Antigravity. It monitors your language model quotas (Gemini and External models) in real-time by securely interfacing with active Antigravity sessions via gRPC-Web, eliminating the need for manual browser interactions.

<p align="center">
  <img src="./assets/preview_5h.png" alt="5-Hour Quota View" width="45%" />
  &nbsp;&nbsp;
  <img src="./assets/preview_weekly.png" alt="Weekly Quota View" width="45%" />
</p>

## ✨ Features
- **Real-Time Telemetry**: Fetches precise 5-hour and weekly remaining quotas directly from the Antigravity internal gRPC-Web API.
- **Zero-Configuration Authentication**: Automatically binds to the `language_server.exe` process to discover dynamic network ports, and extracts the necessary `x-codeium-csrf-token` from system logs. This ensures instant and secure data retrieval with zero user setup.
- **Dynamic Arc Gauges**: Features custom-rendered 270-degree progress arcs indicating remaining percentage and calculated reset times, optimized for OLED dark mode.
- **Segmented Control Layout**: Seamlessly toggle between 5-Hour and Weekly usage views without expanding the widget footprint.
- **Usage History & Burn Rate**: Logs local telemetry every 3 minutes to generate a historical waveform chart and calculate current hourly consumption rates (`🔥 %/h`).

> [!NOTE]
> **Understanding Usage Percentages**  
> Gemini and External models possess significantly different total quota baselines. A 1% consumption in Gemini represents a substantially higher token volume than 1% in an External model. To address this visual disparity, the historical usage graph utilizes a **Self-Normalized Mirrored Area Chart**. Both data streams scale independently to their respective local maximums, allowing for clear side-by-side trend analysis.

## 💻 Compatibility
- **Antigravity 2.0 (Desktop App)**: Fully supported (Integrates with Sidecar lifecycle management).
- **Antigravity IDE**: Fully supported.
- **Antigravity CLI (`agy`)**: Not applicable. The CLI environment does not spawn the persistent language server required for background telemetry.

## 🛠️ Installation & Usage

1. **Clone the Repository**
   ```bash
   git clone https://github.com/YuJunWang/AGY_Fuel_Gauge.git
   cd AGY_Fuel_Gauge
   ```

2. **Install Dependencies**
   Requires Python 3.
   ```bash
   pip install pystray Pillow
   ```

3. **Automate with Antigravity Sidecar (Highly Recommended)**
   Deploying the widget as an [Antigravity Sidecar](https://antigravity.google/docs/sidecars) allows it to run as a daemon process. It will launch automatically with your workspace and restart upon failure.
   
   - Navigate to your Antigravity configuration directory (typically `C:\Users\<YourUsername>\.gemini\config\sidecars\`).
   - Create a new directory named `agy-fuel-gauge`.
   - Create a file named `sidecar.json` inside this directory with the following configuration (update the `args` path to match your installation directory):
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
   - **Usage**: Restart your Antigravity IDE. The system will silently initialize the widget, indicated by the AGY icon in the Windows system tray.
   - **Visibility**: Closing the widget via the `✕` button minimizes it to the system tray while background telemetry continues. Right-click the tray icon and select "Show Widget" to restore the interface.

4. **Manual Execution**
   You can also execute the widget manually:
   ```bash
   pythonw widget.py
   ```

---

# AGY Fuel Gauge (中文說明) 🚀

AGY Fuel Gauge 是一個專為 Antigravity 設計的背景監控儀表板。它能即時追蹤您的 AI 模型額度（包含 Gemini 與 External 外部模型），透過直接與 Antigravity 內部的 gRPC-Web 服務對接，提供安全、全自動的數據監測。

## ✨ 核心功能
- **即時遙測**：直接串接 Antigravity 底層 API，獲取精確的 5 小時與週用量剩餘配額。
- **零配置認證**：自動鎖定 `language_server.exe` 進程以取得動態通訊埠，並從系統日誌中提取 `x-codeium-csrf-token`。無須手動設定或網頁攔截，即可達成穩定且即時的數據讀取。
- **動態圓弧儀表**：自定義渲染的高對比 270 度圓弧進度條，具備發光特效，並能精確換算下次配額重置時間。
- **整合式視圖**：透過 Segmented Control 介面，在 5 小時額度與週額度之間快速切換，維持介面簡潔。
- **歷史分析與消耗率**：每 3 分鐘自動進行本地紀錄，於視窗下方繪製雙向面積圖，並即時計算每小時額度消耗速率 (`🔥 %/h`)。

> [!NOTE]
> **關於配額百分比的視覺化說明**  
> Gemini 與非 Gemini (External) 模型的總可用額度基準差異巨大。Gemini 的 1% 消耗量在實際運算中遠高於 External 的 1%。為了解決這項視覺不對稱，歷史圖表採用了**自我正規化的倒影圖 (Mirrored Area Chart)**。雙方數據會根據各自的局部最大值進行獨立縮放，確保兩種模型的使用趨勢皆能清晰呈現，互不干擾。

## 💻 系統相容性
- **Antigravity 2.0 (桌面版應用程式)**：完全支援（支援 Sidecar 自動化生命週期管理）。
- **Antigravity IDE**：完全支援。
- **Antigravity CLI (`agy`)**：不適用。純命令列環境不會啟動常駐的語言伺服器供背景數據抓取。

## 🛠️ 安裝與使用指南

1. **下載專案**
   ```bash
   git clone https://github.com/YuJunWang/AGY_Fuel_Gauge.git
   cd AGY_Fuel_Gauge
   ```

2. **安裝必備套件**
   請確認環境中已安裝 Python 3，並執行：
   ```bash
   pip install pystray Pillow
   ```

3. **配置為 Antigravity Sidecar 自動啟動 (強烈推薦)**
   建議將本工具配置為 [Sidecar (邊車)](https://antigravity.google/docs/sidecars) 服務。配置後，儀表板將隨開發環境自動啟動，並由系統守護進程確保其持續運行 (自動重啟)。
   
   - **設定方式**：前往您的 Antigravity 設定目錄（通常位於 `C:\Users\<您的使用者名稱>\.gemini\config\sidecars\`），建立名為 `agy-fuel-gauge` 的目錄，並在其中建立 `sidecar.json` 檔案（請將 `args` 替換為實際的專案路徑）：
     ```json
     {
       "description": "AGY Fuel Gauge",
       "command": "pythonw",
       "args": [
         "E:\\您的\\路徑\\AGY_Fuel_Gauge\\widget.py"
       ],
       "restart_policy": "always"
     }
     ```
   - **啟動方式**：重新啟動 Antigravity IDE 即可。系統將於背景靜默啟動程式，並在 Windows 系統匣顯示藍色的 AGY 圖示。
   - **視窗管理**：點擊小工具右上角的 `✕` 僅會將視窗隱藏至系統匣，背景記錄功能將持續運作。若需檢視數據，對系統匣圖示點擊右鍵並選擇 `Show Widget` 即可還原視窗。

4. **手動執行**
   若無需 Sidecar 自動化管理，亦可直接手動啟動：
   ```bash
   pythonw widget.py
   ```

