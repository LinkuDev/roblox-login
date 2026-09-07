"""Web UI cau hinh + dieu khien node - chay local, mo trong cua so Chrome (--app).

Compact, cua so co dinh (khoa resize bang JS). Start = lang nghe pool, Stop = dung.
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from robloxnode.agent import NodeAgent
from robloxnode.config import CAPTCHA_PROVIDERS, NodeConfig, default_config_path
from robloxnode.flows import stub_flow
from robloxnode.pool import LocalPool
from robloxnode.realflow import real_flow


class ConfigBody(BaseModel):
    pool_url: str = ""
    captcha_provider: str = "yescaptcha"
    captcha_key: str = ""
    ram_overflow_percent: int = 85


class PoolAddBody(BaseModel):
    lines: str = ""


def build_app() -> FastAPI:
    app = FastAPI(title="Roblox Node")

    pool = LocalPool()   # RONG: chua co pool that. Nap record test qua /api/pool/add
    # mac dinh chay flow THAT (mo Chrome). Dat RLX_NODE_FLOW=stub de gia lap khong browser.
    run_flow = stub_flow if os.environ.get("RLX_NODE_FLOW") == "stub" else real_flow
    agent = NodeAgent(
        pool,
        run_flow,
        get_overflow_percent=lambda: NodeConfig.load().ram_overflow_percent,
    )

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return _PAGE

    @app.get("/api/config")
    def get_config() -> JSONResponse:
        cfg = NodeConfig.load()
        data = cfg.to_dict()
        data["_providers"] = CAPTCHA_PROVIDERS
        data["_path"] = str(default_config_path())
        return JSONResponse(data)

    @app.post("/api/config")
    def save_config(body: ConfigBody) -> JSONResponse:
        cfg = NodeConfig.load()
        cfg.pool_url = body.pool_url
        cfg.captcha_provider = body.captcha_provider
        cfg.captcha_key = body.captcha_key
        cfg.ram_overflow_percent = body.ram_overflow_percent
        path = cfg.normalized().save()
        return JSONResponse({"ok": True, "path": str(path)})

    @app.post("/api/agent/start")
    def agent_start() -> JSONResponse:
        agent.start()
        return JSONResponse(agent.status())

    @app.post("/api/agent/stop")
    def agent_stop() -> JSONResponse:
        agent.stop()
        return JSONResponse(agent.status())

    @app.get("/api/agent/status")
    def agent_status() -> JSONResponse:
        return JSONResponse(agent.status())

    @app.post("/api/pool/add")
    def pool_add(body: PoolAddBody) -> JSONResponse:
        """Nap record test vao LocalPool (chua co pool that)."""
        added = pool.add_lines(body.lines)
        return JSONResponse({"added": added, "pending": pool.pending_count()})

    return app


_PAGE = """<!doctype html>
<html lang="vi"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Roblox Node</title>
<style>
  :root{
    --bg:#0f141b; --card:#171e28; --line:#28313d; --ink:#e6ebf1; --muted:#8a95a3;
    --node:#2fc7be; --node-dim:rgba(47,199,190,.14); --warn:#e0a44a; --danger:#e56a6a;
    --field:#0f151d;
  }
  *{box-sizing:border-box}
  html,body{margin:0}
  body{background:var(--bg);color:var(--ink);
    font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;font-size:13px;
    -webkit-user-select:none;user-select:none}
  .app{max-width:460px;margin:0 auto;padding:16px 16px 24px}
  header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
  .brand{font-weight:600;font-size:15px;display:flex;align-items:center;gap:8px}
  .dot{width:8px;height:8px;border-radius:50%;background:var(--muted)}
  .dot.on{background:var(--node);box-shadow:0 0 0 3px var(--node-dim)}
  .listen{font-size:12px;color:var(--muted)}
  .listen.on{color:var(--node)}
  .toggle{width:100%;border:0;border-radius:11px;padding:13px;font-size:14px;font-weight:600;
    cursor:pointer;margin-bottom:12px;color:#04211f;background:var(--node)}
  .toggle.stop{background:var(--danger);color:#fff}
  .toggle:hover{filter:brightness(1.06)}
  .stats{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px}
  .stat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:9px 6px;text-align:center}
  .stat b{display:block;font-size:17px;font-variant-numeric:tabular-nums}
  .stat span{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
  .stat.fail b{color:var(--danger)}
  .ram{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:11px 12px;margin-bottom:12px}
  .ram-top{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px}
  .ram-top b{font-size:16px;font-variant-numeric:tabular-nums}
  .badge{font-size:10px;font-weight:600;padding:3px 9px;border-radius:20px;letter-spacing:.03em}
  .badge.ok{background:var(--node-dim);color:var(--node)}
  .badge.full{background:rgba(229,106,106,.16);color:var(--danger)}
  .meter{position:relative;height:9px;background:var(--field);border:1px solid var(--line);border-radius:20px;overflow:hidden}
  .meter .fill{height:100%;background:var(--node);width:0%;transition:width .4s,background .3s}
  .meter.full .fill{background:var(--danger)}
  .thresh{position:absolute;top:-3px;bottom:-3px;width:2px;background:var(--warn);z-index:2}
  .slots{max-height:200px;overflow-y:auto;background:var(--card);border:1px solid var(--line);border-radius:10px;
    padding:6px;margin-bottom:12px;min-height:60px}
  .slot{display:flex;justify-content:space-between;font-size:12px;padding:5px 8px;border-radius:7px}
  .slot:nth-child(odd){background:rgba(255,255,255,.02)}
  .slot .u{color:var(--ink)}
  .slot .t{color:var(--muted);font-variant-numeric:tabular-nums}
  .slots .empty{color:var(--muted);text-align:center;padding:18px 0;font-size:12px}
  details.cfg{background:var(--card);border:1px solid var(--line);border-radius:10px}
  details.cfg>summary{cursor:pointer;padding:10px 12px;font-size:12px;color:var(--muted);
    text-transform:uppercase;letter-spacing:.06em;font-weight:600;list-style:none}
  details.cfg>summary::-webkit-details-marker{display:none}
  details.cfg[open]>summary{color:var(--node)}
  .cfgbody{padding:2px 12px 12px}
  .row{margin-bottom:10px}
  .row:last-child{margin-bottom:0}
  label{display:block;font-size:11px;color:var(--muted);margin-bottom:4px}
  input,select,textarea{width:100%;background:var(--field);border:1px solid var(--line);color:var(--ink);
    border-radius:8px;padding:8px 10px;font-size:13px;font-family:inherit;outline:none}
  textarea{font-size:12px;resize:none;line-height:1.5}
  input:focus,select:focus,textarea:focus{border-color:var(--node)}
  .keywrap{position:relative}
  .keywrap button{position:absolute;right:4px;top:4px;background:none;border:0;color:var(--muted);cursor:pointer;font-size:11px;padding:4px 7px}
  .steprow{display:flex;gap:9px;align-items:center}
  .steprow input[type=range]{flex:1;accent-color:var(--node)}
  .steprow .val{width:46px;text-align:right;font-variant-numeric:tabular-nums;font-weight:600}
  .save{width:100%;background:var(--field);color:var(--node);border:1px solid var(--node);
    border-radius:8px;padding:9px;font-weight:600;font-size:13px;cursor:pointer;margin-top:2px}
  .save:hover{background:var(--node-dim)}
  .savedmsg{font-size:11px;color:var(--node);text-align:center;height:14px;margin-top:5px}
</style></head>
<body><div class="app">
  <header>
    <div class="brand">Roblox Node <span class="dot" id="dot"></span></div>
    <div class="listen" id="listen">dừng</div>
  </header>

  <button class="toggle start" id="toggle">Start · lắng nghe</button>

  <div class="stats">
    <div class="stat"><b id="s_slots">0/0</b><span>slot</span></div>
    <div class="stat"><b id="s_pending">0</b><span>chờ</span></div>
    <div class="stat"><b id="s_done">0</b><span>xong</span></div>
    <div class="stat fail"><b id="s_failed">0</b><span>lỗi</span></div>
  </div>

  <div class="ram">
    <div class="ram-top"><span><b id="ram_now">--</b>% RAM</span><span class="badge ok" id="badge">—</span></div>
    <div class="meter" id="meter"><span class="thresh" id="thresh"></span><span class="fill" id="fill"></span></div>
  </div>

  <div class="slots" id="slots"><div class="empty">chưa chạy slot nào</div></div>

  <details class="cfg" id="cfg" open>
    <summary>Cấu hình</summary>
    <div class="cfgbody">
      <div class="row">
        <label>Pool URL (dùng phase sau)</label>
        <input id="pool_url" placeholder="wss://saas.example.com/ws/node" autocomplete="off">
      </div>
      <div class="row">
        <label>Captcha — nhà cung cấp</label>
        <select id="captcha_provider"></select>
      </div>
      <div class="row">
        <label>Captcha — API key</label>
        <div class="keywrap">
          <input id="captcha_key" type="password" placeholder="clientKey..." autocomplete="off">
          <button type="button" id="togglekey">hiện</button>
        </div>
      </div>
      <div class="row">
        <label>RAM điểm tràn — node đầy khi vượt (%)</label>
        <div class="steprow">
          <input type="range" id="ram_range" min="10" max="99" step="1">
          <span class="val"><span id="ram_val">85</span>%</span>
        </div>
      </div>
      <button class="save" id="save">Lưu cấu hình</button>
      <div class="savedmsg" id="saved"></div>
    </div>
  </details>

  <details class="cfg" id="testcfg">
    <summary>Nạp record test (chưa có pool)</summary>
    <div class="cfgbody">
      <div class="row">
        <label>user:pass mỗi dòng — chỉ để thử loop</label>
        <textarea id="test_lines" rows="3" placeholder="user1:pass1&#10;user2:pass2"></textarea>
      </div>
      <button class="save" id="addpool">Nạp vào pool</button>
      <div class="savedmsg" id="added"></div>
    </div>
  </details>
</div>
<script>
const $=id=>document.getElementById(id);
let providers=["yescaptcha"], listening=false;

async function loadConfig(){
  const c=await(await fetch('/api/config')).json();
  providers=c._providers||providers;
  const sel=$('captcha_provider'); sel.innerHTML='';
  providers.forEach(p=>{const o=document.createElement('option');o.value=p;o.textContent=p;sel.appendChild(o);});
  $('pool_url').value=c.pool_url||'';
  sel.value=c.captcha_provider||providers[0];
  $('captcha_key').value=c.captcha_key||'';
  $('ram_range').value=c.ram_overflow_percent||85;
  $('ram_val').textContent=c.ram_overflow_percent||85;
  drawThresh();
}
function drawThresh(){$('thresh').style.left=(+$('ram_range').value)+'%';}
$('ram_range').addEventListener('input',()=>{$('ram_val').textContent=$('ram_range').value;drawThresh();});
$('togglekey').addEventListener('click',()=>{const k=$('captcha_key'),b=$('togglekey');
  if(k.type==='password'){k.type='text';b.textContent='ẩn';}else{k.type='password';b.textContent='hiện';}});

$('save').addEventListener('click',async()=>{
  const body={pool_url:$('pool_url').value,captcha_provider:$('captcha_provider').value,
    captcha_key:$('captcha_key').value,ram_overflow_percent:+$('ram_range').value};
  const j=await(await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})).json();
  $('saved').textContent=j.ok?'✓ Đã lưu':'Lỗi'; setTimeout(()=>$('saved').textContent='',1800);
});

