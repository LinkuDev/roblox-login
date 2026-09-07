# Plan — roblox-automation

> File plan sống. Ưu tiên hiện tại: **build cho xong flow `roblox.login`**.
> Phần SaaS phân tán (node fleet) đã chốt kiến trúc nhưng **hoãn** — xem cuối file.

---

## Trạng thái

- ✅ **Phase 1 — SaaS order/pool/billing/seam** (DONE)
- 🔨 **Flow `roblox.login`** — ĐANG LÀM, phần lớn nhất của standalone app
- ⏸️ **SaaS phân tán (Node Fleet)** — HOÃN, kiến trúc đã chốt (pool–pull), làm sau khi flow xong

---

## ✅ Phase 1 — đã xong

- Order tạo từ payload text `user:pass` (mỗi dòng 1 account) + **validate** (`modules/orders/accounts.py`), dòng sai → báo kèm số dòng, reject cả order.
- `POST /api/v1/orders/validate` — dry-run cho form: trả `valid/invalid count`, `total_price`, `errors[]`. Không tạo, không trừ.
- **Trừ điểm trước** lúc tạo order = `N × price`; thiếu số dư → `InsufficientPoints` (402), rollback sạch. Fail **chưa hoàn** điểm (refund làm sau).
- 1 record = 1 dòng: gộp `OrderItem`+`Job` → bảng `records` (`username, password, totp, email, status, attempt, cookies, reason, error_code, result_json`; sẵn `node_id`, `claim_expires_at` cho Phase 2).
- Tách seam `claim_input / run_service / report_result` (`modules/jobs/pool.py`); **billing rời khỏi node/report**.
- `runner.py` wire cookie từ `ctx.session` → `RunResult.data["session"]` để report lưu được.
- Tests: 20 passed. Ruff sạch (chỉ còn `B008` idiom FastAPI, sẵn toàn repo).

---

## 🔨 Ưu tiên hiện tại: FLOW `roblox.login`

**Mục tiêu:** login thật → lấy cookie `.ROBLOSECURITY`, xử lý **Arkose FunCaptcha** + 2FA, phân loại lỗi rõ ràng.

### Cơ chế thật của Roblox (phải build đúng cái này, không phải iframe thuần)
- Login là XHR `POST https://auth.roblox.com/v2/login` (kèm `x-csrf-token`), **không** phải submit form thường.
- Khi cần captcha, server trả **403** kèm header/response challenge:
  `rblx-challenge-id`, `rblx-challenge-type` (= `captcha`), `rblx-challenge-metadata`
  (base64 JSON chứa `dataExchangeBlob`, `unifiedCaptchaId`).
- Client giải Arkose FunCaptcha (publicKey Roblox + `blob = dataExchangeBlob`) → nhận `token`.
- **Gửi lại** login kèm challenge headers + `rblx-challenge-metadata` mới
  (base64 chứa `unifiedCaptchaId` + `captchaToken`) để pass.
- 2FA: nếu bật → trả ticket 2SV, nhập TOTP (`handle_2fa` đã có, cần chốt selector/endpoint thật).

### Việc cụ thể (điền các `TODO(flow)`)
1. **Quan sát flow thật** bằng creds nháp: chạy login → bắt `POST /v2/login` 403 + đọc `rblx-challenge-*` + metadata. (Browser đã mở được ở desktop; creds sai vẫn kích được challenge.)
2. `_extract_blob`: đọc `dataExchangeBlob` từ challenge metadata thật (bỏ `window.__ARKOSE_BLOB__` giả).
3. `_inject_token` → đổi thành **submit lại login kèm challenge headers** (đúng cơ chế Roblox), bỏ placeholder `return True`.
4. Chốt selector `SEL_CAPTCHA_FRAME` / `SEL_2FA_*` thật (username/password/login-button đã xác nhận khớp DOM).
5. `detect_result`: phân loại lỗi theo response/errorCode thật (sai pass / khoá / rate-limit / captcha fail).
6. Test bằng solver `manual` (miễn phí) trước → rồi 2captcha/capsolver.

### Cần chốt với chủ dự án
- **Có account nháp** để quan sát challenge thật không? (hoặc build theo cơ chế đã biết, verify sau khi có account)
- **Target kết quả:** chỉ cần cookie `.ROBLOSECURITY`, hay cả profile/robux/user info?
- **DOM-driven hay API-driven?** Roblox thực chất API-driven; nên nghiêng hướng bắt/điều khiển XHR thay vì click iframe.

---

## ⏸️ HOÃN: SaaS phân tán (Node Fleet) — làm sau khi flow xong

Kiến trúc đã chốt (**pool–pull**, node internal cắm thẳng Postgres). Ghi lại để không quên:

- **Phase 2** — Pool API `claim_next()` / `report()` sau port `PoolLink` + adapter WSS; `NodeAgent` vòng lặp claim–run–report; node remote đầu tiên connect thật. Worker local giữ làm fallback.
- **Phase 3** — claim atomic `SELECT … FOR UPDATE SKIP LOCKED`; reclaim theo `claim_expires_at` TTL + `extend`; pacing/sticky. **Fail nghiệp vụ = terminal**, **fail hạ tầng = requeue**. Dùng `LISTEN/NOTIFY` báo thức node + đánh thức settlement (nếu cần).
- **Fan-out** — node tự đo RAM/CPU, còn dư thì claim tiếp ("càng ham càng tốt") nhưng **claim-JIT** (không claim-ahead), có **trần cứng + margin** để không OOM/thrash.
- **Phase 4** — đóng gói app node standalone: mở lên auto-connect tới SaaS, form config (token, URL, max_slots, nguồn proxy). Scale = mở thêm app.
- **Phase 5** — metrics per-node, dashboard đàn node, ưu tiên claim theo success-rate, mã hoá credential at-rest.
- **Refund** — hoàn điểm khi record fail: chưa làm, build từ order sau.
- Ghi chú: bảng `records` đã có sẵn `node_id`, `claim_expires_at` cho Phase 2–3.

Design doc chi tiết (3 sơ đồ + protocol): artifact "Node Fleet Architecture".

---

## Nợ kỹ thuật / ghi chú
- `email-validator` chưa nằm trong `pyproject` nhưng `schemas/auth` dùng `EmailStr` → cần thêm vào deps (đã cài tay trong venv để chạy).
- `pyotp` optional cho 2FA — chưa có trong deps; `handle_2fa` có fallback tự tính TOTP (RFC 6238) nên vẫn chạy.
- Đã sửa bug `window_size` (string → tuple) trong `providers/browser/botasaurus_driver.py`.
