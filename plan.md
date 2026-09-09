# Plan — roblox-automation SaaS

> File plan sống. Cập nhật 2026-09-09.
> Backend **API-first**. FE là **repo Next.js riêng** (chủ dự án tự build) — backend chỉ
> cung cấp API + docs. Docs API: [`docs/api.md`](docs/api.md). Deploy: mục "Deploy" bên dưới.

---

## Trạng thái tổng

| Mảng | Trạng thái |
|------|-----------|
| SaaS core (auth/order/pool/billing/point) | ✅ DONE |
| Flow `roblox.login` (captcha + locked + 2FA + phân loại lỗi) | ✅ chạy được (extension YesCaptcha + CfT 152) |
| Pool phân tán (claim atomic, retry, TTL reclaim, heartbeat, poison cap) | ✅ DONE + đã test |
| Node standalone app (UI config, proxy rotate, grid, remote log) | ✅ DONE |
| SaaS API layer (dashboard, notification, CMS, nạp crypto) | ✅ DONE + đã test |
| Giao tiếp node↔pool (totp, heartbeat, report retry, poison cap) | ✅ DONE (2026-09-09) |
| Deploy Docker prod (BE + Postgres) | ✅ file sẵn, **chưa build/chạy thật trên VPS** |
| FE Next.js | ⬜ chủ dự án tự build (repo riêng) |
| Cancel order (CANCELLED) | ⏳ **CẦN CONFIRM** (xem cuối) |
| Refund điểm khi fail | ⏳ **CẦN CONFIRM** (xem cuối) |
| Mã hoá credential at-rest | ⬜ chưa làm |
| Test NOWPayments thật | ⬜ chờ có API key |

---

## ✅ SaaS API layer (dashboard / notification / CMS / crypto)

Đã test end-to-end bằng TestClient. Chi tiết endpoint xem [`docs/api.md`](docs/api.md).

- **Dashboard**: `GET /dashboard` (balance, order/record theo status, chi tiêu, success
  rate, unread, gần đây) · `GET /dashboard/admin` (toàn hệ thống).
- **Orders + records/đơn**: `GET /orders/{id}/records` (kèm cookie, chỉ chủ đơn) ·
  `GET /orders/{id}/export` (text `user:cookie` = sản phẩm khách mua).
- **Notification**: `Notification` (user_id NULL = broadcast) + `NotificationRead` (đọc
  theo từng user). List/unread-count/read/read-all. Tự bắn: tạo đơn, đơn về terminal, nạp
  thành công. Admin broadcast `POST /admin/notifications`.
- **CMS banner/modal/announcement**: `CmsContent` + `CmsDismissal`. Public `GET /cms/active`
  (có token → lọc dismiss) · `POST /cms/{id}/dismiss` · admin CRUD `/admin/cms`.
- **Hạ tầng**: CORS (`APP_CORS_ORIGINS`); `POST /auth/api-keys` **chỉ admin** (key nội bộ
  cho node claim pool).

### Nạp điểm tự động qua crypto
- **Port `CryptoPaymentProvider`** (swap bằng `CRYPTO_PROVIDER`): `manual` (mặc định, admin
  confirm tay) · `nowpayments` (HTTP thật + xác thực IPN HMAC-SHA512).
- **Giá tính theo USD/point**: `CRYPTO_USD_PER_POINT` (mặc định 0.03 = $0.03/point),
  `CRYPTO_MIN_USD` (nạp tối thiểu theo $). `usd = amount_points * usd_per_point`.
- `CRYPTO_CURRENCIES` **optional** — để trống thì NOWPayments là nguồn sự thật (chỉ điền
  nếu muốn ép tập con coin).
- Flow: `POST /billing/deposits` → địa chỉ/invoice → user trả → webhook
  `POST /billing/deposits/webhook` (**idempotent**, verify chữ ký) → cộng điểm + notification.
  `POST /admin/deposits/{id}/confirm` confirm tay. `GET /billing/crypto-config` cho FE.
