# Boilerplate — lane A/B docs page (extracted 2026-09-02 from docs.apps/2026-09-02-factchat-ops-informe.html)

Head:

```html
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
```

CSS (copy whole, then add only what the page needs):

```css
:root{--accent:#1F65FF;--accent-soft:#EDF2FF;--ink:#0F1115;--ink-2:#3F4552;--ink-3:#767D8D;--rule:#E1E4EA;--rule-2:#EFF1F5;--surface:#fff;--surface-2:#F7F8FA;--ok:#1A7F45;--ok-soft:#E8F7EE;--warn:#A35C11;--warn-soft:#FFF2E6;--bad:#B3261E;--bad-soft:#FDECEC}
*{box-sizing:border-box}
html{color-scheme:light}
body{margin:0;background:var(--surface);color:var(--ink);font-family:"Pretendard","Apple SD Gothic Neo","Noto Sans KR",-apple-system,sans-serif;font-size:13px;line-height:1.5;word-break:keep-all;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:44px 40px 32px}
.title-row{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
h1{font-size:26px;font-weight:700;letter-spacing:-.02em;margin:0;white-space:nowrap}
.sub{font-size:13px;font-weight:500;color:var(--ink-3)}
.rule{flex:1;height:2px;background:var(--accent);min-width:40px}
.meta{margin-top:10px;padding-bottom:14px;border-bottom:1px solid var(--rule);font-size:11px;font-weight:500;color:var(--ink-3)}
section{margin-top:56px}
section+section{margin-top:38px}
.zhead{display:flex;align-items:baseline;gap:12px;margin-bottom:14px}
.znum{font-size:11px;font-weight:700;letter-spacing:.08em;color:var(--accent);white-space:nowrap}
h2{font-size:15px;font-weight:700;letter-spacing:-.012em;margin:0;white-space:nowrap}
.zhead .hair{flex:1;height:1px;background:var(--rule)}
.note{font-size:11px;font-weight:500;color:var(--ink-3);margin:0 0 12px}
p{margin:0 0 10px;color:var(--ink-2);max-width:92ch;text-wrap:pretty}
.tw{overflow-x:auto}
table{width:100%;border-collapse:collapse;border:1px solid var(--rule);font-size:12.5px}
th{font-size:10.5px;font-weight:700;letter-spacing:.08em;color:var(--ink-3);text-align:left;padding:9px 12px;border-bottom:1px solid var(--rule);background:var(--surface-2);white-space:nowrap}
td{padding:9px 12px;border-bottom:1px solid var(--rule-2);color:var(--ink-2);vertical-align:top}
tr:last-child td{border-bottom:0}
td.k{color:var(--ink);font-weight:600;white-space:nowrap}
td.num{text-align:right;font-variant-numeric:tabular-nums;color:var(--ink);font-weight:700;white-space:nowrap}
.focal td{background:var(--accent-soft)}
.focal td.k{position:relative}
.focal td.k:before{content:"";position:absolute;left:0;top:8px;bottom:8px;width:2px;background:var(--accent)}
.new td{background:var(--ok-soft)}
.new td.k{position:relative}
.new td.k:before{content:"";position:absolute;left:0;top:8px;bottom:8px;width:2px;background:var(--ok)}
.soon td{background:var(--warn-soft)}
.soon td.k{position:relative}
.soon td.k:before{content:"";position:absolute;left:0;top:8px;bottom:8px;width:2px;background:var(--warn)}
td.k .pill{margin-right:6px;vertical-align:1px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border:1px solid var(--rule)}
.grid>div{padding:14px 16px;border-right:1px solid var(--rule-2)}
.grid>div:last-child{border-right:0}
.eyebrow{font-size:10.5px;font-weight:700;letter-spacing:.08em;color:var(--ink-3);margin-bottom:6px}
.big{font-size:22px;font-weight:700;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.big small{font-size:12px;font-weight:600;color:var(--ink-2);margin-left:3px}
ul{margin:0 0 10px;padding-left:17px;color:var(--ink-2)}
li{margin-bottom:5px;text-wrap:pretty}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:28px}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11.5px;background:var(--surface-2);border:1px solid var(--rule-2);border-radius:3px;padding:1px 5px;color:var(--ink)}
pre{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11.5px;line-height:1.55;background:var(--surface-2);border:1px solid var(--rule);padding:12px 14px;margin:0 0 10px;overflow-x:auto;color:var(--ink);white-space:pre-wrap;overflow-wrap:anywhere}
pre.chat{font-family:inherit;font-size:12.5px;background:var(--accent-soft);border-color:transparent}
.pill{display:inline-block;font-size:10.5px;font-weight:700;letter-spacing:.04em;padding:1px 7px;border-radius:3px;white-space:nowrap}
.pill.ok{background:var(--ok-soft);color:var(--ok)}
.pill.warn{background:var(--warn-soft);color:var(--warn)}
.pill.bad{background:var(--bad-soft);color:var(--bad)}
.pill.env{background:var(--accent-soft);color:var(--accent)}
.flow{display:grid;grid-template-columns:repeat(5,1fr);gap:0;border:1px solid var(--rule);counter-reset:step}
.flow>div{padding:12px 14px;border-right:1px solid var(--rule-2)}
.flow>div:last-child{border-right:0}
.flow>div:before{counter-increment:step;content:counter(step,decimal-leading-zero);display:block;font-size:10.5px;font-weight:700;letter-spacing:.08em;color:var(--accent);margin-bottom:4px}
.flow b{display:block;color:var(--ink);font-size:12.5px;margin-bottom:3px}
.flow span{font-size:11.5px;color:var(--ink-3)}
.flow .human{background:var(--accent-soft)}
.dev{margin-top:64px;padding-top:24px;border-top:2px solid var(--rule)}
footer{margin-top:52px;padding-top:14px;border-top:1px solid var(--rule);font-size:10.5px;color:var(--ink-3);display:flex;justify-content:space-between;gap:16px}
footer .conf{width:100%}
.foot-line{margin-bottom:6px}
@media (max-width:900px){.grid,.flow{grid-template-columns:1fr}.cols{grid-template-columns:1fr}.grid>div,.flow>div{border-right:0;border-bottom:1px solid var(--rule-2)}h1{white-space:normal}}
@page{size:A4 landscape;margin:12mm}
@media print{body{print-color-adjust:exact;-webkit-print-color-adjust:exact}.wrap{padding:0}section{break-inside:avoid}}
```

