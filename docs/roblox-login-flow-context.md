# Context: flow `roblox.login` (đăng nhập Roblox + captcha)

> Ghi cho người/agent tiếp theo hiểu **trạng thái thật** của flow đăng nhập chính,
> dựa trên test chạy thật (không đoán). Chỉ tập trung vào flow `roblox.login`
> trong flow-core (`src/app`), không nói về node_app/SaaS.

Cập nhật: 2026-09-07.

---

## 1. Flow là gì, chạy ra sao

Service `roblox.login` = 1 chuỗi Step ráp thành Flow. Thứ tự step = thứ tự chạy,
khai báo ở [src/app/services/roblox/login.py](../src/app/services/roblox/login.py):

```
OpenLoginPageStep      # mở /login, nếu đã có cookie session -> already_logged_in
FillCredentialsStep    # điền username + password
SubmitLoginStep        # bấm Log In
SolveCaptchaStep       # optional: chỉ chạy nếu thấy iframe Arkose (<=5s)
Handle2FAStep          # optional: chỉ chạy nếu bật 2FA
DetectLoginResultStep  # phán kết quả: có cookie .ROBLOSECURITY = success
```

Composition root: [src/app/automation/runner.py](../src/app/automation/runner.py)
`run_service(service_id, credential, *, solver, headless, ...)`.
Nó dựng browser (botasaurus) + solver + context, chạy service, rồi
**đóng browser ở `finally`** (điểm này gây khó khi test — xem §6).

### Cách test 1 flow (user/pass, KHÔNG dùng cookie)

Test account để **đăng nhập** chỉ cần `username` + `password`. Cookie trong file
data là kết quả/tham chiếu, flow login không dùng để restore session.

```bash
# CLI trực tiếp (flow-core), không cần DB/API:
.venv/bin/rlx run roblox.login -u USER -p PASS --no-headless
CAPTCHA_PROVIDER=manual .venv/bin/rlx run roblox.login -u USER -p PASS --no-headless   # solver tay

# Gọi hàm trực tiếp:
.venv/bin/python -c "
from app.automation.runner import run_service
from app.domain.models import Credential
r = run_service('roblox.login', Credential(username='USER', password='PASS'), headless=False)
print(r.success, r.error_code, r.error_message)
"
```

Solver captcha lấy từ `CAPTCHA_PROVIDER` (.env) hoặc truyền `--solver`. Node config
(`~/.roblox-node/config.json`) đang set `yescaptcha` + key thật (balance ~22k khi test).

---

## 2. Dữ liệu account: format & bẫy parse

File test: `.data/captcha_lock_cookies.txt` — mỗi dòng `user:pass:cookie`.

**Bẫy:** cookie `.ROBLOSECURITY` **chứa dấu `:`** (`_|WARNING:-DO-NOT-SHARE-...`),
nên `str.split(':')` sẽ vỡ. Phải tách **đúng 2 dấu `:` đầu**:

```python
user, pw, cookie = line.rstrip("\n").split(":", 2)
```

⚠️ `Credential.parse()` mặc định split mọi `:` → phần `_|WARNING` của cookie bị nhét
vào `totp_secret`, kích hoạt nhầm bước 2FA. **Đừng** đút file này thẳng vào
`rlx run --file`; parse riêng lấy user/pass rồi mới tạo `Credential`.

---

## 3. Kết quả test thật (2026-09-07)

Chạy `roblox.login` real (headful, solver yescaptcha) trên vài account đầu file:

| Acc | Kết quả | Trạng thái thật (screenshot) |
|-----|---------|------------------------------|
| `x99oyvfwf5gcmwhf6q24` | flow báo `success`, cookie=yes | **False positive**: login OK nhưng bị redirect `/not-approved` → modal **"Account locked"** (scenario 2) |
| `sp8t6mt27cmn5183u1yn` | fail | Sau submit Roblox bật **Arkose "Verifying browser..."** (scenario 1) |
| `bxz7t5lqm1gszq8x1wv7` | fail | Như trên — Arkose ở login |

Kết luận: **có 2 chỗ chặn bằng Arkose FunCaptcha**, cả hai flow hiện chưa vượt được.

---

## 4. Hai scenario Arkose (điểm cốt lõi)

### Scenario 1 — Arkose ngay ở màn login
- Sau khi điền + bấm Log In, một số account bị Roblox bật modal **"Verifying
  browser…"** (Arkose enforcement) rồi mới tới FunCaptcha thật.
- Public key Roblox dùng (cần xác nhận lại theo thời điểm):
  `FUNCAPTCHA_PUBLIC_KEY = 476068BF-9607-4799-B53D-966BE98E2B81`,
  subdomain `roblox-api.arkoselabs.com` — ở
  [constants.py](../src/app/services/roblox/constants.py).

### Scenario 2 — "Account locked" hậu đăng nhập
- Account login **thành công** (`.ROBLOSECURITY` được set, navbar hiện username),
  nhưng bị redirect **`https://www.roblox.com/not-approved`**.
- Modal: **"Account locked — We've detected suspicious activity on this account.
  You can unlock your account by confirming that you're a human."**
- 2 nút: **"Sign out"** (xám) và **"Continue"** (xanh) — nút Continue là
  `button.foundation-web-button` (class design-system của Roblox; nên click theo
  **text "Continue"** cho chắc, vd `click_element_containing_text` của botasaurus).
- Bấm **Continue** → mở tiếp **Arkose FunCaptcha** để "confirm human" → giải xong
  mới mở khoá.