- ⚠️ **Callback IPN đã wire sẵn** (endpoint cố định + tự đính `ipn_callback_url` mỗi payment).
  Mai sau chỉ điền `CRYPTO_API_KEY` / `CRYPTO_IPN_SECRET` / `CRYPTO_CALLBACK_BASE` (URL public)
  + bật IPN bên NOWPayments. **Chưa test với payload thật** — chữ ký IPN dựng lại JSON
  sort-key bằng `json.dumps`; nếu NOWPayments format số/khoảng trắng lệch thì verify fail →
  lúc có tài khoản gửi 1 IPN test để chỉnh `parse_webhook` nếu cần.

---

## ✅ Flow `roblox.login` (hướng extension)

- Login **viewport PC** → tới `/not-approved` thì **giả lập phone** (CDP device metrics +
  window khớp) → refresh → Continue → giải captcha.
- Arkose FunCaptcha giải bằng **extension YesCaptcha** trong **Chrome for Testing 152**
  (Chrome 151 stable chặn `--load-extension`). API 2captcha/yescaptcha KHÔNG giải được → pivot extension.
- Xử lý `/not-approved` (state machine), QR "cần app" → `need_mobile_app`, app-promo về `/`
  = success. Phân loại lỗi terminal vs hạ tầng.
- Proxy rotation (4 format, test-live-trước, đổi mỗi N browser) qua MV3 proxy-auth extension.

### Proxy chậm → timeout sớm: đã fix (2026-09-09)
- `wait_for` **loading-aware**: PAUSE đồng hồ timeout khi `document.readyState != 'complete'`
  (chỉ đếm khi trang đã tải xong) → trang tải nhanh y hệt cũ, chỉ khi proxy làm tải lâu thì
  thời gian tải không tính vào timeout. Có **trần cứng** `max(timeout×4, timeout+60)` chống treo.
- Có proxy → `get()` trả về ngay ở DOM `interactive` (`wait_for_complete_page_load=False`),
  không chờ hết ảnh/font. (Đã bỏ hướng block resource theo yêu cầu — không đụng captcha.)

---

## ✅ Pool phân tán + Node app

- Claim atomic dialect-aware: Postgres `FOR UPDATE SKIP LOCKED`; SQLite UPDATE tuần tự + WAL
  + busy_timeout. Test 30 thread × 2 → 30 unique, 0 trùng.
- Node standalone: FastAPI UI (pool_url/token, proxies, rotate, captcha key), NodeAgent
  claim–run–report + RAM gate + SlotAllocator grid; remote log; đóng gói PyInstaller.

### Giao tiếp node↔pool — đã củng cố (2026-09-09)
- **Cookie**: flow bắt `.ROBLOSECURITY` qua CDP (đọc cả httpOnly) → `ctx.session` → runner
  → `result.data.session` → report → `record.cookies`. Verify export OK. ✓
- **totp/email**: SaaS claim trả `totp_secret`+`email`; node `Record`/`Credential` giờ giữ →
  **acc 2FA login được** (trước bị drop → luôn `two_factor_required`).
- **Heartbeat/lease**: `POST /pool/heartbeat` + `PoolService.extend_lease` (chỉ gia hạn nếu
  còn `running` & đúng node; trả `ok=false` nếu mất lease). Node heartbeat mỗi **60s** cho mọi
  record đang chạy; claim gửi `lease_ttl=240s` → node sống không bị cướp, node chết reclaim sau 240s.
- **Report retry**: `RemotePool.report` thử 3 lần backoff (cookie không mất vì lỗi mạng
  thoáng qua; cũng luôn lưu local `results.jsonl`).
- **Poison cap**: `HARD_MAX_ATTEMPTS=5` + reap trong `claim_next` → record bị reclaim >5 lần
  (node chết liên tục, không report) → `failed('exhausted')` + sync order → không loop vô hạn.

### Vòng đời status record (đã xử lý đủ)
| Tình huống | Status |
|---|---|
| Tạo order | `queued` |
| Node claim | `running` (+lease, attempt+1) |
| Thành công | `success` + cookie |
| Fail **login** (sai pass/khóa/cần app/2FA) | `failed` (terminal) |
| Fail **ngoài login** (proxy/captcha/browser/mạng/exception), còn lượt | `queued` (retry 1 lần) |
| Fail ngoài login, hết lượt | `failed` |
| Node chết (hết TTL, không report) | reclaim → `running` |
| Node chết liên tục (reclaim >5) | `failed` (`exhausted`) |

