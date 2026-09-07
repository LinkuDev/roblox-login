# Flow dang nhap Roblox (service `roblox.login`)

| # | Step              | optional | retry | Mo ta |
|---|-------------------|----------|-------|-------|
| 1 | open_login        | no       | 2     | Mo trang login, phat hien phien san co |
| 2 | fill_credentials  | no       | 0     | Dien tk/mk (bo qua neu da dang nhap) |
| 3 | submit_login      | no       | 0     | Bam nut dang nhap |
| 4 | solve_captcha     | **yes**  | 1     | Chi chay khi co khung captcha; goi CaptchaSolver |
| 5 | handle_2fa        | **yes**  | 0     | Chi chay khi tk bat 2FA; sinh ma TOTP |
| 6 | detect_result     | no       | 0     | Xac dinh thanh/bai, lay cookie session, phan loai loi |

Loi nghiep vu (sai mk, khoa tk, 2FA, rate limit) duoc phan loai thanh error_code
rieng trong `detect_result` va cac exception `AutomationError` -> tang tren xu ly
duoc (vd khong tru point, hien thong bao dung cho khach).

Ket qua tra ve la `RunResult` gom: success, tung step, chi phi captcha, screenshot
khi loi, va session cookie (`.ROBLOSECURITY`) neu thanh cong.
