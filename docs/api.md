# SaaS API Reference

Backend FastAPI, API-first (FE Next.js la repo rieng goi vao day). Tat ca duong dan
duoi prefix `/api/v1`. OpenAPI tu dong: `GET /openapi.json`, Swagger UI `GET /docs`.

- Base URL dev: `http://localhost:8000`
- Content-Type: `application/json` (tru `/export` tra text, `/deposits/webhook` nhan raw).
- Ngon ngu loi: response loi co dang `{ "code": "...", "message": "...", "context": {...} }`.

---

## 1. Xac thuc (Auth)

Hai cach gui kem request:

| Cach | Header | Dung cho |
|------|--------|----------|
| JWT (nguoi dung) | `Authorization: Bearer <access_token>` | Web/FE dang nhap |
| API key (node) | `X-API-Key: rlx_...` | Node claim pool. **Chi ADMIN tao duoc.** |

Vai tro: `user` (khach) va `admin`. Email trong `APP_ADMIN_EMAILS` tu dong len `admin`
luc register. Admin = topup diem tay, quan ly CMS, confirm nap, gui thong bao, va tao
API key cho node.

### POST `/auth/register`
Body: `{ "email": "...", "password": "..." }` (password >= 6 ky tu).
→ `{ "access_token": "...", "token_type": "bearer" }`

### POST `/auth/login`
Body: `{ "email": "...", "password": "..." }` → `{ "access_token": "..." }`

### POST `/auth/api-keys`  · **admin**
Query: `label` (optional). → `{ "api_key": "rlx_...", "label": "" }`
Key chi tra 1 lan (luu ban bam). Node dung key nay o header `X-API-Key` de claim pool.

---

## 2. Dashboard

### GET `/dashboard`  · user
Tong hop cua chinh user (goi 1 lan cho trang tong quan):
```json
{
  "scope": "user",
  "balance": 5050,
  "orders": { "processing": 1, "completed": 3, "total": 4 },
  "records": { "queued": 0, "running": 0, "success": 8, "failed": 2, "total": 10 },
  "spent_points": 10,
  "success_rate": 80.0,
  "unread_notifications": 2,
  "recent_orders": [ { "id": "...", "service_id": "roblox.login", "status": "partial", ... } ],
  "recent_transactions": [ { "type": "deposit", "amount": 5000, "balance_after": 5050, ... } ]
}
```

### GET `/dashboard/admin`  · **admin**
So lieu toan he thong: `users`, `points_in_circulation`, `orders`, `records`,
`confirmed_deposits`, `recent_orders`.

---

## 3. Services (catalog)

### GET `/services`
Danh sach dich vu ban:
```json
[ { "id": "roblox.login", "name": "...", "category": "...", "price_points": 1,
    "description": "...", "input_fields": ["username","password"] } ]
```

---

## 4. Orders + Records

Mo hinh diem: **tru NGAY khi tao order** = so dong hop le × `price_points`. Moi dong
(account) thanh 1 **record** trong pool.

### POST `/orders/validate`  · user
Dry-run cho form (khong tao, khong tru diem).
Body: `{ "service_id": "roblox.login", "accounts": "user1:pass1\nuser2:pass2" }`
```json
{ "service_id": "roblox.login", "valid_count": 2, "invalid_count": 0,
  "unit_price": 1, "total_price": 2, "errors": [] }
```

### POST `/orders`  · user
Body: `{ "service_id": "...", "accounts": "user:pass\n...", "note": "" }`
Tru diem (thieu → 402 `insufficient_points`), sinh record, day vao pool.
→ `OrderResponse` (id, status, quantity, unit_price, total_price, completed_count, failed_count).

### GET `/orders`  · user — danh sach don cua minh.
### GET `/orders/{order_id}`  · user — chi tiet 1 don (chi chu don).

