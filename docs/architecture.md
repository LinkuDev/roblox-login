# Kien truc

## Nguyen tac
1. **Ports & Adapters**: tang trong (domain, automation, services) chi phu thuoc
   *interface* (`domain/ports`), khong biet gi ve 2captcha hay botasaurus.
   Adapter cu the nam trong `providers/` va tu dang ky vao registry.
2. **Registry + Factory**: doi provider = doi 1 bien env
   (`CAPTCHA_PROVIDER`, `BROWSER_PROVIDER`, `PROXY_PROVIDER`, `QUEUE_BACKEND`).
3. **Flow = list[Step]**: moi buoc dang nhap la 1 Step doc lap, co retry / optional /
   dieu kien chay rieng. Them/bot buoc khong dung buoc khac.
4. **Point-first billing**: chua co thanh toan tu dong. Tru diem khi job THANH CONG.
   Doi chinh sach (tru truoc, goi thang cong thanh toan) chi sua `modules/billing`
   va `modules/orders`.

## Luong 1 don hang (SaaS)
```
POST /orders  -> OrderService.create
     tao Order + N OrderItem + N Job (status=queued) -> enqueue vao JobQueue
Worker.dequeue -> execute_job(job_id)
     doc input -> run_service() -> Flow chay cac Step
     thanh cong: BillingService.charge (tru point) + cap nhat Order
     that bai : ghi error_code, khong tru point
```

## Luong 1 lan chay service (nhan automation)
```
run_service()  (automation/runner.py = composition root)
  build_solver()  build_browser()  build_proxy_provider()
  -> ExecutionContext(credential, browser, solver, proxy, storage)
  -> Service.build_flow(ctx) -> Flow.run(ctx)
       OpenLoginPage -> FillCredentials -> Submit
       -> SolveCaptcha (goi CaptchaSolver PORT) -> Handle2FA -> DetectResult
  -> RunResult (success, steps, cost, artifacts, session cookie)
```

## Tai sao tach `runner` khoi `executor`
- `runner.run_service`: chay 1 service, khong biet DB/point. Dung cho CLI, test.
- `executor.execute_job`: cau noi DB <-> runner, cap nhat order/point.
Nho vay flow automation kiem thu doc lap voi tang SaaS.