$('addpool').addEventListener('click',async()=>{
  const j=await(await fetch('/api/pool/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lines:$('test_lines').value})})).json();
  $('added').textContent='+ '+j.added+' record · chờ: '+j.pending; setTimeout(()=>$('added').textContent='',2600);
});

$('toggle').addEventListener('click',async()=>{
  const ep=listening?'/api/agent/stop':'/api/agent/start';
  render(await(await fetch(ep,{method:'POST'})).json());
});

function render(s){
  listening=s.listening;
  $('dot').className='dot'+(listening?' on':'');
  $('listen').textContent=listening?'đang lắng nghe':'dừng';
  $('listen').className='listen'+(listening?' on':'');
  const t=$('toggle'); t.textContent=listening?'Stop · dừng lắng nghe':'Start · lắng nghe';
  t.className='toggle '+(listening?'stop':'start');
  $('s_slots').textContent=s.active_slots+'/'+s.hard_cap;
  $('s_pending').textContent=s.pending;
  $('s_done').textContent=s.done;
  $('s_failed').textContent=s.failed;
  $('ram_now').textContent=s.ram_percent;
  $('fill').style.width=Math.min(100,s.ram_percent)+'%';
  $('meter').classList.toggle('full',s.full);
  const b=$('badge'); b.textContent=s.full?'ĐẦY':'CÒN NHẬN'; b.className='badge '+(s.full?'full':'ok');
  const box=$('slots');
  if(s.slots.length===0){box.innerHTML='<div class="empty">'+(listening?'chờ việc / hết headroom':'chưa chạy slot nào')+'</div>';}
  else{box.innerHTML=s.slots.map(x=>'<div class="slot"><span class="u">'+x.username+'</span><span class="t">'+x.elapsed+'s</span></div>').join('');}
}
async function poll(){try{render(await(await fetch('/api/agent/status')).json());}catch(e){}}
loadConfig().then(()=>{poll();setInterval(poll,1000);});
</script>
</body></html>"""
