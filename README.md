# Automation SaaS Platform

Nen tang chay dich vu automation (mo dau: dang nhap Roblox + giai captcha), thiet ke
de mo rong thanh SaaS: user / order / thanh toan bang **point**. Kien truc
**hexagonal (ports & adapters)**: nhan automation tach roi hoan toan khoi nha cung
cap captcha, browser va tang web -> doi provider chi bang cau hinh, khong sua logic.

## Idea chinh

**Ban "automation" nhu 1 dich vu.** Khach dua **input** (tk/mk, va tuy chon 2FA),
he thong tu thao tac tren trinh duyet (dang nhap, giai captcha, xu ly 2FA...) va tra
ve **ket qua co gia tri** (session cookie, trang thai account, screenshot). Moi loai
thao tac la 1 *service* ban duoc, tinh tien theo so lan chay thanh cong.

Ba tru cot cua y tuong:

1. **Service = san pham ban.** `roblox.login` chi la cai dau tien. Moi service = mot
   chuoi **Step** rap thanh **Flow**, co gia (point) va input schema rieng. Them dich
   vu moi (roblox.signup, doi mat khau, dich vu game khac...) = viet them Step + dang
   ky, **khong dung** vao dich vu cu. Marketplace mo rong theo chieu ngang.

2. **Moi thu deu thay the duoc (interface-first).** Automation chi noi chuyen voi
   *port* (interface), khong biet dang dung 2captcha hay CapSolver, botasaurus hay
   Playwright. **Doi nha cung cap giai captcha = doi 1 dong `.env`** (`CAPTCHA_PROVIDER`),
   khong sua flow. Tuong tu cho browser, proxy, hang doi, luu tru. Khi 1 provider chet
   hay dat len, thay provider khac trong vai phut.

3. **SaaS-ready tu goc.** User + API key + order + vi **point** da co san. Truoc mat
   chay bang point (admin cong tay / cong khi co giao dich). Khi can **thanh toan tu
   dong**, chi cam them cong thanh toan -> `topup` point, cac tang khac khong doi. Order
   chay bat dong bo qua queue + worker -> scale nhieu account song song.

**Vong doi 1 don hang:**
```
Khach: POST /orders (service_id + danh sach input)
  -> tao Order + N Job, day vao queue (chua tru point)
Worker: keo tung Job -> chay Flow (login + giai captcha + 2FA)
  -> THANH CONG: tru point + tra ket qua (cookie/session)
  -> THAT BAI : khong tru point, ghi ro ly do (sai mk / khoa / 2FA / rate limit)
```

Nguyen tac xuyen suot: **nhan automation chay doc lap** (test/CLI khong can DB, khong
can tien captcha nho `manual` solver), **tang SaaS boc ben ngoai** (point, order, API).
Nho vay ban hoan thien flow that truoc, ghep thuong mai hoa sau ma khong viet lai.

## Trang thai
- [x] Flow engine + service `roblox.login` (khung step, cho phep them buoc)
- [x] Port + adapter captcha: **2captcha / capsolver / anticaptcha / manual**
- [x] Port + adapter browser: **botasaurus** (them Playwright sau khong dung flow)
- [x] Point/billing, order, job, queue, API skeleton
- [ ] Chi tiet Arkose FunCaptcha (lay blob + inject token) — danh dau `TODO(flow)`
- [ ] Thanh toan tu dong (hien chi cong point tay qua admin)

## Cai dat
```bash
make install
cp .env.example .env      # dien TWOCAPTCHA_API_KEY...
```

## Chay thu flow (khong can DB/API)
```bash
rlx services                                   # liet ke service
rlx providers                                  # liet ke provider
rlx balance                                    # so du captcha
rlx run roblox.login -u USER -p PASS --no-headless
rlx run roblox.login --file accounts.txt --out results.json
```
Khi chua nap tien 2captcha, test bang solver thu cong:
```bash
CAPTCHA_PROVIDER=manual rlx run roblox.login -u USER -p PASS --no-headless
```

## Chay tang SaaS
```bash
make api          # http://localhost:8000/docs
make worker       # xu ly order/job trong queue
# hoac full stack:
docker compose -f docker/docker-compose.yml up
```

## Kien truc

```
API / CLI / Worker         (tang vao)
      |
  modules/                 nghiep vu SaaS: auth, users, billing(point), orders, jobs
      |
  services/                san pham ban (roblox.login...) = rap Step thanh Flow
      |
  automation/              flow engine: Step, Flow, Context, Runner
      |
  domain/ports/  <---->    providers/   (adapter: captcha, browser, proxy, storage)
```

Xem chi tiet: [docs/architecture.md](docs/architecture.md) va
[docs/extending.md](docs/extending.md).