### GET `/orders/{order_id}/records`  · user
Records cua don (kem ket qua). Query `status` (optional): `queued|running|success|failed`.
```json
[ { "id": "...", "username": "alice", "status": "success", "attempt": 1,
    "error_code": "", "reason": "", "cookies": "{\".ROBLOSECURITY\":\"...\"}",
    "duration": 4.2, "created_at": "..." } ]
```

### GET `/orders/{order_id}/export`  · user
Tra **text/plain**: moi dong `username:cookie` cho cac record thanh cong. Day la "san
pham" khach mua (gia tri `.ROBLOSECURITY`).

---

## 5. Billing (diem + nap crypto)

### GET `/billing/balance`  · user → `{ "balance": 5050 }`
### GET `/billing/transactions`  · user
So cai diem cua chinh user: `[ { type, amount, balance_after, note } ]`
(type: `topup|deposit|spend|refund|bonus|adjust`).

### POST `/billing/topup`  · **admin**
Cong diem tay cho 1 user. Body: `{ "user_id": "...", "amount": 100, "note": "" }`.

### Nap tu dong qua crypto

Doi cong thanh toan = doi 1 dong config `CRYPTO_PROVIDER` (`manual` | `nowpayments`),
khong sua code. Xem `core/config.py :: CryptoSettings`.

#### GET `/billing/crypto-config`  · public
Cau hinh cho FE dung form nap:
```json
{ "enabled": true, "provider": "nowpayments", "usd_per_point": 0.03,
  "min_usd": 1.0, "min_points": 33, "currencies": [] }
```

#### POST `/billing/deposits`  · user
Tao lenh nap. Body: `{ "amount_points": 5000, "currency": "USDT" }`.
He thong tinh so crypto phai tra (`amount_points * usd_per_point`) + lay dia
chi/invoice tu provider:
```json
{ "id": "...", "status": "pending", "provider": "manual", "amount_points": 5000,
  "currency": "USDT", "amount_crypto": 5.0, "pay_address": "TXyz...", "pay_url": "",
  "tx_hash": "", "expires_at": "...", "confirmed_at": null, "created_at": "..." }
```

#### GET `/billing/deposits`  · user — danh sach lenh nap cua minh.
#### GET `/billing/deposits/{id}`  · user — trang thai 1 lenh (FE poll cho toi `confirmed`).
#### POST `/billing/deposits/{id}/cancel`  · user — huy lenh chua ket thuc.

#### POST `/billing/deposits/webhook`  · public (xac thuc chu ky)
Callback provider goi ve. **Khong auth** — provider tu xac thuc bang chu ky IPN
(NOWPayments: HMAC-SHA512 tren body JSON sort key, header `x-nowpayments-sig`).
**Idempotent**: da `confirmed` thi khong cong diem lai (chong webhook lap).
Khi `confirmed` → cong diem (tx_type=`deposit`) + ban thong bao "Nap diem thanh cong".

Vong doi trang thai: `pending → confirming → confirmed` (terminal) | `expired` | `failed` | `cancelled`.

> Provider `manual` khong nhan webhook → admin confirm tay (muc 7).

---

## 6. Notifications

Thong bao trong app. Broadcast (moi user) hoac rieng 1 user. Trang thai "da doc"
luu theo tung user nen broadcast van danh dau doc rieng le.

### GET `/notifications`  · user
Query: `unread_only` (bool), `limit`, `offset`.
```json
[ { "id": "...", "level": "success", "title": "Nap diem thanh cong",
    "body": "...", "link_url": "", "ref_type": "deposit", "ref_id": "...",
    "is_broadcast": false, "unread": true, "created_at": "..." } ]
```
`level`: `info|success|warning|error` (FE to mau/icon).

### GET `/notifications/unread-count`  · user → `{ "unread": 2 }`
### POST `/notifications/{id}/read`  · user → `{ "ok": true }`
### POST `/notifications/read-all`  · user → `{ "ok": true, "marked": 3 }`

