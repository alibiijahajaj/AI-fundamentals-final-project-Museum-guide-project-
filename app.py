"""Local web app (standard library only). Run:  python app.py   then open http://localhost:8000"""
import json
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from museum_guide import DEFAULT_MAP, LEVELS, plan_tour
from museum_guide.planner import exhibits

PAGE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Smart Museum Tour Guide</title>
<style>
 :root{--ink:#2b1d14;--paper:#fbf7ec;--wall:#f1e9d6;--gold:#b89b5e;--burgundy:#8c2f39;--green:#2f5d46}
 *{box-sizing:border-box}
 body{margin:0;background:var(--wall);color:var(--ink);font-family:Georgia,'Times New Roman',serif;
      background-image:radial-gradient(rgba(120,90,50,.07) 1px,transparent 1px);background-size:14px 14px}
 header{background:var(--ink);color:#f3e6c8;padding:26px 40px 20px;border-bottom:4px double var(--gold)}
 header .kicker{font:12px/1 Arial,sans-serif;letter-spacing:4px;text-transform:uppercase;color:var(--gold)}
 header h1{margin:8px 0 2px;font-size:34px;font-weight:normal;letter-spacing:1px}
 header p{margin:0;font-style:italic;opacity:.8}
 main{display:flex;flex-wrap:wrap;gap:26px;padding:28px 40px;align-items:flex-start}
 .placard{background:var(--paper);border:1px solid var(--gold);outline:1px solid #e2d3ac;outline-offset:4px;
          padding:18px 22px;box-shadow:0 6px 18px rgba(60,40,10,.12)}
 h2{margin:0 0 12px;font-size:13px;font-weight:normal;letter-spacing:3px;text-transform:uppercase;color:var(--burgundy);
    border-bottom:1px solid var(--gold);padding-bottom:6px}
 /* floor plan */
 #grid{display:grid;gap:0;border:6px solid #4a3a2c;width:max-content}
 .t{width:48px;height:48px;position:relative;display:flex;align-items:center;justify-content:center}
 .f0{background:#efe6d2}.f1{background:#e6dac0}
 .wall{background:#5a4636;box-shadow:inset 0 0 0 3px #4a3a2c}
 .door{background:var(--green);color:#f3e6c8;font:bold 12px Arial,sans-serif;letter-spacing:1px}
 .art{background:#efe6d2}
 .frame{display:flex;align-items:center;justify-content:center;width:34px;height:34px;background:#f7efd8;color:var(--ink);
        border:4px solid #b8891f;box-shadow:0 0 0 1px #6e5212,inset 0 0 0 1px #6e5212;font-weight:bold;font-size:17px}
 .badge{position:absolute;top:1px;right:1px;width:17px;height:17px;border-radius:50%;background:var(--ink);color:#f3e6c8;
        font:bold 11px/17px Arial,sans-serif;text-align:center}
 .dot{width:9px;height:9px;border-radius:50%}
 .legend{display:flex;flex-wrap:wrap;gap:14px;margin-top:12px;font:12px Arial,sans-serif;color:#6b5a45}
 .legend i{display:inline-block;width:14px;height:14px;vertical-align:-3px;margin-right:5px}
 /* controls */
 .exrow{display:flex;align-items:center;gap:14px;padding:10px 0;border-bottom:1px dotted var(--gold)}
 .exrow:last-of-type{border-bottom:0}
 .exrow .frame{flex:none}
 .slot{margin:3px 0;font:12px Arial,sans-serif;color:#6b5a45}
 .slot span{display:inline-block;width:68px}
 .chip{font:12px Arial,sans-serif;padding:4px 10px;margin-right:4px;border:1px solid var(--gold);background:transparent;
       color:var(--ink);cursor:pointer;border-radius:2px}
 .chip:hover{background:#efe3c2}
 .chip.on{background:var(--ink);color:#f3e6c8;border-color:var(--ink)}
 .presets{margin-top:14px;font:13px Arial,sans-serif}
 .presets button{font:italic 14px Georgia,serif;background:none;border:0;border-bottom:1px solid var(--burgundy);
                 color:var(--burgundy);cursor:pointer;margin-right:16px;padding:0 0 1px}
 /* itinerary ticket */
 .ticket{background:var(--paper);border:2px dashed var(--gold);padding:18px 22px;min-width:360px;box-shadow:0 6px 18px rgba(60,40,10,.12)}
 .ticket h2{border-bottom:0;text-align:center;letter-spacing:5px;margin-bottom:2px}
 .ticket .sub{text-align:center;font-style:italic;font-size:13px;color:#6b5a45;margin-bottom:12px}
 .stop{display:flex;align-items:center;gap:12px;padding:9px 0;border-top:1px dotted var(--gold)}
 .num{flex:none;width:26px;height:26px;border-radius:50%;color:#fff;font:bold 13px/26px Arial,sans-serif;text-align:center}
 .stop .name{font-size:17px}
 .stop .meta{font:12px Arial,sans-serif;color:#6b5a45}
 .people{letter-spacing:2px;font-size:11px}
 .plaque{margin-left:auto;font:11px Arial,sans-serif;letter-spacing:2px;text-transform:uppercase;padding:4px 9px;border:1px solid}
 .now{color:var(--green);border-color:var(--green)}.later{color:var(--burgundy);border-color:var(--burgundy)}
 .total{border-top:2px solid var(--ink);margin-top:6px;padding-top:10px;display:flex;justify-content:space-between;font-size:15px}
 .note{font:12px Arial,sans-serif;color:#6b5a45;margin-top:10px;line-height:1.5}
 .summary{background:#f1e6c8;border-left:4px solid var(--burgundy);padding:10px 14px;margin-bottom:10px;font:14px/1.7 Arial,sans-serif}
</style></head><body>
<header><div class="kicker">Gallery visit planner</div>
<h1>Smart Museum Tour Guide</h1>
<p>Crowd estimates by Bayes &middot; visit decision by MDP &middot; route by A*</p></header>
<main>
 <div class="placard"><h2>Floor plan</h2><div id="grid"></div>
  <div class="legend">
   <span><i style="background:var(--green)"></i>entrance</span>
   <span><i style="background:#f7efd8;border:3px solid #b8891f;width:16px;height:16px"></i>exhibit (number = visit order)</span>
   <span><i style="background:#5a4636"></i>wall</span>
   <span><i style="background:#8c2f39;border-radius:50%;width:9px;height:9px;vertical-align:1px"></i>route, one colour per leg</span>
  </div></div>
 <div class="placard" style="min-width:340px"><h2>Visitor counter readings</h2>
  <div id="controls"></div>
  <div class="presets">Try: <button onclick="preset(0)">Quiet morning</button><button onclick="preset(1)">Busy afternoon</button><button onclick="preset(2)">Mixed day</button><button onclick="preset(3)">Clear</button></div></div>
 <div class="ticket"><h2>Result</h2><div class="sub">your itinerary &middot; updates as readings change</div>
  <div id="result"></div></div>
</main>
<script>
const LEG=["#8c2f39","#b07d1a","#2f6f6b","#5b3f8c","#a0522d"];
const SHORT={Low:"Low",Medium:"Medium",High:"High"};
let CFG=null, STATE={};
async function init(){
  CFG=await (await fetch("/api/config")).json();
  CFG.exhibit_names.forEach(n=>STATE[n]=[null]);
  buildControls(); planTour();
}
function buildControls(){
  document.getElementById("controls").innerHTML=CFG.exhibit_names.map(n=>{
    const slots=[0].map(k=>`<div class="slot"><span>Reading</span>`+
      CFG.levels.map(l=>`<button class="chip ${STATE[n][k]===l?"on":""}" onclick="setReading('${n}',${k},'${l}')">${SHORT[l]}</button>`).join("")+`</div>`).join("");
    return `<div class="exrow"><div class="frame">${n}</div><div>${slots}</div></div>`;
  }).join("");
}
function setReading(n,k,l){ STATE[n][k]=STATE[n][k]===l?null:l; buildControls(); planTour(); }
function readings(){ const r={}; CFG.exhibit_names.forEach(n=>r[n]=STATE[n].filter(x=>x)); return r; }
function preset(i){
  const P=[[["Low"],["Low"],["Low"]],[["High","High"],["High"],["High","Medium"]],[["High"],["Low"],["Medium"]],[[],[],[]]][i];
  CFG.exhibit_names.forEach((n,k)=>{const v=P[k%P.length]; STATE[n]=[v[0]||null];});
  buildControls(); planTour();
}
function drawMap(plan){
  const owner={}, order={};
  if(plan) plan.tour.forEach((leg,i)=>{order[leg.exhibit]=i+1; leg.path.slice(1).forEach(p=>owner[p[0]+","+p[1]]=i);});
  const g=document.getElementById("grid");
  g.style.gridTemplateColumns=`repeat(${CFG.map[0].length},48px)`;
  g.innerHTML=CFG.map.map((row,r)=>[...row].map((ch,c)=>{
    if(ch==="#") return `<div class="t wall"></div>`;
    if(ch==="S") return `<div class="t door">IN</div>`;
    if(/[A-Z]/.test(ch)) return `<div class="t art"><div class="frame">${ch}</div>${order[ch]?`<div class="badge">${order[ch]}</div>`:""}</div>`;
    const k=r+","+c, base=(r+c)%2?"f1":"f0";
    if(k in owner){const col=LEG[owner[k]%LEG.length];
      return `<div class="t ${base}" style="background:${col}26"><div class="dot" style="background:${col}"></div></div>`;}
    return `<div class="t ${base}"></div>`;
  }).join("")).join("");
}
function people(p){const n=Math.round(p*10);return "●".repeat(n)+"○".repeat(10-n);}
async function planTour(){
  const res=await fetch("/api/plan",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({readings:readings()})});
  const d=await res.json();
  if(!res.ok){alert(d.error);return;}
  drawMap(d);
  const empty=CFG.exhibit_names.every(n=>STATE[n].every(x=>!x));
  const stops=d.tour.map((l,i)=>{
    const p=d.exhibits[l.exhibit].belief.Crowded, now=l.decision==="Visit Now";
    return `<div class="stop"><div class="num" style="background:${LEG[i%LEG.length]}">${i+1}</div>
      <div><div class="name">Exhibit ${l.exhibit}</div>
      <div class="meta"><span class="people">${people(p)}</span> &nbsp;P(crowded) ${p.toFixed(2)} &middot; ${l.steps} steps</div></div>
      <div class="plaque ${now?"now":"later"}">${now?"Visit now":"Visit later"}</div></div>`;
  }).join("");
  const route=d.tour.map(l=>l.exhibit).join(" → ");
  const crowd=Object.entries(d.exhibits).map(([n,i])=>n+" "+i.belief.Crowded.toFixed(2)).join(" · ");
  const nowList=d.tour.filter(l=>l.decision==="Visit Now").map(l=>l.exhibit).join(", ")||"none";
  const laterList=d.tour.filter(l=>l.decision!=="Visit Now").map(l=>l.exhibit).join(", ")||"none";
  const summary=`<div class="summary"><b>Route:</b> ${route} (${d.total_steps} steps)<br><b>Crowd estimate P(crowded):</b> ${crowd}<br><b>Decision:</b> now: ${nowList}; later: ${laterList}</div>`;
  document.getElementById("result").innerHTML=summary+stops+
    `<div class="total"><span>Total walking</span><b>${d.total_steps} steps</b></div>`+
    (d.unreachable.length?`<div class="note">Unreachable: ${d.unreachable.join(", ")}</div>`:"")+
    `<div class="note">`+(empty?"No sensor readings yet, so estimates equal the prior (0.40). ":"")+
    `The MDP (value iteration, ${d.mdp.iterations} iterations) says: go now only if P(crowded) is below 0.26.</div>`;
}
init();
</script></body></html>
"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            self._send(200, PAGE, "text/html")
        elif self.path == "/api/config":
            self._send(200, json.dumps({
                "map": DEFAULT_MAP,
                "levels": list(LEVELS),
                "exhibit_names": sorted(exhibits(DEFAULT_MAP)),
            }))
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        if self.path != "/api/plan":
            return self._send(404, json.dumps({"error": "not found"}))
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
            readings = payload.get("readings", {})
            if not isinstance(readings, dict):
                raise ValueError("'readings' must be an object")
            for name, vals in readings.items():
                if name not in exhibits(DEFAULT_MAP) or not isinstance(vals, list):
                    raise ValueError(f"Bad readings for exhibit {name!r}")
            self._send(200, json.dumps(plan_tour(DEFAULT_MAP, readings)))
        except (ValueError, json.JSONDecodeError) as e:
            self._send(400, json.dumps({"error": str(e)}))

    def log_message(self, *args):  # quiet console
        pass


def make_server(port=8000):
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = make_server(port)
    url = f"http://localhost:{port}"
    print("Smart Museum Tour Guide running at", url, "(Ctrl+C to stop)")
    try:
        webbrowser.open(url)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
