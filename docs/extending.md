# Mo rong he thong

## Them nha cung cap giai captcha moi
1. Tao `src/app/providers/captcha/<ten>.py`.
2. Neu provider theo mo hinh createTask/getTaskResult -> ke thua `HttpTaskSolver`,
   chi cai `build_task()`. Neu khac -> implement thang `CaptchaSolver`.
3. Decorator `@captcha_registry.register("<ten>")`.
4. Import trong `providers/captcha/__init__.py`, them API key vao `ProviderKeys`.
5. Doi provider: `CAPTCHA_PROVIDER=<ten>` trong `.env`. Khong sua step/flow.

## Them service moi (san pham ban)
1. Tao thu muc `src/app/services/<category>/`.
2. Viet cac Step trong `steps/` (ke thua `automation.Step`).
3. Viet Service (ke thua `services.base.Service`), khai bao `ServiceSpec`
   (id, gia point, input) va `build_flow()` rap cac Step.
4. `@service_registry.register("<category>.<name>")` + import de dang ky.
5. Service tu dong xuat hien o `GET /api/v1/services` va CLI `rlx services`.

## Doi browser engine (botasaurus -> playwright...)
Viet adapter implement `BrowserProvider` + `BrowserSession`, dang ky vao
`browser_registry`, doi `BROWSER_PROVIDER`. Step khong thay doi.

## Them thanh toan tu dong (tuong lai)
Point da co san. Chi can:
1. Them module `modules/payments/` voi port `PaymentGateway` + adapter (stripe...).
2. Webhook thanh cong -> `BillingService.topup(user_id, points)`.
Cac tang khac khong doi.

## TODO(flow) can dien khi chay that
- `steps/solve_captcha.py::_extract_blob` — lay dataExchangeBlob cua Arkose.
- `steps/solve_captcha.py::_inject_token` — bom token vao callback Arkose.
- `services/roblox/constants.py` — xac nhan lai selector + FUNCAPTCHA_PUBLIC_KEY.
- `providers/browser/botasaurus_driver.py::switch_to_iframe` — chot API iframe.
