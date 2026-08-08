# AGY Fuel Gauge 🚀

Honestly, looking at most telemetry dashboards just gives me anxiety. They shove massive graphs and endless configuration files in your face when all you really want is a tiny indicator that shuts up and stays out of your way. I built this because I just needed to know my remaining AI quota without breaking my flow state. It doesn't even ask for your credentials. We took the most brute-force route possible: it literally eavesdrops on the local daemon's traffic happening right on your machine. You don't configure it, you just run it and it works.

<p align="center">
  <img src="./assets/widget_v5_5h.png" alt="Vertical Fuel Gauge 5H View" />
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="./assets/widget_v5_wk.png" alt="Vertical Fuel Gauge Weekly View" />
</p>

## Tech Specs
1. **Zero Auth API Hook**: Extracts port and `x-codeium-csrf-token` from `language_server.exe` logs. Hooks internal gRPC-Web directly.
2. **GDI Frameless UI**: Windows `SetWindowRgn` for an L-shaped window. Pure black canvas.
3. **Pixel-Perfect Chart**: 1 pixel equals 3 minutes. Zero gaps.
4. **Dynamic RGB**: 3-keyframe gradient (GEM: Green→Yellow→Red; EXT: Orange→Purple→Blue). Triggers `deepen_rgb` overdrive at 5.0%.
5. **Canvas Toggle**: Custom smooth sliding switch for 5H/WK views.
6. **Async Telemetry**: Background polling. Visualized by a random-jittered scanline animation.

## Compatibility
- **Antigravity 2.0 Desktop**: Supported (via Sidecar).
- **Antigravity IDE**: Supported.
- **Antigravity CLI**: Not supported.

## Installation

1. **Clone Repo**
   ```bash
   git clone https://github.com/YuJunWang/AGY_Fuel_Gauge.git
   cd AGY_Fuel_Gauge
   ```

2. **Install Deps**
   ```bash
   pip install pystray Pillow
   ```

3. **Configure Sidecar**
   Create `C:\Users\<Username>\.gemini\config\sidecars\agy-fuel-gauge\sidecar.json`:
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

Restart Antigravity IDE. Gauge icon loads in system tray. Right-click to wake, hit `✕` to hide.

---

# AGY Fuel Gauge（中文說明）🚀

其實市面上一堆監控工具看了就覺得煩，動不動就要搞一堆複雜儀表板跟設定檔，光是看著就讓我焦慮。我只想要一個東西：不要擋路、不要吵我，安安靜靜在角落告訴我 AI 額度到底還剩多少就好。所以這個小工具根本不跟你要帳號密碼，我們直接用最暴力的解法——直接攔截你電腦裡那支負責通訊的背景精靈流量。你連設定都不用設定，裝上去它自己就會搞定。

## 核心技術
1. **API 自動掛載**：動態抓取 `language_server.exe` 的 port。從日誌挖出 token，直連內部 gRPC-Web。
2. **GDI 無邊框渲染**：呼叫 Windows `SetWindowRgn`。做出不規則 L 型純黑視窗。
3. **像素級等化器**：每 3 分鐘數據剛好對應 1 像素高。完全零間距。
4. **動態 RGB 插值**：三節點漸層（GEM：綠黃紅；EXT：橘紫藍）。用量破 5.0% 自動觸發 `deepen_rgb` 過載變色。
5. **平滑滑動開關**：自定義 Canvas 繪製 5H / WK 切換鈕。視覺與資訊完美分離。
6. **非同步資料同步**：背景抓數據。成功抓取時會觸發帶有隨機雜訊（Jitter）的折線微動畫。

## 支援環境
- **Antigravity 2.0（桌面版）**：支援。走 Sidecar 機制。
- **Antigravity IDE**：支援。
- **Antigravity CLI**：不支援。沒有背景精靈可以聽。

## 安裝步驟

1. **下載專案**
   ```bash
   git clone https://github.com/YuJunWang/AGY_Fuel_Gauge.git
   cd AGY_Fuel_Gauge
   ```

2. **安裝套件**
   ```bash
   pip install pystray Pillow
   ```

3. **掛載背景執行（推薦）**
   在 `C:\Users\<帳號>\.gemini\config\sidecars\` 建立 `agy-fuel-gauge` 資料夾。新增 `sidecar.json`：
   ```json
   {
     "description": "AGY Fuel Gauge",
     "command": "pythonw",
     "args": [
       "E:\\你的路徑\\AGY_Fuel_Gauge\\widget.py"
     ],
     "restart_policy": "always"
   }
   ```

重啟 Antigravity IDE。右下角系統匣會出現圖示。點 `✕` 縮小到背景，對圖示點右鍵可重新喚醒。