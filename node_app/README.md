# roblox-node — app standalone

App **riêng**, chạy trên từng máy vật lý (node). Không phải backend SaaS.

- Lõi Python (flow chạy trên botasaurus). UI là 1 trang web local, render trong
  cửa sổ Chrome (`--app`) — kiểu Electron thu nhỏ, thuần Python.
- Đóng gói bằng PyInstaller thành 1 file chạy độc lập.

## Chạy dev
```bash
pip install -e node_app          # cài package roblox-node + script
python -m robloxnode             # hoặc: roblox-node
```
Mở cửa sổ cấu hình. Config lưu ở `~/.roblox-node/config.json`
(đổi bằng env `RLX_NODE_CONFIG`).

## Config (trước mắt)
1. **Pool URL** — connect tới SaaS pool (dùng ở phase sau).
2. **Captcha** — nhà cung cấp (`yescaptcha`) + API key.
3. **RAM điểm tràn (%)** — RAM vượt ngưỡng ⇒ node "đầy", ngừng claim tới khi tụt xuống.

## Sắp tới
- Node agent: vòng lặp `claim → run flow → report` tới SaaS pool.
- Nhúng flow-core (automation/services/providers) — hiện tách khỏi backend SaaS.