> Đây khớp memory cũ: "Arkose ở cả login lẫn màn Account locked hậu đăng nhập".

---

## 5. Trạng thái từng phần code (đâu chạy, đâu còn TODO)

| Phần | File | Trạng thái |
|------|------|-----------|
| Selector login (`#login-username/#login-password/#login-button`) | [constants.py](../src/app/services/roblox/constants.py) | ✅ Đúng, form điền + submit được |
| `FillCredentialsStep` | [steps/fill_credentials.py](../src/app/services/roblox/steps/fill_credentials.py) | ✅ Chạy được **sau khi fix** `type()` (xem §5.1) |
| `SolveCaptchaStep` | [steps/solve_captcha.py](../src/app/services/roblox/steps/solve_captcha.py) | ⚠️ **TODO thật**: `_extract_blob` trả `None`, `_inject_token` chỉ `return True` (placeholder). Chưa lấy blob, chưa inject token → **chưa giải được Arkose**. `should_run` chỉ chờ iframe **5s** (quá ngắn: "Verifying browser..." load lâu hơn) |
| `DetectLoginResultStep` | [steps/detect_result.py](../src/app/services/roblox/steps/detect_result.py) | ⚠️ Chỉ dựa `.ROBLOSECURITY` có mặt = success → **false-positive** với `/not-approved`. Đọc kết quả **quá sớm** (ngay sau submit, trang còn spinner). Có phân loại `AccountLocked` bằng text lỗi nhưng **không** click Continue |
| Xử lý modal "Account locked" (`/not-approved` → Continue) | — | ❌ **Chưa có step nào**. Cần viết mới |
| Handle 2FA | [steps/handle_2fa.py](../src/app/services/roblox/steps/handle_2fa.py) | Khung, optional |

### 5.1. Đã fix trong lần này (chưa commit)
`BotasaurusSession.type()` trong
[src/app/providers/browser/botasaurus_driver.py](../src/app/providers/browser/botasaurus_driver.py):
- Trước: gọi `el.type()` (Element **không có** method `type` → `AttributeError` →
  fallback `driver.type`), **không verify**. Với input React của Roblox, giá trị bị
  "nuốt" khi trang chưa hydrate → form rỗng → submit ra **"Username and password
  required"**.
- Sau: `focus` + `clear_input` + `send_keys` (key event thật), rồi **verify value
  qua JS**; nếu vẫn rỗng → fallback set value bằng native setter + dispatch
  `input`/`change` (React mới nhận); vẫn rỗng → raise `BrowserError` (không submit
  form rỗng). Kết quả: `open_login` 120s→~10s, form điền đúng.

---

## 6. Vấn đề "log xong đóng browser luôn"

`run_service()` bọc session trong context manager, `finally` luôn `close()` →
chạy xong đóng ngay, **không quan sát được** captcha/modal.

Workaround khi test/điều tra: script giữ browser mở + dump DOM
(`scratchpad/observe.py` trong session này — dùng `build_browser(headless=False)`,
tự goto/fill/submit rồi loop `run_js` tìm modal, **không** đóng). Chính nó chụp
được modal "Account locked" và tìm ra nút Continue. Nếu cần lâu dài: thêm cờ
`--no-close`/keep-open cho chế độ test.

Ảnh chụp bằng chứng (session này): `data/screenshots/observe/*.png`,
`data/screenshots/t2/login_failed.png` (Arkose "Verifying browser…"),
`data/screenshots/t3/login_failed.png`.

---

## 7. Việc cần làm tiếp (đề xuất, theo độ ưu tiên)

1. **Step "Account locked" (scenario 2)** — dễ & giá trị cao:
   - Detect: `current_url()` chứa `/not-approved` **hoặc** thấy modal "Account
     locked".
   - Click **Continue** (theo text) → chuyển sang Arkose.
   - Sửa `DetectLoginResultStep`: `.ROBLOSECURITY` + `/not-approved` ⇒ **LOCKED**,
     KHÔNG phải success. Xác nhận success thật bằng gọi
     `API_AUTHENTICATED = https://users.roblox.com/v1/users/authenticated` (đã khai
     trong constants nhưng chưa dùng).
   - Cho `DetectLoginResultStep` **chờ** trạng thái cuối (cookie / error / arkose /
     2FA) thay vì đọc ngay.

2. **Arkose engine (scenario 1 & 2)** — phần nặng nhất, là blocker để có success:
   - `_extract_blob`: đọc `dataExchangeBlob` thật từ enforcement Arkose (thường qua
     biến JS/global hoặc sự kiện). Provider yescaptcha nhận blob qua field `data`
     (xem [yescaptcha.py](../src/app/providers/captcha/yescaptcha.py)).
   - `_inject_token`: inject token đã giải vào callback Arkose (`arkose.setup` /
     iframe callback) để Roblox chấp nhận.
   - `should_run`: chờ iframe > 5s; áp dụng cả ở màn `/not-approved`.

3. **Chế độ test giữ browser mở** — thêm cờ để chạy 1 acc user/pass, không đóng,
   phục vụ quan sát/điều tra runtime Arkose.

---

## 8. Lệnh nhanh

```bash
# chạy 1 flow
.venv/bin/rlx run roblox.login -u USER -p PASS --no-headless
# balance captcha (yescaptcha đọc từ node config)
.venv/bin/python -c "from app.providers.captcha import build_solver; s=build_solver('yescaptcha'); print(s.balance())"
# lint file đã sửa
.venv/bin/ruff check src/app/providers/browser/botasaurus_driver.py
```