Furniture (copy the shape):

```html
<div class="wrap">
<div class="title-row"><h1>제목</h1><div class="sub">부제 · 부제</div><div class="rule"></div></div>
<div class="meta">문서 종류 <span>·</span> 2026-09-02 16:00 KST 기준 <span>·</span> 작성: 이름</div>

<section>
  <div class="zhead"><div class="znum">01</div><h2>구역 제목</h2><div class="hair"></div></div>
  <p class="note">이 구역의 기준(데이터 출처, 기간)을 한 줄로.</p>
  <div class="grid"> <div><div class="eyebrow">라벨</div><div class="big">38<small>대</small></div></div> … </div>
  <div class="tw"><table><tr><th>…</th></tr><tr class="focal"><td class="k">…</td><td>…</td></tr></table></div>
</section>

<footer><div class="conf">
  <div class="foot-line">본 문서는 마인드로직의 대외비 자료로, 무단 복제 및 배포를 금합니다.</div>
  <div style="display:flex;justify-content:space-between"><span>Confidential 기밀자료</span><span>© 2026. Mindlogic Inc. All Rights Reserved.</span></div>
</div></footer>
</div>
```

Classes: `.focal` (accent tick) · `.new` (ok) · `.soon` (warn) row states · `.pill.ok|warn|bad|env` · `.flow` five numbered steps, `.human` for the highlighted step · `.cols` two columns · `pre.chat` for a Slack utterance.
