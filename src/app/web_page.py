"""Trang web SaaS (single-page) - login/register, tao order, xem pool.

Compact, dung fetch + JWT trong localStorage. Server chi serve HTML nay o "/".
"""

WEB_PAGE = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Roblox SaaS</title>
<style>
:root{--bg:#0f1216;--card:#171b21;--line:#252b34;--ink:#e6e9ee;--mut:#8b95a3;--acc:#3b82f6;--ok:#22c55e;--err:#ef4444;--warn:#f59e0b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px system-ui,Segoe UI,Roboto}
.wrap{max-width:1000px;margin:0 auto;padding:16px}
h1{font-size:18px;margin:0 0 12px}.mut{color:var(--mut)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin-bottom:14px}
label{display:block;color:var(--mut);font-size:12px;margin:8px 0 4px}
input,textarea,button{width:100%;background:#0f1216;border:1px solid var(--line);color:var(--ink);border-radius:8px;padding:9px;font:13px system-ui}
textarea{resize:vertical;min-height:90px;font-family:ui-monospace,monospace}
button{background:var(--acc);border:none;color:#fff;cursor:pointer;font-weight:600;width:auto;padding:9px 16px}
button.sec{background:#222834}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.pill{display:inline-block;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600}
.s-success{background:#0f2a19;color:var(--ok)}.s-failed{background:#2a1315;color:var(--err)}
.s-queued{background:#2a2410;color:var(--warn)}.s-running{background:#12233a;color:#60a5fa}
table{width:100%;border-collapse:collapse;font-size:12px}th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line)}
th{color:var(--mut);font-weight:500}.hide{display:none}.tab{cursor:pointer;padding:8px 14px;border-radius:8px;background:#222834}
.tab.on{background:var(--acc)}.msg{font-size:12px;margin-top:6px}.err{color:var(--err)}.ok{color:var(--ok)}
code{background:#0f1216;padding:2px 6px;border-radius:6px;font-size:12px}
</style></head><body><div class="wrap">
<h1>Roblox SaaS <span class="mut" id="whoami"></span></h1>

<div id="auth" class="card">
  <div class="row"><span class="tab on" id="t-login" onclick="tab('login')">Đăng nhập</span>
    <span class="tab" id="t-reg" onclick="tab('reg')">Đăng ký</span></div>
  <label>Email</label><input id="email" type="email" placeholder="you@mail.com">
  <label>Mật khẩu</label><input id="pass" type="password" placeholder="••••••">
  <div style="margin-top:10px"><button id="authbtn" onclick="doAuth()">Đăng nhập</button></div>
  <div class="msg" id="authmsg"></div>
</div>

<div id="app" class="hide">
  <div class="card row" style="justify-content:space-between">
    <div>Số dư: <b id="bal">–</b> điểm</div>
    <div class="row">
      <button class="sec" onclick="mkKey()">Tạo API key (cho node)</button>
      <button class="sec" onclick="logout()">Đăng xuất</button>
    </div>
  </div>
  <div class="msg" id="keymsg"></div>

  <div class="card">
    <h1 style="font-size:15px">Tạo order</h1>
    <label>Danh sách account (mỗi dòng <code>user:pass</code>) — mỗi account = 1 điểm</label>
    <textarea id="accts" placeholder="user1:pass1&#10;user2:pass2"></textarea>
    <div class="row" style="margin-top:8px">
      <button class="sec" onclick="validate()">Kiểm tra</button>
      <button onclick="createOrder()">Tạo order (trừ điểm)</button>
    </div>
    <div class="msg" id="ordmsg"></div>
  </div>

  <div class="card">
    <div class="row" style="justify-content:space-between"><h1 style="font-size:15px">Pool — tất cả record</h1>
      <button class="sec" onclick="loadPool()">Tải lại</button></div>
    <div class="mut" id="poolstats" style="font-size:12px;margin-bottom:8px"></div>
    <div style="overflow:auto"><table id="pooltbl"><thead><tr>
      <th>Account</th><th>Trạng thái</th><th>Lần</th><th>Node</th><th>Lỗi</th></tr></thead><tbody></tbody></table></div>
  </div>
</div>

<script>
const $=id=>document.getElementById(id);
let mode='login', tokenKey='rlx_saas_token';
const tok=()=>localStorage.getItem(tokenKey);
const H=()=>({'Content-Type':'application/json','Authorization':'Bearer '+tok()});
async function api(m,p,b){const r=await fetch('/api/v1'+p,{method:m,headers:H(),body:b?JSON.stringify(b):undefined});
  let j=null;try{j=await r.json()}catch(e){}; return {ok:r.ok,status:r.status,j};}
function tab(t){mode=t;$('t-login').classList.toggle('on',t==='login');$('t-reg').classList.toggle('on',t==='reg');
  $('authbtn').textContent=t==='login'?'Đăng nhập':'Đăng ký';}
async function doAuth(){const email=$('email').value.trim(),password=$('pass').value;
  const path=mode==='login'?'/auth/login':'/auth/register';
  const r=await api('POST',path,{email,password});
  if(r.ok&&r.j.access_token){localStorage.setItem(tokenKey,r.j.access_token);show();}
  else $('authmsg').innerHTML='<span class=err>'+((r.j&&(r.j.message||r.j.detail))||'lỗi')+'</span>';}
function logout(){localStorage.removeItem(tokenKey);location.reload();}
async function show(){$('auth').classList.add('hide');$('app').classList.remove('hide');
  const b=await api('GET','/billing/balance'); if(b.ok)$('bal').textContent=b.j.balance;
  loadPool();}
async function mkKey(){const r=await api('POST','/auth/api-keys');
  if(r.ok)$('keymsg').innerHTML='API key (lưu lại, chỉ hiện 1 lần): <code>'+r.j.api_key+'</code>';}
async function validate(){const accounts=$('accts').value;const r=await api('POST','/orders/validate',{service_id:'roblox.login',accounts});
  if(r.ok)$('ordmsg').innerHTML='Hợp lệ: <b>'+r.j.valid_count+'</b> | Lỗi: '+r.j.invalid_count+' | Trừ: <b>'+r.j.total_price+'</b> điểm'
    +(r.j.errors&&r.j.errors.length?'<br><span class=err>'+r.j.errors.slice(0,5).map(e=>'dòng '+e.line+': '+e.error).join('<br>')+'</span>':'');
  else $('ordmsg').innerHTML='<span class=err>'+(r.j.message||'lỗi')+'</span>';}
async function createOrder(){const accounts=$('accts').value;const r=await api('POST','/orders',{service_id:'roblox.login',accounts});
  if(r.ok){$('ordmsg').innerHTML='<span class=ok>Đã tạo order '+r.j.id.slice(0,8)+' ('+r.j.quantity+' account, trừ '+r.j.total_price+' điểm)</span>';
    const b=await api('GET','/billing/balance');if(b.ok)$('bal').textContent=b.j.balance;loadPool();}
  else $('ordmsg').innerHTML='<span class=err>'+(r.j.message||'lỗi (thiếu điểm?)')+'</span>';}
async function loadPool(){const s=await api('GET','/pool/stats');
  if(s.ok)$('poolstats').textContent=Object.entries(s.j).map(([k,v])=>k+': '+v).join('  ·  ')||'trống';
  const r=await api('GET','/pool/records');const tb=$('pooltbl').querySelector('tbody');tb.innerHTML='';
  if(r.ok)r.j.forEach(x=>{const tr=document.createElement('tr');
    tr.innerHTML='<td>'+x.username+'</td><td><span class="pill s-'+x.status+'">'+x.status+'</span></td>'
      +'<td>'+x.attempt+'</td><td class=mut>'+(x.node_id||'–')+'</td><td class=mut>'+(x.error_code||'')+'</td>';tb.appendChild(tr);});}
if(tok())show();
</script></div></body></html>"""