`PENDING` (enum) không dùng — record vào thẳng `queued`. `CANCELLED` chưa có đường tới (xem CẦN CONFIRM).

---

## Deploy (BE + Pool lên VPS)

- Mô hình **pull**: node là máy ngoài, KHÔNG chạy ở server → image API **không cần chromium**.
- File: [`docker/Dockerfile.api`](docker/Dockerfile.api) (lean, `rlx initdb` + uvicorn workers),
  [`docker/docker-compose.prod.yml`](docker/docker-compose.prod.yml) (chỉ `api` + `db` Postgres,
  healthcheck, no redis/worker), [`.dockerignore`](.dockerignore), [`.env.prod.example`](.env.prod.example).
- Đã xóa docker cũ Phase-1 (Dockerfile + docker-compose.yml có worker/redis/chromium — không dùng).
- **Tạo bảng prod**: `rlx initdb` (idempotent) — vì `init_db()` chỉ auto khi không phải prod,
  chưa có alembic. Đã test tạo đủ 11 bảng.
- **Chạy TỪ REPO ROOT** (để compose đọc root `.env` cho `${POSTGRES_*}`):
  `docker compose -f docker/docker-compose.prod.yml up -d --build`.
- Node cắm pool: `pool_url = https://<vps>` + `pool_token = API key của ADMIN` (claim/report
  là admin-only).
- ⚠️ **Chưa build/chạy thật trên VPS** (máy dev không có Docker — mới validate YAML/logic/compile).

---

## 🔧 Nợ kỹ thuật / chưa làm

- **Mã hoá credential at-rest**: `records.username/password` đang plaintext (có TODO trong model).
- **Test NOWPayments thật**: cần API key + callback URL public; hiện mới test chữ ký IPN offline.
- **Build/run Docker prod thật** trên VPS (mới validate tĩnh).
- **service_id từ claim**: node hardcode `"roblox.login"` (bỏ qua `service_id` claim trả về) —
  ok vì hiện 1 service; cần sửa khi chạy đa service.
- **NOWPayments live currencies**: option thêm `GET /billing/crypto-currencies` proxy
  `/v1/merchant/coins` để FE lấy list coin đang bật (thay vì gõ tay `CRYPTO_CURRENCIES`).
- **pyotp** chưa vào `pyproject` (2FA có fallback tự tính TOTP RFC 6238 nên vẫn chạy).
- Metrics per-node, ưu tiên claim theo success-rate, dashboard đàn node — để sau.
- ✅ Đã trả nợ: `email-validator` đã thêm vào `pyproject` (trước chỉ cài tay trong venv).

---

## ⏳ CẦN CONFIRM (chờ chủ dự án quyết)

**A. Hủy order (`CANCELLED`).** Có làm endpoint hủy order không? Nếu có:
- Ai được hủy: khách tự hủy đơn của mình, hay chỉ admin?
- Semantics đề xuất: đánh record `queued` → `cancelled` (node ngừng claim); record `running`
  đang chạy thì để chạy nốt. Có hoàn điểm phần bị hủy không (liên quan B)?

**B. Hoàn điểm khi fail.** Hiện trừ điểm lúc tạo order, fail KHÔNG hoàn. Muốn hoàn loại nào?
- Chỉ hoàn khi fail **hạ tầng / `exhausted`** (lỗi hệ thống)?
- Có hoàn khi fail **login** (sai pass/khóa) không? — thường KHÔNG (account tự lỗi).
- Cơ chế sẵn có: `BillingService.refund(user, amount, ref_type='order', ref_id=...)`; hook ở
  `pool/report` khi record → `failed` (phân loại qua `error_code`).

**C. NOWPayments**: sẽ dùng provider `nowpayments`. Khi có tài khoản → điền env + gửi 1 IPN
test để chốt `parse_webhook`.

---

Design doc node fleet: artifact "Node Fleet Architecture".
