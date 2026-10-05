"""romdiff.json → 비공개 비교 페이지 (영역마다 판들을 나란히 + 고르기(가져옴/버림/참고) + 비고, 고른 것은 페이지 db 에 저장)
  python3 romdiff_page.py work/romdiff.json OUT.html
원작 내용이 들어가므로 OUT 은 스크래치/비공개 페이지에만 (저장소에 안 올림). 발행: capabilities {db:{}, user:{}}
db: choices/<줄 id> = {area, key, pick, memo, at} (줄을 고를 때만 생김), areas/<영역 id> = {area, pick, memo, at} (영역 전체)"""
import hashlib, json, sys

src, out = sys.argv[1], sys.argv[2]
D = json.load(open(src))
labels = D['labels']
areas = []
for ai, (name, rows) in enumerate(D['areas'].items()):
    aid = 'a%02d' % ai
    rr = [[hashlib.md5((name + '|' + r['key']).encode()).hexdigest()[:12], r['key'], r['vals'], 1 if r['same'] else 0,
           [i for i in range(1, len(r['vals'])) if r['vals'][i] != r['vals'][0]]] for r in rows]   # [4] = 첫 판(1.4)과 다른 판 번호
    areas.append(dict(id=aid, name=name, rows=rr, diff=sum(1 for r in rr if 1 in r[4])))   # 탭 숫자 = 둘째 판(2.0)이 첫 판과 다른 줄
