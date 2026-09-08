# Plan — roblox-automation SaaS

> File plan sống. Cập nhật 2026-09-08.
> Backend **API-first** (FE Next.js là **repo riêng**, chủ dự án tự build — backend chỉ
> cung cấp API + docs). Docs API: [`docs/api.md`](docs/api.md).

---

## Trạng thái tổng

| Mảng | Trạng thái |
|------|-----------|
| Phase 1 — SaaS order/pool/billing/seam | ✅ DONE |
| Flow `roblox.login` (captcha + locked + 2FA + phân loại lỗi) | ✅ chạy được (extension YesCaptcha + CfT 152) |
| Pool phân tán (claim atomic, retry, TTL reclaim) | ✅ DONE + đã test |
| Standalone Node app (UI config, proxy rotate, grid, remote log) | ✅ DONE |
| **SaaS API layer** (dashboard, notification, CMS, nạp crypto) | ✅ **DONE (mới)** + đã test |
| FE Next.js | ⬜ chủ dự án tự build (repo riêng) |
| Refund điểm khi fail terminal | ⬜ chưa làm |
| Mã hoá credential at-rest | ⬜ chưa làm |

---

## ✅ SaaS API layer — vừa hoàn thành (2026-09-08)

Mục tiêu: cung cấp **đầy đủ API** cho FE (repo riêng) — dashboard, order, records-per-order,
+ feature hay: notification, CMS banner/modal, nạp điểm tự động qua crypto. Đã test
end-to-end bằng TestClient (auth/deposit/idempotent/notification/dashboard/CMS/pool).

### 1. Dashboard  ✅
- `GET /dashboard` — balance, order/record theo status, chi tiêu, success rate, số
  notification chưa đọc, order/giao dịch gần đây (1 call cho trang tổng quan).
- `GET /dashboard/admin` — số liệu toàn hệ thống (users, điểm lưu hành, deposits...).

### 2. Orders + records-per-order  ✅
- Giữ nguyên `validate` / create / list / get.
- `GET /orders/{id}/records` (kèm cookie/kết quả, chỉ chủ đơn) + filter `status`.
- `GET /orders/{id}/export` — text `user:cookie` cho record thành công (= "sản phẩm" khách mua).

### 3. Notification  ✅
- `Notification` (user_id NULL = broadcast) + `NotificationRead` (đọc theo từng user →
  broadcast vẫn đánh dấu đọc riêng lẻ).
- `GET /notifications` (`unread_only`), `/unread-count`, `POST /{id}/read`, `/read-all`.
- Tự bắn: **tạo đơn**, **đơn về terminal** (completed/partial/failed), **nạp crypto thành công**.
- Admin broadcast: `POST /admin/notifications`.

### 4. CMS banner / modal / announcement  ✅
- `CmsContent` (kind, placement, time-window, priority, dismissible, is_active) +
  `CmsDismissal` (tắt theo user).
- Public `GET /cms/active?placement=&kind=` (có token → lọc bỏ cái đã dismiss).
- `POST /cms/{id}/dismiss`. Admin CRUD `/admin/cms` (list/create/get/patch/delete).

### 5. Nạp điểm tự động qua crypto  ✅
- **Port `CryptoPaymentProvider`** (swap bằng `CRYPTO_PROVIDER`, như captcha): registry +
  factory. Provider `manual` (mặc định — hiện địa chí ví + admin/webhook nội bộ confirm)
  và `nowpayments` (HTTP thật + xác thực IPN HMAC-SHA512, đã test chữ ký).
- `Deposit` (points↔crypto theo tỷ giá chốt, external_id, tx_hash, expires, status).
- `POST /billing/deposits` (tạo lệnh → trả địa chỉ/invoice), list/get/cancel.
- `POST /billing/deposits/webhook` — **idempotent** (đã confirmed thì không cộng lại),
  confirm → cộng điểm (`tx_type=deposit`) + notification.
- `POST /admin/deposits/{id}/confirm` — confirm tay (manual / tranh chấp).
- `GET /billing/crypto-config`, `GET /billing/transactions` (sổ cái điểm).

### 6. Hạ tầng đi kèm  ✅
- **CORS** (`APP_CORS_ORIGINS`) cho FE Next.js gọi vào (auth qua header, không cookie).
- **API key = chỉ ADMIN** (`POST /auth/api-keys` → `require_admin`): key này để node
  claim pool (nội bộ), khách không cần.
- `.env.example` bổ sung nhóm `CRYPTO_*` + `APP_CORS_ORIGINS`.
- Docs: [`docs/api.md`](docs/api.md).

### 🐞 Bug đã fix trong lúc test
- `pool/_sync_order`: `autoflush=False` khiến đếm lại record **lệch 1 nhịp** (record vừa
  report chưa flush) → order không tới terminal, notification hoàn tất không bắn. Fix:
  `session.flush()` trước khi đếm.

---

## ✅ Flow `roblox.login` — chạy được (chốt hướng extension)

- Login **viewport PC** → tới `/not-approved` thì **giả lập phone** (CDP device metrics +
  window khớp) → refresh → Continue → giải captcha.
- Arkose FunCaptcha giải bằng **extension YesCaptcha** nạp vào **Chrome for Testing 152**
  (Chrome 151 stable chặn `--load-extension`). API 2captcha/yescaptcha **không** giải được
  Roblox FunCaptcha → đã pivot sang extension.
- Xử lý `/not-approved` (account locked state machine), QR "cần app mobile" → `need_mobile_app`,
  app-promo về `/` = success. Phân loại lỗi terminal vs hạ tầng.
- Proxy rotation (4 format, test-live-trước, đổi mỗi N browser) qua MV3 proxy-auth extension.

---

## ✅ Pool phân tán + Node app — DONE

- Claim atomic dialect-aware: Postgres `FOR UPDATE SKIP LOCKED`, SQLite UPDATE tuần tự +
  WAL + busy_timeout. Test 30 thread × 2 claim → 30 unique, 0 trùng, 0 "database locked".
- Retry: fail login = terminal (FAILED ngay); fail hạ tầng + còn lượt = requeue (attempt+1),
  hết lượt → FAILED. Đã verify vòng đời.
- TTL reclaim node chết. Scope: khách xem record của mình, admin xem tất cả.
- Node standalone: FastAPI UI (pool_url/token, proxies, rotate, captcha key), NodeAgent
  claim–run–report + RAM gate + SlotAllocator grid; remote log PC info + account count;
  đóng gói PyInstaller (Chrome for Testing + auto-install Python).

---

## ⬜ Còn lại / nợ kỹ thuật

- **FE Next.js** — chủ dự án tự build repo riêng (backend đã sẵn API + CORS + docs).
- **Refund điểm** khi record fail terminal (hiện trừ trước, chưa hoàn). Build từ
  `BillingService.refund` + hook ở `pool/report` khi FAILED.
- **Mã hoá credential at-rest** (`records.username/password` đang plaintext — có TODO).
- **Test provider `nowpayments` thật** (cần API key + callback URL public; hiện mới test
  chữ ký IPN offline).
- `email-validator` / `pyotp` chưa vào `pyproject` (cài tay trong venv để chạy).
- Refund/metrics per-node, ưu tiên claim theo success-rate — để sau.

Design doc node fleet: artifact "Node Fleet Architecture".