Su kien tu dong ban thong bao: tao don, don ve trang thai ket thuc
(completed/partial/failed), nap crypto thanh cong.

---

## 7. CMS (banner / modal / announcement)

Admin bat/tat noi dung khong can deploy. FE render theo `placement` + `kind`.

### GET `/cms/active`  · public (co token thi ca nhan hoa)
Query: `placement`, `kind` (optional). Tra cac muc dang bat + trong cua so thoi gian,
sap theo `priority` giam. Neu gui token → loc bo cai user da `dismiss`.
```json
[ { "id": "...", "kind": "banner", "placement": "dashboard_top", "title": "Sale 20%",
    "body": "...", "image_url": "", "link_url": "", "cta_label": "", "level": "success",
    "priority": 10, "dismissible": true } ]
```
`kind`: `banner|modal|announcement`.

### POST `/cms/{id}/dismiss`  · user → tat 1 muc dismissible (khong hien lai cho user do).

### Quan ly (admin) — xem muc 8.

---

## 8. Admin (`/admin/*`, toan bo **require admin**)

### CMS
- `GET  /admin/cms` — liet ke tat ca (ke ca dang tat).
- `POST /admin/cms` — tao. Body: `CmsCreateRequest` (kind, placement, title, body,
  image_url, link_url, cta_label, level, priority, dismissible, is_active,
  starts_at, ends_at).
- `GET  /admin/cms/{id}` — chi tiet.
- `PATCH /admin/cms/{id}` — sua (gui field nao doi field do).
- `DELETE /admin/cms/{id}` — xoa.

### Notification broadcast
- `POST /admin/notifications` — Body: `{ title, body, level, user_id?, link_url }`.
  `user_id` = null → broadcast toan bo; co user_id → gui rieng 1 user.

### Deposits (crypto)
- `POST /admin/deposits/{id}/confirm` — confirm tay 1 lenh nap (provider `manual` hoac
  xu ly tranh chap). Body: `{ "tx_hash": "" }`. Cong diem **1 lan** (idempotent).

---

## 9. Pool phan tan (node claim) — **admin key**

Node dung `X-API-Key` cua admin. Khach (`user`) **khong** claim/report duoc.

- `POST /pool/claim` — Body: `{ "node_id": "", "ttl_seconds": 300 }`. Lay 1 record
  (atomic, khong 2 node trung). `204 No Content` neu pool rong.
- `POST /pool/report` — Body: `{ "record_id": "...", "result": {...}, "node_id": "" }`.
  `result.success=true` → SUCCESS + luu cookie. Loi login (terminal:
  `invalid_credentials|account_locked|need_mobile_app|two_factor_required`) → FAILED.
  Loi ha tang & con luot → tra lai pool (retry 1 lan).
- `GET /pool/records` — Query `order_id`, `status`. Khach xem record cua minh; admin xem tat ca.
- `GET /pool/stats` — dem theo status (scoped nhu tren).

---

## 10. Cau hinh lien quan FE/nap (env)

| Env | Y nghia |
|-----|---------|
| `APP_CORS_ORIGINS` | Origin FE duoc phep goi API (`*` hoac list). |
| `APP_ADMIN_EMAILS` | Email tu dong len admin luc register. |
| `CRYPTO_PROVIDER` | `manual` \| `nowpayments`. |
| `CRYPTO_USD_PER_POINT` | Gia 1 diem = bao nhieu USD (vd 0.03). |
| `CRYPTO_MIN_USD` | Nap toi thieu theo USD. |
| `CRYPTO_CURRENCIES` | Coin cho phep (allowlist). De trong -> NOWPayments tu quyet. |
| `CRYPTO_WALLET_ADDRESS` | (manual) dia chi vi nhan tien. |
| `CRYPTO_API_KEY` / `CRYPTO_IPN_SECRET` / `CRYPTO_CALLBACK_BASE` | (nowpayments). |

Xem them `.env.example`.