data = json.dumps(dict(labels=labels, areas=areas), ensure_ascii=False, separators=(',', ':'))
cols = ''.join('<th>%s</th>' % l for l in labels)
page = r'''<title>디지몬스터 판 비교</title>
<style>
:root{--bg:#f4f5f2;--card:#fff;--ink:#1d2321;--muted:#606a64;--line:#d9ddd6;--accent:#2f6f8f;--soft:#e3eef3;--take:#2e7d4f;--drop:#a33a2b;--ref:#8a6d1d;
--f-body:"IBM Plex Sans KR","Apple SD Gothic Neo","Malgun Gothic",sans-serif;--f-mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#141917;--card:#1c2320;--ink:#e5e9e6;--muted:#9aa49f;--line:#2f3a35;--accent:#7fb7d3;--soft:#1f3038;--take:#6fc493;--drop:#e08374;--ref:#d9b968;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#141917;--card:#1c2320;--ink:#e5e9e6;--muted:#9aa49f;--line:#2f3a35;--accent:#7fb7d3;--soft:#1f3038;--take:#6fc493;--drop:#e08374;--ref:#d9b968;color-scheme:dark}
body{background:var(--bg);color:var(--ink);font-family:var(--f-body);line-height:1.5;padding-inline:16px;padding-block:20px 56px}
main{max-width:1280px;margin:0 auto;display:flex;flex-direction:column;gap:16px}
h1{font-size:1.5rem;margin:0}.lede{color:var(--muted);margin:0;max-width:80ch}
.tabs{display:flex;flex-wrap:wrap;gap:6px}
.tab{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;padding:4px 12px;font:inherit;font-size:.88rem;cursor:pointer}
.tab[aria-selected="true"]{background:var(--accent);color:var(--bg);border-color:var(--accent)}
.tab .n{font-family:var(--f-mono);font-size:.78rem;opacity:.8;margin-left:4px}
section{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px 16px;min-width:0}
.bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:10px}
input[type=search],input.memo{box-sizing:border-box;min-width:0;padding:6px 9px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink);font:inherit}
input[type=search]{flex:1 1 220px}input.memo{width:100%;font-size:.82rem}
label.chk{font-size:.88rem;color:var(--muted);display:flex;gap:6px;align-items:center}
.scroll{overflow-x:auto;max-width:100%}
table{border-collapse:collapse;width:100%;font-size:.84rem}th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{background:var(--card);position:sticky;top:0;white-space:nowrap}td.k{font-family:var(--f-mono);font-size:.78rem;color:var(--muted);max-width:22ch;word-break:break-all}
td.v{min-width:16ch;max-width:44ch;white-space:pre-wrap;word-break:break-word}td.v.none{color:var(--muted);font-style:italic}
tr.same td.v{color:var(--muted)}td.v.chg{background:var(--soft)}
select{padding:6px 8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink);font:inherit}
.pick{display:flex;gap:4px;flex-wrap:wrap}
.pick button{border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:5px;padding:2px 8px;font:inherit;font-size:.8rem;cursor:pointer}
.pick button[aria-pressed="true"][data-p="take"]{background:var(--take);color:var(--card);border-color:var(--take)}
.pick button[aria-pressed="true"][data-p="drop"]{background:var(--drop);color:var(--card);border-color:var(--drop)}
.pick button[aria-pressed="true"][data-p="ref"]{background:var(--ref);color:var(--card);border-color:var(--ref)}
.areahead{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;margin-bottom:8px}
.areahead h2{font-size:1.1rem;margin:0}
.status{font-size:.82rem;color:var(--muted)}
button.more{margin-top:10px;border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:6px;padding:6px 12px;font:inherit;cursor:pointer}
</style>
<main>
<header>
<h1>디지몬스터 판 비교</h1>
<p class="lede">영역마다 판들을 나란히 놓고 줄마다 <b>가져옴 · 버림 · 참고</b>와 비고를 고릅니다. 영역 전체도 한 번에 고를 수 있습니다. 고른 것은 이 페이지에 저장되어 롬 세션이 읽고 반영합니다. 기본은 <b>2.0 이 1.4 와 다른 줄</b>만 보이고, 1.4 와 달라진 칸은 색으로 표시됩니다.</p>
<p class="status" id="st">저장 기능 확인 중…</p>
</header>
<nav class="tabs" id="tabs" aria-label="영역"></nav>
<section id="sec">
<div class="areahead"><h2 id="an"></h2>
<div><span class="status">영역 전체:</span> <span class="pick" id="apick"></span></div></div>
<input class="memo" id="amemo" placeholder="영역 전체 비고 (예: 음악은 우리 판 유지)" style="margin-bottom:10px">
<div class="bar"><input type="search" id="q" placeholder="찾기 (이름·지역·대사)" aria-label="찾기">
<select id="mode" aria-label="보기"><option value="1">2.0 이 1.4 와 다른 줄</option><option value="2">우리 판이 1.4 와 다른 줄</option><option value="any">어느 판이든 다른 줄</option><option value="all">모든 줄</option></select>
<label class="chk"><input type="checkbox" id="undec"> 안 고른 줄만</label>
<span class="status" id="cnt"></span></div>
<div class="scroll"><table><thead><tr><th>항목</th>COLS<th>고르기 · 비고</th></tr></thead><tbody id="tb"></tbody></table></div>
<button class="more" id="more" hidden>더 보기</button>
</section>
</main>
<script>
const D=DATA;
const PICKS=[['take','가져옴'],['drop','버림'],['ref','참고']];
let cur=D.areas[0].id, limit=200, db=null, canWrite=false, choices={}, areaPicks={};
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const area=()=>D.areas.find(a=>a.id===cur);
function tabs(){document.getElementById('tabs').innerHTML=D.areas.map(a=>{const n=a.rows.filter(r=>choices[r[0]]&&choices[r[0]].pick).length;
 return '<button class="tab" role="tab" data-id="'+a.id+'" aria-selected="'+(a.id===cur)+'">'+esc(a.name)+'<span class="n">2.0 바뀜 '+a.diff+(n?' · 고름 '+n:'')+'</span></button>'}).join('');}
function pickHTML(id,p,dis){return PICKS.map(([k,t])=>'<button type="button" data-id="'+id+'" data-p="'+k+'" aria-pressed="'+(p===k)+'"'+(dis?' disabled':'')+'>'+t+'</button>').join('');}
let pending=false;
function typing(){const a=document.activeElement;return a&&a.classList&&a.classList.contains('memo')&&a.id!=='amemo'}
function refresh(){if(typing()){pending=true;return}render()}
document.addEventListener('focusout',()=>{if(pending){pending=false;setTimeout(render,0)}});
function render(){tabs();const a=area();document.getElementById('an').textContent=a.name;
 const ap=areaPicks[a.id]||{};document.getElementById('apick').innerHTML=pickHTML('area:'+a.id,ap.pick,!canWrite);
 const am=document.getElementById('amemo');if(document.activeElement!==am)am.value=ap.memo||'';am.disabled=!canWrite;
 const q=document.getElementById('q').value.trim(),mode=document.getElementById('mode').value,und=document.getElementById('undec').checked;
 const okm=r=>mode==='all'||(mode==='any'?!r[3]:r[4].includes(+mode));
 const rows=a.rows.filter(r=>okm(r)&&(!q||(r[1]+' '+r[2].join(' ')).includes(q))&&(!und||!(choices[r[0]]&&choices[r[0]].pick)));
 document.getElementById('cnt').textContent=rows.length+'줄';
 document.getElementById('tb').innerHTML=rows.slice(0,limit).map(r=>{const c=choices[r[0]]||{};
  return '<tr class="'+(r[3]?'same':'')+'"><td class="k">'+esc(r[1])+'</td>'+r[2].map((v,i)=>'<td class="v'+(v==null?' none':'')+(r[4].includes(i)?' chg':'')+'">'+(v==null?'없음':esc(v))+'</td>').join('')+
  '<td><div class="pick">'+pickHTML(r[0],c.pick,!canWrite)+'</div><input class="memo" data-id="'+r[0]+'" value="'+esc(c.memo||'')+'" placeholder="비고"'+(canWrite?'':' disabled')+'></td></tr>'}).join('');
 document.getElementById('more').hidden=rows.length<=limit;}
async function save(id,patch){if(!db||!canWrite)return;
 try{if(id.startsWith('area:')){const aid=id.slice(5);const a=D.areas.find(x=>x.id===aid);const body=Object.assign({area:a.name,pick:'',memo:''},areaPicks[aid]||{},patch,{at:new Date().toISOString()});areaPicks[aid]=body;await db.doc('areas/'+aid).set(body);}
 else{let row=null,an='';for(const a of D.areas){const r=a.rows.find(x=>x[0]===id);if(r){row=r;an=a.name;break}}
  const body=Object.assign({area:an,key:row[1],pick:'',memo:''},choices[id]||{},patch,{at:new Date().toISOString()});choices[id]=body;await db.doc('choices/'+id).set(body);}
  document.getElementById('st').textContent='저장됨';}
 catch(e){document.getElementById('st').textContent='저장 안 됨 ('+(e&&e.code||'오류')+')';if(e&&e.code==='invalid_argument'){canWrite=false;render();}}}
document.addEventListener('click',e=>{const t=e.target.closest('.tab');if(t){cur=t.dataset.id;limit=200;render();return}
 const b=e.target.closest('.pick button');if(b&&!b.disabled){const id=b.dataset.id,p=b.dataset.p;const prev=id.startsWith('area:')?(areaPicks[id.slice(5)]||{}).pick:(choices[id]||{}).pick;save(id,{pick:prev===p?'':p});render();}});
let timers={};document.addEventListener('input',e=>{const m=e.target;
 if(m.classList.contains('memo')){const id=m.id==='amemo'?'area:'+cur:m.dataset.id;clearTimeout(timers[id]);timers[id]=setTimeout(()=>save(id,{memo:m.value}),700);}});
document.getElementById('q').addEventListener('input',()=>{limit=200;render()});
document.getElementById('mode').addEventListener('change',()=>{limit=200;render()});document.getElementById('undec').addEventListener('change',render);
document.getElementById('more').addEventListener('click',()=>{limit+=300;render()});
render();
(async()=>{const st=document.getElementById('st');
 try{db=window.claude&&await window.claude.use('db');}catch(e){db=null}
 if(!db){st.textContent='저장 기능이 없는 화면이라 보기만 됩니다.';return}
 let user=null;try{user=await window.claude.use('user')}catch(e){}
 const w=user&&user.can?await user.can('data.write'):null;canWrite=w!==false;
 st.textContent=canWrite?'고르면 바로 저장됩니다.':'보기 전용입니다 (고르기는 편집 권한이 있는 사람만).';
 db.collection('choices').onSnapshot(s=>{choices={};s.docs.forEach(d=>{choices[d.id]=d.data()});refresh()},e=>{st.textContent='불러오기 안 됨 ('+e.code+')'});
 db.collection('areas').onSnapshot(s=>{areaPicks={};s.docs.forEach(d=>{areaPicks[d.id]=d.data()});refresh()},()=>{});
 render();})();
</script>'''
page = page.replace('DATA', data).replace('COLS', cols)
open(out, 'w').write(page)
print('%s: 영역 %d, 줄 %d, %d KB' % (out, len(areas), sum(len(a['rows']) for a in areas), len(page) // 1024))
