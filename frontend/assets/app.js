/* ==========================================================================
   Librario – 프론트엔드 SPA (프레임워크 없음, 빌드 불필요)
   ========================================================================== */
'use strict';

/* ---------- 아이콘 ---------- */
const DUCK = `<svg viewBox="0 0 48 48" fill="none"><path d="M8 11c5-2 11-2 16 1 5-3 11-3 16-1v26c-5-2-11-2-16 1-5-3-11-3-16-1V11Z" fill="#f0b45a"/><path d="M24 13v26" stroke="#221a08" stroke-width="1.5" opacity="0.55"/><path d="M29 6h7v11l-3.5-2.4L29 17V6Z" fill="#d9973f"/></svg>`;
const IC = {
  home:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/></svg>',
  shelf:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 4h18"/><path d="M3 12h18"/><path d="M3 20h18"/><rect x="5" y="6" width="3" height="6"/><rect x="10" y="6" width="3" height="6"/><rect x="5" y="14" width="3" height="6"/><rect x="10" y="14" width="4" height="6"/></svg>',
  image:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="8.5" cy="10" r="1.5"/><path d="m5 17 4.5-4.5 3 3L16 12l3 3"/></svg>',
  list:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 6h13"/><path d="M8 12h13"/><path d="M8 18h13"/><path d="M3.5 6h.01"/><path d="M3.5 12h.01"/><path d="M3.5 18h.01"/></svg>',
  library:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="6" height="16" rx="1"/><rect x="10" y="4" width="5" height="16" rx="1"/><path d="M17 5l3.5.9-2.7 14.4-3.5-.9"/></svg>',
  search:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.2-3.2"/></svg>',
  gear:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 0 0-.1-1.3l2-1.5-2-3.4-2.3.9a7 7 0 0 0-2.2-1.3L14 2h-4l-.4 2.1a7 7 0 0 0-2.2 1.3l-2.3-.9-2 3.4 2 1.5A7 7 0 0 0 5 12c0 .4 0 .9.1 1.3l-2 1.5 2 3.4 2.3-.9a7 7 0 0 0 2.2 1.3L10 22h4l.4-2.1a7 7 0 0 0 2.2-1.3l2.3.9 2-3.4-2-1.5c.1-.4.1-.9.1-1.3Z"/></svg>',
  admin:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3 4 6v5c0 5 3.4 8.5 8 10 4.6-1.5 8-5 8-10V6z"/></svg>',
  back:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m15 5-7 7 7 7"/></svg>',
  close:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 6l12 12M18 6 6 18"/></svg>',
  star:'<svg viewBox="0 0 24 24" fill="currentColor"><path d="m12 3 2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 17l-5.2 2.9 1-5.8L3.5 9.2l5.9-.9z"/></svg>',
  check:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="m5 12 5 5L20 7"/></svg>',
  more:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
  book:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 5c0-1 1-2 2.5-2H20v16H6.5C5 19 4 20 4 21z"/><path d="M4 19h16"/></svg>',
  aa:'<svg viewBox="0 0 24 24" fill="currentColor"><text x="12" y="18" text-anchor="middle" font-size="17" font-weight="700">Aa</text></svg>',
};

/* ---------- 상태 ---------- */
const state = { user: null, libraries: [] };
let overlayStack = [];

/* ---------- 독서 환경설정 (localStorage) ---------- */
const PREF_KEY = 'librario_prefs_v1';
const HOME_SECTIONS = [
  {id:'fav_series',    label:'즐겨찾기',            key:'favorite_series',         kind:'series', more:'fav-series'},
  {id:'continue',      label:'이어보기',            key:'continue_reading',        kind:'book',   more:'reading-books'},
  {id:'read_books',    label:'최근 읽은 책',        key:'recently_read_books',     kind:'book',   more:'read-books'},
  {id:'read_series',   label:'최근 읽은 시리즈',    key:'recently_read_series',    kind:'series', more:'read-series'},
  {id:'added_books',   label:'최근 추가된 책',      key:'recently_added_books',    kind:'book',   more:'added-books'},
  {id:'added_series',  label:'최근 추가된 시리즈',  key:'recently_added_series',   kind:'series', more:'added-series'},
  {id:'upd_series',    label:'최근 업데이트된 시리즈', key:'recently_updated_series', kind:'series', more:'updated-series'},
  {id:'upd_books',     label:'최근 업데이트된 책',  key:'recently_updated_books',  kind:'book',   more:'updated-books'},
];
const defaultPrefs = {
  comicMode: 'webtoon',   // webtoon | paged
  comicFit: 'width',      // width | height | contain | original
  comicZoom: 100,         // 50~300 (%)
  tapMode: 'lr',          // lr(좌우) | tb(상하) | off
  tapInvert: false,       // 좌우 반전(우철 만화)
  autoNext: true,         // 마지막에서 다음 권 자동 열기
  epubLite: 'auto',       // auto | always | never (대용량 EPUB 경량 리더)
  epubLiteMB: 60,         // 이 크기(MB)를 넘으면 경량 리더 사용
  epubPrefetch: 3,        // 읽는 동안 미리 받아둘 다음 조각 수 (0=끄기)
  fontSize: 110,          // %
  fontFamily: 'sans',     // sans | serif
  lineHeight: 1.7,
  theme: 'dark',          // light | sepia | dark
  epubFlow: 'paginated',  // paginated | scrolled
  homeOrder: HOME_SECTIONS.map(s=>s.id),
  homeHidden: [],
};
function loadPrefs(){ try{ return {...defaultPrefs, ...JSON.parse(localStorage.getItem(PREF_KEY)||'{}')}; }catch(e){ return {...defaultPrefs}; } }
function savePrefs(){ try{ localStorage.setItem(PREF_KEY, JSON.stringify(prefs)); }catch(e){} }
const prefs = loadPrefs();

/* ---------- DOM 헬퍼 ---------- */
function h(tag, attrs, ...kids){
  const e = document.createElement(tag);
  attrs = attrs || {};
  for (const k in attrs){
    const v = attrs[k];
    if (v == null || v === false) continue;
    if (k === 'html') e.innerHTML = v;
    else if (k === 'class') e.className = v;
    else if (k === 'style' && typeof v === 'object') Object.assign(e.style, v);
    else if (k === 'dataset') Object.assign(e.dataset, v);
    else if (k.slice(0,2) === 'on' && typeof v === 'function') e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v);
  }
  kids.flat().forEach(kid => {
    if (kid == null || kid === false) return;
    e.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  });
  return e;
}
const $ = sel => document.querySelector(sel);
function clear(node){ while(node.firstChild) node.removeChild(node.firstChild); return node; }

function toast(msg){
  const t = h('div', {class:'t'}, msg);
  $('#toast').append(t);
  setTimeout(()=>{ t.style.opacity='0'; t.style.transition='opacity .3s'; setTimeout(()=>t.remove(),300); }, 2200);
}
function fmtSize(b){
  if(!b) return '';
  const u=['B','KB','MB','GB']; let i=0; b=+b;
  while(b>=1024 && i<u.length-1){ b/=1024; i++; }
  return b.toFixed(b<10&&i>0?1:0)+u[i];
}
function fmtDate(iso){ if(!iso) return ''; const d=new Date(iso); return d.toLocaleDateString('ko-KR',{year:'2-digit',month:'2-digit',day:'2-digit'}); }
function esc(s){ return String(s==null?'':s); }

/* ---------- API ---------- */
async function api(path, opts){
  opts = opts || {};
  const init = { method: opts.method||'GET', headers:{}, credentials:'same-origin' };
  if (opts.body !== undefined){ init.headers['Content-Type']='application/json'; init.body=JSON.stringify(opts.body); }
  const res = await fetch(path, init);
  if (res.status === 401){ state.user=null; renderGate(); throw new Error('unauthorized'); }
  const ct = res.headers.get('content-type')||'';
  const data = ct.includes('application/json') ? await res.json() : await res.text();
  if (!res.ok){ const msg = (data && data.detail) ? data.detail : ('오류 '+res.status); throw new Error(msg); }
  return data;
}
const coverUrl = (type,id) => `/api/${type}/${id}/thumbnail`;

/* ==========================================================================
   부팅 & 게이트 (셋업 / 로그인)
   ========================================================================== */
async function boot(){
  try{
    const st = await api('/api/auth/status');
    if(!st.initialized){ return renderSetup(); }
    const me = await api('/api/auth/me');
    state.user = me;
    await loadLibraries();
    renderApp();
  }catch(e){
    if(String(e.message)!=='unauthorized') renderLogin();
  }
}
async function loadLibraries(){
  try{ state.libraries = await api('/api/libraries'); }catch(e){ state.libraries=[]; }
}

function gateCard(title, sub, formNode){
  return h('div',{class:'gate'},
    h('div',{class:'gate-card'},
      h('div',{class:'brand'}, h('span',{html:DUCK}), h('h1',{},'Librario')),
      h('p',{class:'sub'}, sub),
      formNode
    )
  );
}
function renderGate(){ renderLogin(); }

function renderSetup(){
  const err = h('div',{class:'err'});
  const u = h('input',{class:'input', placeholder:'관리자 아이디', autocomplete:'username'});
  const p = h('input',{class:'input', type:'password', placeholder:'비밀번호 (4자 이상)', autocomplete:'new-password'});
  const p2 = h('input',{class:'input', type:'password', placeholder:'비밀번호 확인', autocomplete:'new-password'});
  const submit = async ()=>{
    err.textContent='';
    if(p.value.length<4) return err.textContent='비밀번호는 4자 이상이어야 합니다.';
    if(p.value!==p2.value) return err.textContent='비밀번호가 일치하지 않습니다.';
    try{
      const r = await api('/api/auth/setup',{method:'POST',body:{username:u.value.trim(),password:p.value}});
      state.user = r.user; await loadLibraries(); renderApp();
    }catch(e){ err.textContent = e.message; }
  };
  const form = h('div',{},
    h('label',{class:'field'}, h('span',{},'관리자 아이디'), u),
    h('label',{class:'field'}, h('span',{},'비밀번호'), p),
    h('label',{class:'field'}, h('span',{},'비밀번호 확인'), p2),
    err,
    h('button',{class:'btn primary',style:{width:'100%',justifyContent:'center',marginTop:'6px'},onclick:submit},'관리자 계정 만들기')
  );
  [u,p,p2].forEach(i=>i.addEventListener('keydown',e=>{if(e.key==='Enter')submit();}));
  clear($('#root')).append(gateCard('설정','첫 관리자 계정을 만들어 시작하세요.',form));
  u.focus();
}

function renderLogin(){
  const err = h('div',{class:'err'});
  const u = h('input',{class:'input', placeholder:'아이디', autocomplete:'username'});
  const p = h('input',{class:'input', type:'password', placeholder:'비밀번호', autocomplete:'current-password'});
  const remember = h('input',{type:'checkbox', checked:'checked', style:{width:'16px',height:'16px'}});
  const submit = async ()=>{
    err.textContent='';
    try{
      const r = await api('/api/auth/login',{method:'POST',body:{username:u.value.trim(),password:p.value,remember:remember.checked}});
      state.user = r.user; await loadLibraries(); renderApp();
    }catch(e){ err.textContent = e.message; }
  };
  const form = h('div',{},
    h('label',{class:'field'}, h('span',{},'아이디'), u),
    h('label',{class:'field'}, h('span',{},'비밀번호'), p),
    h('label',{style:{display:'flex',alignItems:'center',gap:'8px',fontSize:'14px',margin:'2px 0 4px',cursor:'pointer'}},
      remember, h('span',{},'로그인 유지 (자동 로그인)')),
    err,
    h('button',{class:'btn primary',style:{width:'100%',justifyContent:'center',marginTop:'6px'},onclick:submit},'로그인')
  );
  [u,p].forEach(i=>i.addEventListener('keydown',e=>{if(e.key==='Enter')submit();}));
  clear($('#root')).append(gateCard('로그인','계정으로 로그인하세요.',form));
  u.focus();
}

/* ==========================================================================
   앱 셸 + 라우터
   ========================================================================== */
const TABS = [
  {id:'home', label:'홈', icon:IC.home, route:'#/home'},
  {id:'libraries', label:'라이브러리', icon:IC.shelf, route:'#/libraries'},
  {id:'library', label:'서재', icon:IC.library, route:'#/library'},
  {id:'search', label:'검색', icon:IC.search, route:'#/search'},
  {id:'settings', label:'설정', icon:IC.gear, route:'#/settings'},
];

function renderApp(){
  if(!location.hash || location.hash==='#/') location.hash='#/home';
  const root = clear($('#root'));
  const searchInput = h('input',{placeholder:'제목·작가·태그 검색', value:currentQuery(), onkeydown:e=>{
    if(e.key==='Enter'){ location.hash = '#/search?q='+encodeURIComponent(e.target.value.trim()); }
  }});
  const topbar = h('div',{class:'topbar'},
    h('div',{class:'logo'}, h('span',{html:DUCK}), h('span',{},'Librario')),
    h('div',{class:'search-wrap',style:window.innerWidth<820?{display:'none'}:null},
      h('span',{class:'ico',html:IC.search}), searchInput),
    h('div',{class:'grow'}),
    state.user.role==='admin' ? h('button',{class:'icon-btn',title:'관리',html:IC.admin,onclick:()=>location.hash='#/admin'}) : null,
    h('button',{class:'avatar',title:state.user.username,onclick:userMenu}, state.user.username.slice(0,1).toUpperCase())
  );
  const main = h('div',{class:'app-main',id:'view'}, h('div',{class:'spinner'}));
  const nav = h('div',{class:'bottom-nav',id:'nav'});
  root.append(topbar, main, nav);
  route();
}

function userMenu(){
  openSheet(h('div',{},
    h('h3',{}, state.user.username),
    h('p',{class:'muted',style:{margin:'2px 0 18px'}}, state.user.role==='admin'?'관리자':'사용자'),
    state.user.role==='admin'? h('button',{class:'btn',style:{width:'100%',justifyContent:'center',marginBottom:'10px'},onclick:()=>{closeOverlay();location.hash='#/admin';}},'관리자 페이지'):null,
    h('button',{class:'btn danger',style:{width:'100%',justifyContent:'center'},onclick:async()=>{
      await api('/api/auth/logout',{method:'POST'}); state.user=null; closeOverlay(); renderLogin();
    }},'로그아웃')
  ));
}

function currentQuery(){
  const m = location.hash.match(/[?&]q=([^&]*)/);
  return m ? decodeURIComponent(m[1]) : '';
}
function activeTab(){
  const hp = location.hash.slice(2);
  if(hp.startsWith('home')||hp.startsWith('list')) return 'home';
  if(hp.startsWith('libraries')) return 'libraries';
  if(hp.startsWith('library')||hp.startsWith('series')) return 'library';
  if(hp.startsWith('search')) return 'search';
  if(hp.startsWith('settings')) return 'settings';
  return 'home';
}
function renderNav(){
  const nav = $('#nav'); if(!nav) return; clear(nav);
  const at = activeTab();
  TABS.forEach(t=>{
    nav.append(h('a',{class:at===t.id?'active':'', href:t.route},
      h('span',{html:t.icon}), h('span',{},t.label)));
  });
}

let adminScanTimer = null;
let homeScanTimer = null;
const scrollMemory = {};   // 해시별 스크롤 위치
let lastHash = '';
async function route(){
  if(!state.user) return;
  if(adminScanTimer){ clearInterval(adminScanTimer); adminScanTimer=null; }
  if(homeScanTimer){ clearInterval(homeScanTimer); homeScanTimer=null; }
  renderNav();
  const old = $('#view'); if(!old) return;
  // 새 엘리먼트로 교체 → 이전 라우트의 늦게 끝난 비동기 렌더는 분리된 노드에 그려져 사라짐
  // (라이브러리 화면이 두 번 그려지던 문제 방지)
  const view = h('div',{class:'app-main',id:'view'}, h('div',{class:'spinner'}));
  // 떠나기 전 스크롤 위치 저장 (뒤로 왔을 때 그 자리로 복원)
  if(lastHash) scrollMemory[lastHash] = window.scrollY || 0;
  old.replaceWith(view);
  const hp = location.hash.slice(2);
  const restoreY = scrollMemory[location.hash] || 0;
  lastHash = location.hash;
  window.scrollTo(0,0);
  try{
    if(hp.startsWith('home')) await viewHome(view);
    else if(hp.startsWith('libraries')) await viewLibraries(view);
    else if(hp.startsWith('library')) await viewLibrary(view);
    else if(hp.startsWith('list')) await viewList(view);
    else if(hp.startsWith('series/')) await viewSeries(view, +hp.split('/')[1]);
    else if(hp.startsWith('search')) await viewSearch(view);
    else if(hp.startsWith('settings')) await viewSettings(view);
    else if(hp.startsWith('admin')) await viewAdmin(view);
    else await viewHome(view);
    if(restoreY){
      // 이미지·목록이 배치된 뒤 복원 (두 번 시도해 레이아웃 지연에 대비)
      requestAnimationFrame(()=>{
        window.scrollTo(0, restoreY);
        setTimeout(()=>window.scrollTo(0, restoreY), 120);
      });
    }
  }catch(e){
    if(String(e.message)!=='unauthorized')
      clear(view).append(h('div',{class:'center-pad'}, '문제가 발생했습니다: '+e.message));
  }
}
window.addEventListener('hashchange', ()=>{ if(overlayStack.length===0) route(); });

/* ---------- 오버레이(시트/뷰어) + 뒤로가기 통합 ---------- */
function openOverlay(node){
  overlayStack.push(node);
  document.body.append(node);
  history.pushState({ov:overlayStack.length},'');
  document.body.style.overflow='hidden';
}
function closeOverlay(){
  if(overlayStack.length===0) return;
  history.back(); // popstate 에서 실제 제거
}
function popOverlay(){
  const node = overlayStack.pop();
  if(node){ if(node._onClose) try{node._onClose();}catch(e){} node.remove(); }
  if(overlayStack.length===0) document.body.style.overflow='';
}
window.addEventListener('popstate', ()=>{
  if(overlayStack.length>0) popOverlay();
  else route();
});
function openSheet(inner, onClose){
  const back = h('div',{class:'sheet-back', onclick:e=>{ if(e.target===back) closeOverlay(); }});
  const sheet = h('div',{class:'sheet'}, inner);
  back.append(sheet); back._onClose=onClose;
  openOverlay(back);
  return back;
}

/* ==========================================================================
   표지 카드
   ========================================================================== */
function coverNode(type, id, opts){
  opts = opts||{};
  const wrap = h('div',{class:'cover'});
  const img = h('img',{loading:'lazy', alt:'', onerror:function(){ this.style.display='none'; wrap.append(h('div',{class:'ph'}, opts.title||'')); }});
  img.src = coverUrl(type,id);
  wrap.append(img);
  if(opts.badge) wrap.append(h('div',{class:'badge'}, opts.badge));
  if(opts.count!=null) wrap.append(h('div',{class:'cnt'}, opts.count+'권'));
  if(opts.completed) wrap.append(h('div',{class:'done',html:IC.check}));
  else if(opts.percent!=null && opts.percent>0) wrap.append(h('div',{class:'prog'}, h('i',{style:{width:Math.min(100,opts.percent)+'%'}})));
  return wrap;
}
function bookCard(b){
  const pr = b.progress||{};
  const card = h('div',{class:'card', onclick:()=>openBook(b)},
    coverNode('books', b.id, {title:b.title, badge:b.format, percent:pr.percent, completed:pr.completed}),
    h('div',{class:'t'}, b.title),
    h('div',{class:'st'}, b.series_name && b.series_name!==b.title ? b.series_name : (b.author||''))
  );
  return card;
}
function seriesCard(s){
  const card = h('div',{class:'card', onclick:()=>location.hash='#/series/'+s.id},
    coverNode('series', s.id, {title:s.name, count:s.book_count,
      completed: s.book_count>0 && s.read_count>=s.book_count,
      percent: (s.book_count>0 && (s.read_count+s.in_progress_count)>0) ? Math.round((s.read_count/s.book_count)*100) : null}),
    h('div',{class:'t'}, s.favorite?h('span',{class:'fav-mark'},'★ '):null, s.name),
    h('div',{class:'st'}, s.book_count+'권', s.my_rating?h('span',{class:'card-rate'}, ' ★'+s.my_rating):null)
  );
  return card;
}
function hrow(title, items, node, moreType){
  if(!items || !items.length) return null;
  return h('div',{class:'row'},
    h('div',{class:'row-head'},
      h('h2',{}, title),
      moreType ? h('a',{class:'more-link', href:'#/list?type='+moreType}, '전체보기 ›') : null
    ),
    h('div',{class:'hscroll'}, items.map(node))
  );
}

/* ==========================================================================
   홈
   ========================================================================== */
function homeSectionsInOrder(){
  const byId = Object.fromEntries(HOME_SECTIONS.map(s=>[s.id,s]));
  const order = (prefs.homeOrder||[]).filter(id=>byId[id]);
  HOME_SECTIONS.forEach(s=>{ if(!order.includes(s.id)) order.push(s.id); }); // 새로 추가된 섹션 보정
  const hidden = new Set(prefs.homeHidden||[]);
  return order.map(id=>byId[id]).filter(s=>!hidden.has(s.id));
}

async function viewHome(view){
  const banner = h('div',{});          // 스캔 진행 알림
  const rowsWrap = h('div',{});
  clear(view).append(banner, rowsWrap);

  async function draw(){
    const data = await api('/api/home');
    const rows = homeSectionsInOrder()
      .map(s=>hrow(s.label, data[s.key], s.kind==='book'?bookCard:seriesCard, s.more))
      .filter(Boolean);
    clear(rowsWrap);
    if(!rows.length){
      rowsWrap.append(h('div',{class:'center-pad'},
        h('div',{class:'brand',style:{marginBottom:'14px'}}, h('span',{html:DUCK})),
        h('p',{},'아직 표시할 책이 없습니다.'),
        state.user.role==='admin'
          ? h('button',{class:'btn primary',style:{marginTop:'10px'},onclick:()=>location.hash='#/admin'},'라이브러리 추가하기')
          : h('p',{class:'muted'},'관리자가 라이브러리를 추가하면 여기에 표시됩니다.')
      ));
      return;
    }
    rows.forEach(r=>rowsWrap.append(r));
  }
  await draw();

  // ---- 스캔 중이면 실시간 반영 (새로고침 없이 새 책이 나타남) ----
  let lastKey = null, wasRunning = false;
  if(homeScanTimer){ clearInterval(homeScanTimer); homeScanTimer=null; }
  const tick = async ()=>{
    if(!location.hash.startsWith('#/home')){ clearInterval(homeScanTimer); homeScanTimer=null; return; }
    let s;
    try{ s = await api('/api/libraries/scan-status'); }catch(e){ return; }
    if(s.running){
      wasRunning = true;
      const pct = s.found? Math.round((s.processed/Math.max(s.found,1))*100):0;
      clear(banner).append(h('div',{class:'scan-banner'},
        h('div',{}, `${s.mode==='deep'?'심층 스캔':'스캔'} 중 · ${s.library_name||''} — 추가 ${s.added} · 처리 ${s.processed}/${s.found}`),
        h('div',{class:'bar'}, h('i',{style:{width:pct+'%'}}))
      ));
      // 새 책이 들어올 때마다 목록 갱신
      const key = `${s.added}|${s.updated}|${s.restored}`;
      if(key !== lastKey){ lastKey = key; draw().catch(()=>{}); }
    }else{
      clear(banner);
      if(wasRunning){ wasRunning=false; lastKey=null; draw().catch(()=>{}); }  // 완료 직후 최종 갱신
    }
  };
  tick();
  homeScanTimer = setInterval(tick, 3000);
}

/* 즐겨찾기 토글 (시리즈/책 공용) */
async function toggleFavorite(kind, item){
  const on = !item.favorite;
  try{
    await api(`/api/favorites/${kind}/${item.id}`, {method: on?'POST':'DELETE'});
    item.favorite = on;
    toast(on?'즐겨찾기에 추가했습니다.':'즐겨찾기에서 뺐습니다.');
    return on;
  }catch(e){ toast(e.message); return item.favorite; }
}

function favButton(kind, item){
  const btn = h('button',{class:'btn sm'+(item.favorite?' primary':''), onclick:async(e)=>{
    e.stopPropagation();
    const on = await toggleFavorite(kind, item);
    btn.className = 'btn sm'+(on?' primary':'');
    btn.textContent = on?'★ 즐겨찾기':'☆ 즐겨찾기';
  }}, item.favorite?'★ 즐겨찾기':'☆ 즐겨찾기');
  return btn;
}

/* ==========================================================================
   라이브러리 탭 (라이브러리별 보기)
   ========================================================================== */
async function viewLibraries(view){
  clear(view);
  await loadLibraries();
  const libs = state.libraries || [];
  if(!libs.length){
    view.append(h('div',{class:'center-pad'},
      h('p',{},'표시할 라이브러리가 없습니다.'),
      state.user.role==='admin'
        ? h('button',{class:'btn primary',style:{marginTop:'10px'},onclick:()=>location.hash='#/admin'},'라이브러리 추가하기')
        : h('p',{class:'muted'},'관리자에게 접근 권한을 요청하세요.')));
    return;
  }
  view.append(h('div',{class:'row-head',style:{marginBottom:'4px'}},
    h('h2',{},'라이브러리'),
    state.user.role==='admin' ? h('a',{class:'more-link',href:'#/admin'},'순서 변경 ›') : null));

  const grid = h('div',{class:'lib-grid'});
  libs.forEach(l=>{
    grid.append(h('div',{class:'lib-card', onclick:()=>{ libState.library=l.id; libState.tag=null; location.hash='#/library'; }},
      h('div',{class:'lib-card-name'}, l.name, l.restricted?h('span',{class:'badge-pill warn',style:{marginLeft:'6px'}},'제한'):null),
      h('div',{class:'lib-card-sub'}, `시리즈 ${l.series_count} · 책 ${l.book_count}`)
    ));
  });
  view.append(grid);
}

/* ==========================================================================
   전체보기 목록 (홈 섹션 → 더보기)
   ========================================================================== */
const LIST_TYPES = {
  'unread-books':  {title:'안 읽은 책', ep:'/api/books', kind:'book', sort:'created', order:'desc', extra:{progress:'unread'}},
  'fav-series':    {title:'즐겨찾기 시리즈', ep:'/api/series', kind:'series', sort:'favorite', order:'desc', extra:{favorite:'true'}},
  'fav-books':     {title:'즐겨찾기 책',     ep:'/api/books',  kind:'book',   sort:'favorite', order:'desc', extra:{favorite:'true'}},
  'added-books':   {title:'최근 추가된 책',       ep:'/api/books',  kind:'book',   sort:'created', order:'desc'},
  'updated-books': {title:'최근 업데이트된 책',   ep:'/api/books',  kind:'book',   sort:'updated', order:'desc'},
  'read-books':    {title:'최근 읽은 책',         ep:'/api/books',  kind:'book',   sort:'read',    order:'desc'},
  'reading-books': {title:'이어보기',             ep:'/api/books',  kind:'book',   sort:'read',    order:'desc', extra:{progress:'reading'}},
  'added-series':  {title:'최근 추가된 시리즈',   ep:'/api/series', kind:'series', sort:'created', order:'desc'},
  'updated-series':{title:'최근 업데이트된 시리즈',ep:'/api/series', kind:'series', sort:'updated', order:'desc'},
  'read-series':   {title:'최근 읽은 시리즈',     ep:'/api/series', kind:'series', sort:'read',    order:'desc'},
};
const BOOK_SORTS = [['favorite:desc','즐겨찾기 먼저'],['rating:desc','별점 높은순'],['read:desc','최근 읽은순'],
                    ['created:desc','최근 추가순'],['updated:desc','최근 업데이트순'],
                    ['title:asc','제목 오름차순'],['title:desc','제목 내림차순'],['size:desc','용량 큰순']];
const SERIES_SORTS = [['favorite:desc','즐겨찾기 먼저'],['rating:desc','별점 높은순'],['read:desc','최근 읽은순'],
                      ['created:desc','최근 추가순'],['updated:desc','최근 업데이트순'],
                      ['name:asc','이름 오름차순'],['name:desc','이름 내림차순'],['books:desc','권수 많은순']];

async function viewList(view){
  const m = location.hash.match(/[?&]type=([^&]*)/);
  const type = m ? decodeURIComponent(m[1]) : 'added-books';
  const cfg = LIST_TYPES[type] || LIST_TYPES['added-books'];
  let sort = cfg.sort, order = cfg.order, library = null, page = 1;
  let items = [], total = 0;

  clear(view);
  const sortOpts = cfg.kind==='book' ? BOOK_SORTS : SERIES_SORTS;
  const sortSel = h('select',{class:'input',style:{width:'auto'},onchange:e=>{
    const [s,o]=e.target.value.split(':'); sort=s; order=o; page=1; load(true);
  }}, ...sortOpts.map(([v,l])=>h('option',{value:v, selected:(sort+':'+order)===v}, l)));
  const libSel = h('select',{class:'input',style:{width:'auto',minWidth:'110px'},onchange:e=>{
    library = e.target.value?+e.target.value:null; page=1; load(true);
  }}, h('option',{value:''},'모든 라이브러리'),
     ...(state.libraries||[]).map(l=>h('option',{value:l.id}, l.name+(l.restricted?' 🔒':''))));

  const head = h('div',{style:{display:'flex',alignItems:'center',gap:'10px',marginBottom:'8px'}},
    h('button',{class:'icon-btn',html:IC.back,onclick:()=>location.hash='#/home'}),
    h('h2',{style:{margin:0,fontSize:'19px'}}, cfg.title));
  const countLbl = h('div',{class:'muted',style:{fontSize:'13px',margin:'0 0 8px'}},'');
  const gridWrap = h('div',{});
  const moreWrap = h('div',{style:{textAlign:'center',margin:'18px 0'}});
  view.append(head, h('div',{class:'filterbar'}, sortSel, libSel), countLbl, gridWrap, moreWrap);

  async function load(reset){
    if(reset){ items=[]; clear(gridWrap).append(h('div',{class:'spinner'})); }
    const p = new URLSearchParams();
    p.set('sort',sort); p.set('order',order); p.set('page',page); p.set('size','60');
    if(library) p.set('library', library);
    Object.entries(cfg.extra||{}).forEach(([k,v])=>p.set(k,v));
    let data;
    try{ data = await api(cfg.ep+'?'+p.toString()); }
    catch(e){ clear(gridWrap).append(h('div',{class:'center-pad'}, e.message)); return; }
    total = data.total;
    items = items.concat(data.items);
    clear(gridWrap);
    if(!items.length){ gridWrap.append(h('div',{class:'center-pad'},'표시할 항목이 없습니다.')); clear(moreWrap); countLbl.textContent=''; return; }
    const grid = h('div',{class:'grid'});
    items.forEach(it=> grid.append(cfg.kind==='series'?seriesCard(it):bookCard(it)));
    gridWrap.append(grid);
    countLbl.textContent = `${items.length} / ${total}개`;
    clear(moreWrap);
    if(items.length < total){
      moreWrap.append(h('button',{class:'btn',onclick:async(e)=>{
        e.target.disabled=true; e.target.textContent='불러오는 중…'; page+=1; await load(false);
      }},'더 보기'));
    }
  }
  load(true);
}

/* ==========================================================================
   서재 (라이브러리 브라우즈)
   ========================================================================== */
const libState = { mode:'series', library:null, tag:null, sort:'updated', order:'desc' };
async function viewLibrary(view){
  clear(view);
  // 필터바
  const libSel = h('select',{class:'input',style:{width:'auto',minWidth:'120px'},onchange:e=>{
    libState.library = e.target.value?+e.target.value:null;
    libState.tag = null; loadChips(); loadGrid();
  }},
    h('option',{value:''},'모든 라이브러리'),
    ...state.libraries.map(l=>h('option',{value:l.id, selected:libState.library===l.id}, l.name + (l.restricted?' 🔒':'')))
  );
  const sortSel = h('select',{class:'input',style:{width:'auto'},onchange:e=>{
    const [s,o]=e.target.value.split(':'); libState.sort=s; libState.order=o; loadGrid();
  }},
    h('option',{value:'updated:desc',selected:libState.sort==='updated'},'최근 업데이트순'),
    h('option',{value:'created:desc'},'최근 추가순'),
    h('option',{value:'name:asc'},'이름 오름차순'),
    h('option',{value:'name:desc'},'이름 내림차순'),
    h('option',{value:'books:desc'},'권수 많은순')
  );
  const seg = h('div',{class:'seg'},
    h('button',{class:libState.mode==='series'?'on':'', onclick:()=>{libState.mode='series';renderFilter();loadGrid();}},'시리즈'),
    h('button',{class:libState.mode==='books'?'on':'', onclick:()=>{libState.mode='books';renderFilter();loadGrid();}},'전체 책')
  );
  const filterbar = h('div',{class:'filterbar'}, seg, libSel, sortSel);
  const chipsWrap = h('div',{class:'chips-scroll'});
  const gridWrap = h('div',{});
  view.append(filterbar, chipsWrap, gridWrap);

  function renderFilter(){
    seg.children[0].className = libState.mode==='series'?'on':'';
    seg.children[1].className = libState.mode==='books'?'on':'';
  }

  // 태그 칩 — 현재 선택한 라이브러리의 태그만 표시
  async function loadChips(){
    try{
      const t = await api('/api/tags'+(libState.library?('?library='+libState.library):''));
      clear(chipsWrap);
      chipsWrap.append(h('span',{class:'chip'+(libState.tag===null?' active':''), onclick:()=>{libState.tag=null;refreshChips();loadGrid();}},'전체'));
      (t.tags||[]).slice(0,60).forEach(tag=>{
        chipsWrap.append(h('span',{class:'chip'+(libState.tag===tag.name?' active':''), onclick:()=>{
          libState.tag = libState.tag===tag.name?null:tag.name; refreshChips(); loadGrid();
        }}, tag.name, h('span',{class:'muted',style:{fontSize:'11px'}}, ' '+tag.count)));
      });
      if(!(t.tags||[]).length) chipsWrap.append(h('span',{class:'muted',style:{fontSize:'12.5px',padding:'4px'}},'이 라이브러리에는 태그가 없습니다.'));
    }catch(e){}
  }
  await loadChips();
  function refreshChips(){
    [...chipsWrap.children].forEach(c=>{
      const name = c.firstChild ? c.textContent.replace(/\s\d+$/,'').trim() : '';
      const isAll = c.textContent==='전체';
      c.className = 'chip'+((isAll&&libState.tag===null)||(!isAll&&libState.tag===name)?' active':'');
    });
  }

  async function loadGrid(){
    clear(gridWrap).append(h('div',{class:'spinner'}));
    const params = new URLSearchParams();
    if(libState.library) params.set('library', libState.library);
    if(libState.tag) params.set('tag', libState.tag);
    params.set('sort', libState.sort); params.set('order', libState.order); params.set('size','100');
    const ep = libState.mode==='series' ? '/api/series?' : '/api/books?';
    const data = await api(ep+params.toString());
    clear(gridWrap);
    if(!data.items.length){ gridWrap.append(h('div',{class:'center-pad'},'조건에 맞는 항목이 없습니다.')); return; }
    const grid = h('div',{class:'grid'});
    data.items.forEach(it=> grid.append(libState.mode==='series'?seriesCard(it):bookCard(it)));
    gridWrap.append(grid);
    if(data.total>data.items.length) gridWrap.append(h('p',{class:'muted',style:{textAlign:'center',marginTop:'16px',fontSize:'13px'}}, `${data.items.length} / ${data.total}개 표시`));
  }
  loadGrid();
}

/* ==========================================================================
   검색
   ========================================================================== */
async function viewSearch(view){
  clear(view);
  const q0 = currentQuery();
  let mode = 'series', tag = null, library = null;
  const input = h('input',{class:'input', placeholder:'제목·작가 검색 (초성 가능: ㄴㅎㅈㅁ)', value:q0});
  const modeSeg = h('div',{class:'seg'},
    h('button',{class:'on',onclick:()=>{mode='series';go();}},'시리즈'),
    h('button',{onclick:()=>{mode='books';go();}},'책')
  );
  const libSel = h('select',{class:'input',style:{width:'auto',minWidth:'110px'},onchange:e=>{
    library = e.target.value?+e.target.value:null; loadTags(); go();
  }}, h('option',{value:''},'모든 라이브러리'),
     ...(state.libraries||[]).map(l=>h('option',{value:l.id}, l.name+(l.restricted?' 🔒':''))));

  let onlyFav = false, minRating = 0;
  let pickedTags = [];                 // 다중 선택
  let pickedFmts = [];
  const tagFilter = h('input',{class:'input',placeholder:'태그 찾기',style:{maxWidth:'160px'}});
  const resetBtn = h('button',{class:'btn sm',onclick:()=>{
    pickedTags=[]; pickedFmts=[]; onlyFav=false; minRating=0; tag=null;
    tagFilter.value=''; rateSel.value='0';
    favChip.className='chip'; paintFmts(); loadTags(); go();
  }},'초기화');
  const FMTS = [['cbz','만화'],['zip','만화(zip)'],['pdf','PDF'],['epub','EPUB'],['txt','텍스트']];
  const fmtBar = h('div',{class:'chips-scroll'});
  function paintFmts(){
    clear(fmtBar);
    FMTS.forEach(([v,label])=>{
      const on = pickedFmts.includes(v);
      fmtBar.append(h('span',{class:'chip'+(on?' active':''),onclick:()=>{
        pickedFmts = on ? pickedFmts.filter(x=>x!==v) : pickedFmts.concat(v);
        paintFmts(); go();
      }}, label));
    });
  }
  let onlyUnread = false;
  const unreadChip = h('span',{class:'chip', onclick:()=>{
    onlyUnread=!onlyUnread; unreadChip.className='chip'+(onlyUnread?' active':''); go();
  }},'📖 안 읽은 것만');
  const favChip = h('span',{class:'chip', onclick:()=>{
    onlyFav=!onlyFav; favChip.className='chip'+(onlyFav?' active':''); go();
  }},'★ 즐겨찾기만');
  const rateSel = h('select',{class:'input',style:{width:'auto'},onchange:e=>{
    minRating = +e.target.value; go();
  }}, h('option',{value:'0'},'별점 전체'),
     ...[5,4,3,2,1].map(v=>h('option',{value:String(v)}, `★${v} 이상`)));
  const tagBar = h('div',{class:'chips-scroll'});
  const results = h('div',{});
  view.append(
    h('div',{class:'filterbar'}, h('div',{style:{flex:'1',minWidth:'180px'}}, input), modeSeg, libSel),
    h('div',{class:'filterbar',style:{marginTop:'-2px'}}, favChip, unreadChip, rateSel, resetBtn),
    h('div',{class:'row-head',style:{margin:'6px 2px 4px'}}, h('h2',{style:{fontSize:'14px'}},'형식')),
    fmtBar,
    h('div',{class:'row-head',style:{margin:'8px 2px 4px'}}, h('h2',{style:{fontSize:'14px'}},'태그'), tagFilter),
    tagBar, results);

  let timer=null;
  input.addEventListener('input', ()=>{ clearTimeout(timer); timer=setTimeout(go, 300); });
  input.addEventListener('keydown', e=>{ if(e.key==='Enter'){clearTimeout(timer);go();} });

  async function loadTags(){
    clear(tagBar).append(h('span',{class:'muted',style:{fontSize:'12px',padding:'4px'}},'태그 불러오는 중…'));
    try{
      const t = await api('/api/tags'+(library?('?library='+library):''));
      clear(tagBar);
      allTags = t.tags||[];
      drawTags();
      if(!(t.tags||[]).length) tagBar.append(h('span',{class:'muted',style:{fontSize:'12.5px',padding:'4px'}},'태그가 없습니다.'));
    }catch(e){ clear(tagBar); }
  }
  let allTags = [];
  function drawTags(){
    const q = (tagFilter.value||'').trim().toLowerCase();
    const sel = allTags.filter(t=>pickedTags.includes(t.name));
    const rest = allTags.filter(t=>!pickedTags.includes(t.name) &&
                                   (!q || t.name.toLowerCase().includes(q)));
    clear(tagBar);
    // 선택한 태그를 항상 앞에 고정 → 다시 찾을 필요 없음
    sel.concat(rest.slice(0, q?200:80)).forEach(tg=>{
      const on = pickedTags.includes(tg.name);
      tagBar.append(h('span',{class:'chip'+(on?' active':''), onclick:()=>{
        pickedTags = on ? pickedTags.filter(x=>x!==tg.name) : pickedTags.concat(tg.name);
        drawTags(); go();
      }}, (on?'✓ ':'')+tg.name, h('span',{class:'muted',style:{fontSize:'11px'}}, ' '+tg.count)));
    });
    if(!tagBar.children.length) tagBar.append(h('span',{class:'muted',style:{fontSize:'12.5px',padding:'4px'}},'일치하는 태그가 없습니다.'));
  }
  function paintTags(){ drawTags(); }

  async function go(){
    const q = input.value.trim();
    modeSeg.children[0].className = mode==='series'?'on':'';
    modeSeg.children[1].className = mode==='books'?'on':'';
    if(location.hash.indexOf('search')>=0) history.replaceState(null,'','#/search?q='+encodeURIComponent(q));
    if(!q && !tag && !onlyFav && !minRating && !onlyUnread){
      clear(results).append(h('div',{class:'center-pad'},'검색어(초성도 가능: ㄴㅎㅈㅁ)를 입력하거나 태그·즐겨찾기·별점으로 찾아보세요.'));
      return;
    }
    clear(results).append(h('div',{class:'spinner'}));
    const p = new URLSearchParams();
    if(q) p.set('search', q);
    if(pickedTags.length) p.set('tags', pickedTags.join(','));
    if(pickedFmts.length) p.set('fmt', pickedFmts.join(','));
    if(library) p.set('library', library);
    if(onlyFav) p.set('favorite','true');
    if(onlyUnread) p.set('progress','unread');
    if(minRating) p.set('min_rating', String(minRating));
    p.set('size','100');
    let data;
    try{ data = await api((mode==='series'?'/api/series?':'/api/books?')+p.toString()); }
    catch(e){ clear(results).append(h('div',{class:'center-pad'}, e.message)); return; }
    clear(results);
    const label = [q?`'${q}'`:null, ...pickedTags.map(t=>'#'+t),
                   pickedFmts.length?pickedFmts.join('/'):null, onlyFav?'즐겨찾기':null,
                   onlyUnread?'안 읽음':null,
                   minRating?`★${minRating} 이상`:null].filter(Boolean).join(' + ');
    if(!data.items.length){ results.append(h('div',{class:'center-pad'},`${label} 검색 결과가 없습니다.`)); return; }
    results.append(h('div',{class:'muted',style:{fontSize:'13px',margin:'0 2px 10px'}},
      `${label} · ${data.total}개`));
    const grid = h('div',{class:'grid'});
    data.items.forEach(it=>grid.append(mode==='series'?seriesCard(it):bookCard(it)));
    results.append(grid);
  }

  tagFilter.addEventListener('input', ()=>drawTags());
  paintFmts();
  loadTags();
  if(q0){ go(); input.focus(); }
  else{ clear(results).append(h('div',{class:'center-pad'},'검색어를 입력하거나 위의 태그를 선택하세요.')); input.focus(); }
}

/* ==========================================================================
   시리즈 상세
   ========================================================================== */
/* 시리즈 별점 (1~5, 같은 별을 다시 누르면 해제) */
function seriesStars(s){
  const wrap = h('div',{class:'stars',style:{marginTop:'6px'}});
  function paint(){
    clear(wrap);
    for(let i=1;i<=5;i++){
      wrap.append(h('span',{class:'star'+(i<=(s.my_rating||0)?' on':''), onclick:async()=>{
        const v = (s.my_rating === i) ? 0 : i;
        try{
          await api('/api/series/'+s.id+'/rating',{method:'PUT',body:{value:v}});
          s.my_rating = v; paint();
        }catch(e){ toast(e.message); }
      }}, '★'));
    }
    wrap.append(h('span',{class:'muted',style:{fontSize:'12px',marginLeft:'6px'}},
      s.my_rating? `내 별점 ${s.my_rating}` : '별점 없음'));
  }
  paint();
  return wrap;
}

async function viewSeries(view, id){
  const s = await api('/api/series/'+id);
  clear(view);
  const head = h('div',{class:'detail-head'},
    coverNode('series', s.id, {title:s.name, count:s.book_count}),
    h('div',{style:{flex:'1',minWidth:'0'}},
      h('h1',{}, s.name),
      h('div',{class:'detail-meta'}, `${s.library_name} · ${s.book_count}권 · 읽음 ${s.read_count}/${s.book_count}`),
      seriesStars(s),
      h('div',{style:{display:'flex',gap:'8px',flexWrap:'wrap',marginTop:'8px'}},
        s.books[0] ? h('button',{class:'btn primary',onclick:()=>openBook(pickResume(s))}, resumeLabel(s)) : null,
        favButton('series', s))
    )
  );
  // 태그 (편집 가능)
  const tagList = h('div',{class:'taglist'});
  const renderTags = ()=>{
    clear(tagList);
    s.tags.forEach(t=> tagList.append(h('span',{class:'chip', onclick:()=>{location.hash='#/library';libState.tag=t;} }, t)));
    tagList.append(h('span',{class:'chip', style:{borderStyle:'dashed'}, onclick:()=>addSeriesTag()}, '+ 태그'));
  };
  async function addSeriesTag(){
    const name = prompt('시리즈의 모든 책에 추가할 태그:');
    if(!name) return;
    try{ const r = await api('/api/series/'+s.id+'/tags',{method:'POST',body:{tag:name}}); s.tags=r.tags; renderTags(); toast('태그를 추가했습니다.'); }
    catch(e){ toast(e.message); }
  }
  renderTags();

  const list = h('div',{class:'booklist'});
  s.books.forEach(b=>{
    const pr = b.progress||{};
    list.append(h('div',{class:'book-row', onclick:()=>openBook(b)},
      h('img',{class:'mini', loading:'lazy', src:coverUrl('books',b.id), onerror:function(){this.style.visibility='hidden';}}),
      h('div',{class:'info'},
        h('div',{class:'bt'}, b.title),
        h('div',{class:'bs'}, [b.format.toUpperCase(), b.page_count?b.page_count+'p':null, fmtSize(b.file_size)].filter(Boolean).join(' · '))
      ),
      pr.completed ? h('span',{class:'rp',html:IC.check,style:{color:'var(--green)'}})
        : (pr.percent? h('span',{class:'rp'}, pr.percent+'%') : null),
      h('button',{class:'icon-btn',html:IC.more, onclick:e=>{e.stopPropagation();openBookSheet(b);}})
    ));
  });
  view.append(head, tagList, h('div',{class:'row-head',style:{marginTop:'8px'}}, h('h2',{},'수록 도서')), list);
}
function pickResume(s){
  const inprog = s.books.find(b=>b.progress && !b.progress.completed && b.progress.page>0);
  const unread = s.books.find(b=>!b.progress);
  return inprog || unread || s.books[0];
}
function resumeLabel(s){
  const b = pickResume(s);
  if(b.progress && b.progress.page>0 && !b.progress.completed) return '이어 읽기';
  return '읽기';
}

/* ==========================================================================
   책 상세 시트 (평점 · 태그 · 읽기)
   ========================================================================== */
async function openBookSheet(book){
  const b = await api('/api/books/'+book.id); // 최신 상태
  const inner = h('div',{});
  const stars = starRating(b.my_rating, async v=>{
    const r = await api('/api/books/'+b.id+'/rating',{method:'PUT',body:{value:v}});
    b.my_rating = r.my_rating; b.avg_rating=r.avg_rating;
    avgEl.textContent = b.avg_rating? `평균 ${b.avg_rating} (${r.rating_count})` : '';
  }, 'lg');
  const avgEl = h('span',{class:'muted',style:{fontSize:'13px'}}, b.avg_rating?`평균 ${b.avg_rating} (${b.rating_count})`:'');

  const tagWrap = h('div',{class:'taglist'});
  const renderTags = ()=>{
    clear(tagWrap);
    b.tags.forEach(t=> tagWrap.append(h('span',{class:'chip'}, t.name,
      t.source==='manual' ? h('span',{class:'x', onclick:async e=>{ e.stopPropagation();
        const r=await api(`/api/books/${b.id}/tags/${encodeURIComponent(t.name)}`,{method:'DELETE'}); b.tags=r.tags; renderTags();
      }},'✕') : null)));
    tagWrap.append(h('span',{class:'chip',style:{borderStyle:'dashed'},onclick:async()=>{
      const name=prompt('태그 추가:'); if(!name)return;
      try{const r=await api('/api/books/'+b.id+'/tags',{method:'POST',body:{tag:name}}); b.tags=r.tags; renderTags();}catch(e){toast(e.message);}
    }},'+ 태그'));
  };
  renderTags();

  const isAdmin = state.user && state.user.role==='admin';
  const descBox = h('p',{class:'muted',style:{fontSize:'13px',lineHeight:'1.5',margin:'4px 0 0',whiteSpace:'pre-wrap',maxHeight:'160px',overflow:'auto'}}, b.description||'');
  inner.append(
    h('div',{class:'sheet-head'},
      coverNode('books', b.id, {title:b.title, badge:b.format}),
      h('div',{style:{flex:'1',minWidth:'0'}},
        h('h3',{}, b.title),
        h('p',{class:'muted',style:{margin:'2px 0 4px',fontSize:'13px'}},
          [b.author, b.publisher, b.language, b.page_count?b.page_count+'페이지':null, fmtSize(b.file_size)].filter(Boolean).join(' · ')),
        h('div',{style:{display:'flex',alignItems:'center',gap:'10px',flexWrap:'wrap'}}, stars, avgEl)
      )
    ),
    b.description? descBox : null,
    tagWrap,
    isAdmin? h('div',{class:'modal-actions',style:{borderTop:'1px solid var(--line)',paddingTop:'8px'}},
      h('button',{class:'btn sm',onclick:async(ev)=>{
        const btn=ev.target; btn.disabled=true; btn.textContent='새로고침 중…';
        try{ const r=await api('/api/books/'+b.id+'/refresh',{method:'POST'}); toast('메타데이터를 새로고침했습니다.'); closeOverlay(); openBookSheet(r.book);}
        catch(e){ toast(e.message); btn.disabled=false; btn.textContent='메타 새로고침'; }
      }},'메타 새로고침'),
      h('button',{class:'btn sm',onclick:()=>openMetadataFetch(b)},'메타데이터 찾기')
    ) : null,
    h('div',{class:'modal-actions'},
      b.progress && b.progress.page>0 ? h('button',{class:'btn sm',onclick:async()=>{
        await api('/api/books/'+b.id+'/progress',{method:'DELETE'}); toast('진행 기록을 지웠습니다.'); closeOverlay();
      }},'기록 초기화') : null,
      h('a',{class:'btn sm',href:'/api/books/'+b.id+'/download',target:'_blank'},'다운로드'),
      h('button',{class:'btn primary',onclick:()=>{ closeOverlay(); openBook(b); }},
        (b.progress&&b.progress.page>0&&!b.progress.completed)?'이어 읽기':'읽기')
    )
  );
  openSheet(inner);
}

function starRating(value, onSet, size){
  const wrap = h('div',{class:'stars'+(size==='lg'?' lg':'')});
  let cur = value||0;
  const draw = (n)=>{ [...wrap.children].forEach((sv,i)=> sv.className = i<n?'on':''); };
  for(let i=1;i<=5;i++){
    const sv = document.createElement('span');
    sv.innerHTML = IC.star;
    sv.addEventListener('mouseenter',()=>draw(i));
    sv.addEventListener('mouseleave',()=>draw(cur));
    sv.addEventListener('click',()=>{ cur=(cur===i?0:i); draw(cur); onSet(cur); });
    wrap.append(sv);
  }
  draw(cur);
  return wrap;
}

/* ==========================================================================
   설정 (독서 환경설정)
   ========================================================================== */
async function viewSettings(view){
  clear(view);
  const card = (title, body) => h('div',{class:'list-card',style:{flexDirection:'column',alignItems:'stretch'}},
    h('div',{class:'lc-title',style:{marginBottom:'12px'}},title), body);

  const comicMode = segPick(['webtoon','paged'], ['웹툰(세로)','페이지'], prefs.comicMode, v=>{prefs.comicMode=v;savePrefs();});
  const fontFam = segPick(['sans','serif'], ['고딕','명조'], prefs.fontFamily, v=>{prefs.fontFamily=v;savePrefs();});
  const themePick = h('div',{style:{display:'flex',gap:'8px'}},
    ...[['light','#f5f0e6'],['sepia','#f3e9d2'],['dark','#16171c']].map(([id,c])=>
      h('button',{class:'theme-swatch'+(prefs.theme===id?' on':''),style:{background:c},
        onclick:e=>{prefs.theme=id;savePrefs();[...e.target.parentNode.children].forEach(b=>b.className='theme-swatch');e.target.className='theme-swatch on';}})));

  view.append(
    h('h2',{style:{margin:'2px 0 16px'}},'독서 설정'),
    card('만화 뷰어', h('div',{},
      settingRow('기본 보기 방식', comicMode),
      settingRow('기본 맞춤', segPick(['width','height','contain','original'],
        ['너비','높이','화면맞춤','원본'],prefs.comicFit,v=>{prefs.comicFit=v;savePrefs();}))
    )),
    card('화면 터치 이동', h('div',{},
      h('p',{class:'muted',style:{fontSize:'12.5px',margin:'0 0 12px'}},
        '화살표 대신 화면을 눌러 페이지를 넘깁니다. 가운데를 누르면 상·하단 바가 숨겨집니다.'),
      settingRow('터치 구역', segPick(['lr','tb','off'],['좌·우','위·아래','끄기'],
        prefs.tapMode||'lr', v=>{prefs.tapMode=v;savePrefs();})),
      settingRow('방향 반전', segPick([false,true],['보통','반전(우철)'],
        !!prefs.tapInvert, v=>{prefs.tapInvert=v;savePrefs();})),
      settingRow('다음 권 자동 열기', segPick([true,false],['켜기','끄기'],
        !!prefs.autoNext, v=>{prefs.autoNext=v;savePrefs();}))
    )),
    card('전자책 / 텍스트 뷰어', h('div',{},
      settingRow('글꼴', fontFam),
      settingRow('테마', themePick),
      settingRow('EPUB 보기', segPick(['paginated','scrolled'],['쪽넘김','스크롤'],prefs.epubFlow,v=>{prefs.epubFlow=v;savePrefs();})),
      settingRow('큰 EPUB 경량 모드', segPick(['auto','always','never'],['자동','항상','끄기'],
        prefs.epubLite||'auto', v=>{prefs.epubLite=v;savePrefs();})),
      settingRow('읽는 중 미리 받기', segPick([0,3,10],['끄기','3개','10개'],
        prefs.epubPrefetch||0, v=>{prefs.epubPrefetch=v;savePrefs();})),
      h('p',{class:'muted',style:{fontSize:'12px',margin:'2px 2px 0'}},
        `수백 MB~GB 짜리 EPUB 은 챕터 단위로만 받아 바로 열립니다. 기준 ${prefs.epubLiteMB||60}MB.`)
    )),
    card('홈 화면 구성', homeOrderEditor()),
    h('p',{class:'muted',style:{fontSize:'12.5px',marginTop:'8px'}},'글자 크기·줄 간격은 각 뷰어의 Aa 버튼에서 실시간으로 조절할 수 있습니다.')
  );
}

/* 홈 섹션 순서 변경 + 표시/숨김 */
function homeOrderEditor(){
  const wrap = h('div',{});
  const listWrap = h('div',{});
  const hint = h('p',{class:'muted',style:{fontSize:'12.5px',margin:'0 0 10px'}},
    '홈에 표시할 항목과 순서를 정합니다. ▲▼로 순서를 바꾸고 체크로 표시 여부를 정하세요.');

  function persist(){ savePrefs(); render(); }
  function currentOrder(){
    const byId = Object.fromEntries(HOME_SECTIONS.map(s=>[s.id,s]));
    const order = (prefs.homeOrder||[]).filter(id=>byId[id]);
    HOME_SECTIONS.forEach(s=>{ if(!order.includes(s.id)) order.push(s.id); });
    prefs.homeOrder = order;
    return order;
  }
  function render(){
    const order = currentOrder();
    const hidden = new Set(prefs.homeHidden||[]);
    clear(listWrap);
    order.forEach((id, idx)=>{
      const sec = HOME_SECTIONS.find(s=>s.id===id);
      const chk = h('input',{type:'checkbox', ...(hidden.has(id)?{}:{checked:'checked'}), onchange:()=>{
        const hs = new Set(prefs.homeHidden||[]);
        if(chk.checked) hs.delete(id); else hs.add(id);
        prefs.homeHidden = [...hs]; persist();
      }});
      listWrap.append(h('div',{class:'order-row'},
        chk,
        h('span',{style:{flex:'1',minWidth:0, opacity: hidden.has(id)?'0.45':'1'}}, sec.label),
        h('button',{class:'btn sm', disabled: idx===0?'disabled':null, onclick:()=>{
          const o=currentOrder(); [o[idx-1],o[idx]]=[o[idx],o[idx-1]]; prefs.homeOrder=o; persist();
        }},'▲'),
        h('button',{class:'btn sm', disabled: idx===order.length-1?'disabled':null, onclick:()=>{
          const o=currentOrder(); [o[idx+1],o[idx]]=[o[idx],o[idx+1]]; prefs.homeOrder=o; persist();
        }},'▼')
      ));
    });
  }
  render();
  wrap.append(hint, listWrap,
    h('button',{class:'btn sm',style:{marginTop:'10px'},onclick:()=>{
      prefs.homeOrder = HOME_SECTIONS.map(s=>s.id); prefs.homeHidden=[]; persist(); toast('기본값으로 되돌렸습니다.');
    }},'기본값으로'));
  return wrap;
}
function settingRow(label, control){
  return h('div',{class:'rs-row'}, h('span',{},label), h('div',{class:'rs-controls'}, control));
}
function segPick(values, labels, current, onSet){
  const wrap = h('div',{class:'seg-pick'});
  values.forEach((v,i)=> wrap.append(h('button',{class:current===v?'on':'', onclick:()=>{
    [...wrap.children].forEach(b=>b.className=''); wrap.children[i].className='on'; onSet(v);
  }}, labels[i])));
  return wrap;
}

/* ==========================================================================
   관리자
   ========================================================================== */
async function viewAdmin(view){
  if(state.user.role!=='admin'){ clear(view).append(h('div',{class:'center-pad'},'접근 권한이 없습니다.')); return; }
  clear(view);
  const TABDEF = [
    ['libraries','라이브러리', adminLibraries],
    ['scan','예약·규칙', adminScanSettings],
    ['trash','휴지통', adminTrash],
    ['tools','정리·백업', adminTools],
    ['analytics','분석', adminAnalytics],
    ['users','사용자', adminUsers],
  ];
  let tab='libraries';
  const tabs = h('div',{class:'admin-tabs'});
  TABDEF.forEach(([id,label])=> tabs.append(
    h('button',{class:id===tab?'on':'',onclick:()=>{tab=id;render();}},label)));
  const body = h('div',{});
  view.append(h('div',{style:{display:'flex',alignItems:'center',gap:'10px',marginBottom:'6px'}},
    h('button',{class:'icon-btn',html:IC.back,onclick:()=>location.hash='#/home'}), h('h2',{style:{margin:0}},'관리')), tabs, body);
  function render(){
    [...tabs.children].forEach((b,i)=>b.className = TABDEF[i][0]===tab?'on':'');
    const fn = (TABDEF.find(t=>t[0]===tab)||TABDEF[0])[2];
    fn(body);
  }
  render();
}

async function adminLibraries(body){
  clear(body).append(h('div',{class:'spinner'}));
  const libs = await api('/api/libraries');
  clear(body);
  // 스캔 상태
  const statusBox = h('div',{class:'scan-status'});
  const refreshStatus = async ()=>{
    try{
      const s = await api('/api/libraries/scan-status');
      clear(statusBox);
      // 대기열 표시
      api('/api/libraries/queue').then(q=>{
        const qw = statusBox.querySelector('.queue-box');
        if(qw) qw.remove();
        if(!q.queue || !q.queue.length) return;
        const box = h('div',{class:'queue-box'},
          h('div',{class:'muted',style:{fontSize:'12.5px',margin:'8px 0 4px'}},
            `대기열 ${q.queue.length}개`),
          ...q.queue.map((it,i)=> h('div',{class:'queue-row'},
            h('span',{class:'muted',style:{fontSize:'11px',minWidth:'18px'}}, String(i+1)),
            h('span',{style:{flex:'1',minWidth:0}}, it.name + (it.deep?' (심층)':'')),
            h('button',{class:'btn sm',title:'위로',disabled:i===0?'disabled':null,onclick:async()=>{
              const ids=q.queue.map(x=>x.library_id);
              [ids[i-1],ids[i]]=[ids[i],ids[i-1]];
              try{ await api('/api/libraries/queue/order',{method:'PUT',body:{ids}}); refreshStatus(); }catch(e){toast(e.message);}
            }},'▲'),
            h('button',{class:'btn sm danger',onclick:async()=>{
              try{ await api('/api/libraries/queue/'+it.library_id,{method:'DELETE'}); toast('대기열에서 제거'); refreshStatus(); }catch(e){toast(e.message);}
            }},'취소'))),
          h('button',{class:'btn sm',style:{marginTop:'6px'},onclick:async()=>{
            try{ await api('/api/libraries/queue/clear',{method:'POST'}); toast('대기열 비움'); refreshStatus(); }catch(e){toast(e.message);}
          }},'대기열 비우기'));
        statusBox.append(box);
      }).catch(()=>{});

      if(s.running){
        const pct = s.found? Math.round((s.processed/Math.max(s.found,1))*100):0;
        const modeLbl = s.mode==='deep'?'심층 스캔':'스캔';
        const cancelBtn = h('button',{class:'btn sm danger',style:{marginTop:'8px'},
          disabled: s.cancel_requested?'disabled':null,
          onclick:async(e)=>{ e.target.disabled=true; e.target.textContent='취소 중…';
            try{ await api('/api/libraries/scan-cancel',{method:'POST'}); toast('스캔 취소를 요청했습니다.'); }
            catch(err){ toast(err.message); }
          }}, s.cancel_requested?'취소 중…':'스캔 취소');
        statusBox.append(
          h('div',{}, `${modeLbl} 중: ${s.library_name||''} — 발견 ${s.found} · 처리 ${s.processed} · 추가 ${s.added} · 갱신 ${s.updated} · 휴지통 ${s.trashed||0} · 복구 ${s.restored||0}`),
          h('div',{class:'bar'}, h('i',{style:{width:pct+'%'}})),
          cancelBtn
        );
      }else{
        statusBox.append(h('div',{class:'muted'},
          s.cancelled? `스캔이 취소되었습니다 · 추가 ${s.added} · 갱신 ${s.updated} (사라진 파일 정리는 건너뜀)`
          : s.finished_at? `마지막 ${s.mode==='deep'?'심층 ':''}스캔 완료 · 추가 ${s.added} · 갱신 ${s.updated} · 휴지통 ${s.trashed||0} · 복구 ${s.restored||0}${s.file_errors?(' · 건너뛴 파일 '+s.file_errors+'개'):''}${s.error?(' · 오류: '+s.error):''}`
          : '대기 중'));
      }
    }catch(e){}
  };
  refreshStatus();
  if(adminScanTimer) clearInterval(adminScanTimer);
  adminScanTimer = setInterval(refreshStatus, 2000);

  const listWrap = h('div',{});
  let saveTimer = null;
  // 드래그로 순서 변경 — 화면을 다시 그리지 않고 DOM 만 옮긴 뒤 저장한다
  function persistOrder(){
    clearTimeout(saveTimer);
    saveTimer = setTimeout(async ()=>{
      const ids = [...listWrap.children].map(el=>+el.dataset.libid).filter(Boolean);
      try{
        await api('/api/libraries/order',{method:'PUT',body:{ids}});
        state.libraries = ids.map(id=>libs.find(l=>l.id===id)).filter(Boolean);
        toast('순서를 저장했습니다.');
      }catch(e){ toast(e.message); }
    }, 400);
  }
  function swapWith(el, delta){
    const sib = delta<0 ? el.previousElementSibling : el.nextElementSibling;
    if(!sib || !sib.dataset.libid) return;
    if(delta<0) listWrap.insertBefore(el, sib); else listWrap.insertBefore(sib, el);
    persistOrder();
  }
  let dragEl = null;
  // 모바일(터치)에서는 HTML5 드래그가 동작하지 않아 포인터 이벤트로 직접 처리한다
  function enableTouchDrag(card, handle){
    let startY=0, moved=false, holdTimer=null, active=false;
    const begin = ()=>{
      active=true; dragEl=card; card.classList.add('dragging');
      try{ navigator.vibrate && navigator.vibrate(15); }catch(e){}
    };
    handle.addEventListener('pointerdown', e=>{
      if(e.pointerType==='mouse') return;         // 마우스는 기본 드래그 사용
      startY=e.clientY; moved=false;
      handle.setPointerCapture(e.pointerId);
      holdTimer=setTimeout(begin, 180);            // 살짝 누르면 바로 잡힘
    });
    handle.addEventListener('pointermove', e=>{
      if(!active){
        if(Math.abs(e.clientY-startY)>10){ clearTimeout(holdTimer); }
        return;
      }
      e.preventDefault(); moved=true;
      const el=document.elementFromPoint(e.clientX, e.clientY);
      const t=el && el.closest ? el.closest('.list-card') : null;
      if(t && t!==dragEl && t.parentElement===listWrap){
        const r=t.getBoundingClientRect();
        const after=(e.clientY-r.top) > r.height/2;
        listWrap.insertBefore(dragEl, after ? t.nextSibling : t);
      }
    });
    const end = ()=>{
      clearTimeout(holdTimer);
      if(active){ card.classList.remove('dragging'); dragEl=null; active=false; if(moved) persistOrder(); }
    };
    handle.addEventListener('pointerup', end);
    handle.addEventListener('pointercancel', end);
  }
  libs.forEach((l, idx)=>{
    const card = h('div',{class:'list-card', draggable:'true', dataset:{libid:String(l.id)},
      ondragstart:e=>{ dragEl=e.currentTarget; e.currentTarget.classList.add('dragging');
                       e.dataTransfer.effectAllowed='move'; },
      ondragend:e=>{ e.currentTarget.classList.remove('dragging'); dragEl=null; persistOrder(); },
      ondragover:e=>{
        e.preventDefault();
        const t=e.currentTarget;
        if(!dragEl || dragEl===t) return;
        const r=t.getBoundingClientRect();
        const after = (e.clientY - r.top) > r.height/2;
        listWrap.insertBefore(dragEl, after ? t.nextSibling : t);
      }},
      h('div',{class:'drag-handle',title:'끌어서 순서 변경'},'⠿'),
      h('div',{style:{display:'flex',flexDirection:'column',gap:'2px'}},
        h('button',{class:'btn sm', title:'위로',
          onclick:e=>swapWith(e.currentTarget.closest('.list-card'),-1)},'▲'),
        h('button',{class:'btn sm', title:'아래로',
          onclick:e=>swapWith(e.currentTarget.closest('.list-card'),1)},'▼')),
      h('div',{class:'lc-main'},
        h('div',{class:'lc-title'}, l.name, ' ', l.restricted?h('span',{class:'badge-pill warn'},'제한'):(l.private?h('span',{class:'badge-pill warn'},'비공개'):h('span',{class:'badge-pill'},'공개'))),
        h('div',{class:'lc-sub'}, l.path),
        h('div',{class:'lc-sub'}, `시리즈 ${l.series_count} · 책 ${l.book_count}`)
      ),
      h('button',{class:'btn sm',onclick:async()=>{try{await api('/api/libraries/'+l.id+'/scan',{method:'POST'});toast('스캔 시작');refreshStatus();}catch(e){toast(e.message);}}},'스캔'),
      h('button',{class:'btn sm',title:'모든 파일 메타데이터·표지 재확인',onclick:async()=>{try{await api('/api/libraries/'+l.id+'/scan?deep=true',{method:'POST'});toast('심층 스캔 시작');refreshStatus();}catch(e){toast(e.message);}}},'심층'),
      h('button',{class:'btn sm',onclick:()=>editLibrary(l)},'수정'),
      h('button',{class:'btn sm danger',onclick:async()=>{
        if(!confirm(`'${l.name}' 라이브러리를 삭제할까요? (파일은 삭제되지 않습니다)`))return;
        await api('/api/libraries/'+l.id,{method:'DELETE'}); await loadLibraries(); adminLibraries(body);
      }},'삭제'),
      h('button',{class:'btn sm',title:'태그·제목 규칙을 기존 책에 다시 적용',onclick:async(e)=>{
        e.target.disabled=true; e.target.textContent='재적용 중…';
        try{ const r=await api('/api/libraries/'+l.id+'/reapply',{method:'POST'}); toast(r.message); }
        catch(err){ toast(err.message); }
        e.target.disabled=false; e.target.textContent='재적용';
      }},'재적용')
    );
    listWrap.append(card);
    const hnd = card.querySelector('.drag-handle');
    if(hnd) enableTouchDrag(card, hnd);
  });

  clear(body).append(
    statusBox,
    h('div',{style:{display:'flex',gap:'9px',marginBottom:'14px'}},
      h('button',{class:'btn primary',onclick:()=>addLibrary(body)},'+ 라이브러리 추가'),
      h('button',{class:'btn',onclick:async()=>{try{await api('/api/libraries/scan-all',{method:'POST'});toast('전체 스캔 시작');}catch(e){toast(e.message);}}},'전체 스캔'),
      h('button',{class:'btn',title:'모든 라이브러리의 모든 파일 재확인',onclick:async()=>{try{await api('/api/libraries/scan-all?deep=true',{method:'POST'});toast('전체 심층 스캔 시작');}catch(e){toast(e.message);}}},'전체 심층')
    ),
    libs.length? listWrap : h('div',{class:'center-pad'},'등록된 라이브러리가 없습니다.')
  );

  function addLibrary(){
    const name=h('input',{class:'input',placeholder:'표시 이름 (예: 웹툰-완결)'});
    const path=h('input',{class:'input',placeholder:'폴더 찾기로 선택하거나 직접 입력'});
    const restricted=h('input',{type:'checkbox'});
    const priv=h('input',{type:'checkbox'});
    const err=h('div',{class:'err'});

    // ---- 폴더 탐색기 ----
    const crumb=h('div',{style:{fontSize:'12.5px',fontWeight:'600',margin:'0 0 6px',wordBreak:'break-all',color:'var(--fg,#eee)'}});
    const listDiv=h('div',{style:{maxHeight:'240px',overflow:'auto',border:'1px solid var(--line,#333)',borderRadius:'8px',padding:'4px'}});
    const pickBtn=h('button',{class:'btn sm primary',style:{marginTop:'8px',display:'none'}},'이 폴더 선택');
    const browser=h('div',{style:{display:'none',margin:'6px 0 12px'}}, crumb, listDiv, pickBtn);
    let current='';

    const folderRow=(label, onClick, pickPath)=> h('div',{
        style:{display:'flex',alignItems:'center',gap:'8px',padding:'8px 8px',borderRadius:'6px',cursor:'pointer'},
        onmouseenter:e=>e.currentTarget.style.background='rgba(240,180,90,0.12)',
        onmouseleave:e=>e.currentTarget.style.background='transparent'},
      h('span',{onclick:onClick,style:{flex:'1',display:'flex',alignItems:'center',gap:'8px',minWidth:0}},
        h('span',{},label)),
      pickPath!=null? h('button',{class:'btn sm',style:{padding:'2px 8px',fontSize:'12px'},
        onclick:e=>{e.stopPropagation(); path.value=pickPath; browser.style.display='none'; toast('선택됨: '+pickPath);}},'선택') : null
    );

    async function loadDir(p){
      current=p;
      clear(listDiv).append(h('div',{class:'spinner'}));
      try{
        const d=await api('/api/libraries/browse'+(p?('?path='+encodeURIComponent(p)):''));
        crumb.textContent = d.is_root ? '📂 최상위 (마운트된 폴더)' : ('📂 '+d.path);
        pickBtn.style.display = d.is_root ? 'none' : 'inline-flex';
        clear(listDiv);
        if(!d.is_root){
          listDiv.append(folderRow('⬆  상위 폴더', ()=>loadDir(d.parent||''), null));
        }
        if(!d.entries.length){
          listDiv.append(h('div',{class:'muted',style:{padding:'10px',fontSize:'13px'}},
            d.is_root?'표시할 폴더가 없습니다. (BROWSE_ROOTS 환경변수로 지정할 수 있어요)':'하위 폴더가 없습니다.'));
        }
        d.entries.forEach(en=> listDiv.append(
          folderRow('📁  '+en.name, ()=>loadDir(en.path), en.path)));
      }catch(e){ clear(listDiv).append(h('div',{class:'err',style:{padding:'8px'}}, e.message)); }
    }
    pickBtn.onclick=()=>{ if(current){ path.value=current; browser.style.display='none'; toast('선택됨: '+current); } };

    const toggleBrowser=()=>{
      const showing = browser.style.display!=='none';
      browser.style.display = showing?'none':'block';
      if(!showing) loadDir(current||'');
    };

    openSheet(h('div',{},
      h('h3',{},'라이브러리 추가'),
      h('p',{class:'muted',style:{fontSize:'12.5px',margin:'4px 0 16px'}},'도커 볼륨으로 매핑한 폴더 안에서 선택하세요.'),
      h('label',{class:'field'},h('span',{},'이름'),name),
      h('label',{class:'field'},h('span',{},'폴더 경로'),path),
      h('button',{class:'btn sm',style:{margin:'-4px 0 4px'},onclick:toggleBrowser},'📁 폴더 찾기'),
      browser,
      h('label',{style:{display:'flex',alignItems:'center',gap:'8px',marginBottom:'6px'}},restricted,h('span',{},'제한(성인/R17) — 권한 있는 사용자만 접근')),
      h('label',{style:{display:'flex',alignItems:'center',gap:'8px',marginBottom:'10px'}},priv,h('span',{},'비공개 — 허용한 사용자만 접근 (성인물 아님)')),
      err,
      h('div',{class:'modal-actions'},
        h('button',{class:'btn',onclick:closeOverlay},'취소'),
        h('button',{class:'btn primary',onclick:async()=>{
          try{ await api('/api/libraries',{method:'POST',body:{name:name.value.trim(),path:path.value.trim(),restricted:restricted.checked,private:priv.checked}});
            await loadLibraries(); closeOverlay(); toast('추가됨 · 스캔을 시작합니다'); adminLibraries(body);
          }catch(e){ err.textContent=e.message; }
        }},'추가')
      )
    ));
  }
  function editLibrary(l){
    const name=h('input',{class:'input',value:l.name});
    const restricted=h('input',{type:'checkbox',checked:l.restricted});
    const priv2=h('input',{type:'checkbox',...(l.private?{checked:'checked'}:{})});
    const extraPaths=h('textarea',{class:'input',rows:'3',style:{fontFamily:'monospace',fontSize:'12px'},
      placeholder:'/Comic/추가폴더'});
    extraPaths.value=(l.extra_paths||[]).join('\n');
    const ls=((l.settings||{}).schedule)||{};
    const schedMode=h('select',{class:'input',style:{width:'auto'}},
      h('option',{value:'global', selected:ls.mode!=='custom'&&ls.mode!=='off'},'전역 설정 따름'),
      h('option',{value:'custom', selected:ls.mode==='custom'},'개별 설정'),
      h('option',{value:'off', selected:ls.mode==='off'},'예약 안 함'));
    const qh=h('input',{class:'input',type:'number',min:'1',max:'720',value:String(ls.quick_every_hours||6),style:{maxWidth:'72px'}});
    const dd=h('input',{class:'input',type:'number',min:'1',max:'365',value:String(ls.deep_every_days||7),style:{maxWidth:'72px'}});
    const dat=h('input',{class:'input',type:'time',value:ls.deep_at||'04:00',style:{maxWidth:'110px'}});
    openSheet(h('div',{},
      h('h3',{},'라이브러리 수정'),
      h('label',{class:'field',style:{marginTop:'12px'}},h('span',{},'이름'),name),
      h('label',{style:{display:'flex',alignItems:'center',gap:'8px'}},restricted,h('span',{},'제한(성인/R17)')),
      h('label',{style:{display:'flex',alignItems:'center',gap:'8px',marginTop:'6px'}},priv2,h('span',{},'비공개 — 허용한 사용자만 접근')),
      h('div',{style:{marginTop:'12px'}},
        h('div',{class:'muted',style:{fontSize:'12.5px',marginBottom:'4px'}},'추가 경로 (한 줄에 하나)'),
        extraPaths),
      h('div',{style:{marginTop:'12px'}},
        h('div',{class:'muted',style:{fontSize:'12.5px',marginBottom:'4px'}},'이 라이브러리 예약 스캔'),
        h('div',{style:{display:'flex',gap:'8px',flexWrap:'wrap',alignItems:'center'}},
          schedMode,
          h('span',{class:'muted',style:{fontSize:'12px'}},'빠른(시간)'), qh,
          h('span',{class:'muted',style:{fontSize:'12px'}},'심층(일)'), dd, dat)),
      h('div',{class:'modal-actions'},
        h('button',{class:'btn',onclick:closeOverlay},'취소'),
        h('button',{class:'btn primary',onclick:async()=>{
          await api('/api/libraries/'+l.id,{method:'PATCH',body:{name:name.value.trim(),restricted:restricted.checked,private:priv2.checked,
            extra_paths:extraPaths.value.split('\n').map(x=>x.trim()).filter(Boolean),
            settings:{schedule:{mode:schedMode.value,
              quick_enabled:schedMode.value==='custom', quick_every_hours:parseInt(qh.value)||6,
              deep_enabled:schedMode.value==='custom', deep_every_days:parseInt(dd.value)||7,
              deep_at:dat.value||'04:00'}}}});
          await loadLibraries(); closeOverlay(); adminLibraries(body);
        }},'저장')
      )
    ));
  }
}

async function adminUsers(body){
  clear(body).append(h('div',{class:'spinner'}));
  const [users, libs] = await Promise.all([api('/api/auth/users'), api('/api/libraries')]);
  clear(body);
  const listWrap = h('div',{});
  users.forEach(u=>{
    listWrap.append(h('div',{class:'list-card'},
      h('div',{class:'lc-main'},
        h('div',{class:'lc-title'}, u.username, ' ',
          u.role==='admin'?h('span',{class:'badge-pill ok'},'관리자'):h('span',{class:'badge-pill'},'사용자'),
          u.is_active?null:h('span',{class:'badge-pill warn'},'비활성')),
        h('div',{class:'lc-sub'}, u.granted_library_ids.length? ('제한 접근 '+u.granted_library_ids.length+'개') : '기본 접근')
      ),
      h('button',{class:'btn sm',onclick:()=>editUser(u)},'수정'),
      u.id!==state.user.id? h('button',{class:'btn sm danger',onclick:async()=>{
        if(!confirm(`'${u.username}' 사용자를 삭제할까요?`))return;
        await api('/api/auth/users/'+u.id,{method:'DELETE'}); adminUsers(body);
      }},'삭제'):null
    ));
  });
  clear(body).append(
    h('button',{class:'btn primary',style:{marginBottom:'14px'},onclick:()=>userForm()},'+ 사용자 추가'),
    listWrap
  );

  function libChecks(selected){
    const wrap=h('div',{style:{display:'flex',flexWrap:'wrap',gap:'8px',margin:'6px 0 12px'}});
    const restricted = libs.filter(l=>l.restricted || l.private);
    if(!restricted.length) return h('p',{class:'muted',style:{fontSize:'12.5px'}},'제한 라이브러리가 없습니다. (공개 라이브러리는 모두 접근 가능)');
    restricted.forEach(l=>{
      const cb=h('input',{type:'checkbox',checked:selected.includes(l.id),dataset:{id:l.id}});
      wrap.append(h('label',{class:'chip',style:{cursor:'pointer'}},cb,' ',l.name));
    });
    wrap._selected = ()=>[...wrap.querySelectorAll('input:checked')].map(c=>+c.dataset.id);
    return wrap;
  }

  function userForm(){
    const uname=h('input',{class:'input',placeholder:'아이디'});
    const pw=h('input',{class:'input',type:'password',placeholder:'비밀번호 (4자 이상)'});
    const role=h('select',{class:'input'},h('option',{value:'user'},'사용자'),h('option',{value:'admin'},'관리자'));
    const checks=libChecks([]);
    const err=h('div',{class:'err'});
    openSheet(h('div',{},
      h('h3',{},'사용자 추가'),
      h('label',{class:'field',style:{marginTop:'12px'}},h('span',{},'아이디'),uname),
      h('label',{class:'field'},h('span',{},'비밀번호'),pw),
      h('label',{class:'field'},h('span',{},'권한'),role),
      h('div',{},h('span',{class:'muted',style:{fontSize:'13px'}},'제한 라이브러리 접근'),checks),
      err,
      h('div',{class:'modal-actions'},
        h('button',{class:'btn',onclick:closeOverlay},'취소'),
        h('button',{class:'btn primary',onclick:async()=>{
          try{ await api('/api/auth/users',{method:'POST',body:{username:uname.value.trim(),password:pw.value,role:role.value,library_ids:checks._selected?checks._selected():[]}});
            closeOverlay(); adminUsers(body); toast('사용자를 추가했습니다.');
          }catch(e){ err.textContent=e.message; }
        }},'추가')
      )
    ));
  }
  function editUser(u){
    const pw=h('input',{class:'input',type:'password',placeholder:'변경 시에만 입력'});
    const role=h('select',{class:'input'},h('option',{value:'user',selected:u.role==='user'},'사용자'),h('option',{value:'admin',selected:u.role==='admin'},'관리자'));
    const active=h('input',{type:'checkbox',checked:u.is_active});
    const checks=libChecks(u.granted_library_ids);
    openSheet(h('div',{},
      h('h3',{},u.username+' 수정'),
      h('label',{class:'field',style:{marginTop:'12px'}},h('span',{},'새 비밀번호'),pw),
      h('label',{class:'field'},h('span',{},'권한'),role),
      h('label',{style:{display:'flex',alignItems:'center',gap:'8px',marginBottom:'8px'}},active,h('span',{},'활성 상태')),
      h('div',{},h('span',{class:'muted',style:{fontSize:'13px'}},'제한 라이브러리 접근'),checks),
      h('div',{class:'modal-actions'},
        h('button',{class:'btn',onclick:closeOverlay},'취소'),
        h('button',{class:'btn primary',onclick:async()=>{
          const patch={role:role.value,is_active:active.checked,library_ids:checks._selected?checks._selected():u.granted_library_ids};
          if(pw.value) patch.password=pw.value;
          try{ await api('/api/auth/users/'+u.id,{method:'PATCH',body:patch}); closeOverlay(); adminUsers(body); }
          catch(e){ toast(e.message); }
        }},'저장')
      )
    ));
  }
}

/* ==========================================================================
   뷰어 진입
   ========================================================================== */
/* ==========================================================================
   외부 메타데이터 찾기 오버레이 (관리자)
   ========================================================================== */
async function openMetadataFetch(book){
  const inner = h('div',{});
  let providers=[];
  try{ const r=await api('/api/metadata/providers'); providers=r.providers||[]; }catch(e){}
  if(!providers.length){ toast('메타데이터 공급자를 불러오지 못했습니다.'); return; }
  const sel = h('select',{class:'input',style:{maxWidth:'160px'}});
  providers.forEach(p=> sel.append(h('option',{value:p.id}, p.label)));
  const q = h('input',{class:'input',value:book.title||'',placeholder:'검색어'});
  const results = h('div',{style:{marginTop:'10px',display:'flex',flexDirection:'column',gap:'10px'}});
  const doSearch = async ()=>{
    clear(results).append(h('div',{class:'spinner'}));
    try{
      const r = await api(`/api/books/${book.id}/metadata/search?provider=${encodeURIComponent(sel.value)}&query=${encodeURIComponent(q.value.trim())}`);
      clear(results);
      if(!r.results || !r.results.length){ results.append(h('div',{class:'muted',style:{padding:'8px'}},'결과가 없습니다. (NAS 인터넷 연결/검색어를 확인하세요)')); return; }
      r.results.forEach(c=> results.append(candidateCard(book, c)));
    }catch(e){ clear(results).append(h('div',{class:'err'}, e.message)); }
  };
  q.addEventListener('keydown',e=>{if(e.key==='Enter')doSearch();});
  inner.append(
    h('h3',{style:{marginTop:0}},'메타데이터 찾기'),
    h('div',{style:{display:'flex',gap:'8px',flexWrap:'wrap'}}, sel, h('div',{style:{flex:'1',minWidth:'160px'}},q), h('button',{class:'btn primary',onclick:doSearch},'검색')),
    results
  );
  openSheet(inner);
  doSearch();
}

function candidateCard(book, c){
  const cover = c.cover_url ? h('img',{src:c.cover_url,style:{width:'54px',height:'76px',objectFit:'cover',borderRadius:'6px',flex:'0 0 auto',background:'#222'},referrerpolicy:'no-referrer'}) : h('div',{style:{width:'54px',height:'76px',borderRadius:'6px',background:'#222',flex:'0 0 auto'}});
  const fields = {description:'줄거리', author:'작가', tags:'태그', publisher:'출판사', language:'언어', title:'제목'};
  const checks = {};
  const chkRow = h('div',{style:{display:'flex',flexWrap:'wrap',gap:'8px',margin:'6px 0'}});
  Object.entries(fields).forEach(([k,lbl])=>{
    const has = k==='author'? (c.authors&&c.authors.length): k==='tags'? (c.tags&&c.tags.length): !!c[k];
    if(k==='title' && !c.title) return;
    const cb = h('input',{type:'checkbox', ...(has&&k!=='title'?{checked:'checked'}:{})});
    if(!has) cb.disabled=true;
    checks[k]=cb;
    chkRow.append(h('label',{style:{display:'flex',alignItems:'center',gap:'4px',fontSize:'12px',opacity:has?'1':'0.4'}}, cb, lbl));
  });
  const coverChk = h('input',{type:'checkbox', ...(c.cover_url?{checked:'checked'}:{})});
  if(!c.cover_url) coverChk.disabled=true;
  chkRow.append(h('label',{style:{display:'flex',alignItems:'center',gap:'4px',fontSize:'12px',opacity:c.cover_url?'1':'0.4'}}, coverChk, '표지'));
  const apply = h('button',{class:'btn sm primary',onclick:async(ev)=>{
    const flds=Object.entries(checks).filter(([k,cb])=>cb.checked).map(([k])=>k);
    ev.target.disabled=true; ev.target.textContent='적용 중…';
    try{
      const r=await api(`/api/books/${book.id}/metadata/apply`,{method:'POST',body:{provider:c.provider,external_id:c.id,fields:flds,replace_cover:coverChk.checked}});
      toast('적용됨: '+(r.applied.join(', ')||'변경 없음')); closeOverlay(); openBookSheet(r.book);
    }catch(e){ toast(e.message); ev.target.disabled=false; ev.target.textContent='적용'; }
  }},'적용');
  return h('div',{class:'list-card',style:{alignItems:'flex-start'}},
    cover,
    h('div',{class:'lc-main'},
      h('div',{class:'lc-title'}, c.title||'(제목없음)', c.year?h('span',{class:'muted',style:{fontSize:'12px',marginLeft:'6px'}},String(c.year)):null),
      c.authors&&c.authors.length? h('div',{class:'lc-sub'}, c.authors.join(', ')):null,
      c.description? h('div',{class:'lc-sub',style:{maxHeight:'54px',overflow:'hidden'}}, c.description):null,
      chkRow, apply
    )
  );
}

/* ==========================================================================
   관리 - 예약 스캔 & 태그 규칙
   ========================================================================== */
async function adminScanSettings(body){
  clear(body).append(h('div',{class:'spinner'}));
  let sc={}, tr={}, so={}, th={};
  try{ sc=await api('/api/scan/schedule'); }catch(e){}
  try{ tr=await api('/api/scan/tag-rules'); }catch(e){}
  try{ so=await api('/api/scan/options'); }catch(e){}
  try{ th=await api('/api/threads'); }catch(e){}
  clear(body);

  // ---- 메모리 설정 ----
  let mem={};
  try{ mem=await api('/api/memory'); }catch(e){}
  const cacheIn=h('input',{class:'input',type:'number',min:'2',max:'4096',
    value:String(mem.cache_mb||40),style:{maxWidth:'100px'}});
  const mmapIn=h('input',{class:'input',type:'number',min:'0',max:'8192',
    value:String(mem.mmap_mb||256),style:{maxWidth:'100px'}});
  const homeIn=h('input',{class:'input',type:'number',min:'0',max:'600',
    value:String(mem.home_cache_sec!=null?mem.home_cache_sec:20),style:{maxWidth:'100px'}});
  const ramTxt = mem.system_ram_mb
    ? `이 NAS 의 RAM ${(mem.system_ram_mb/1024).toFixed(1)}GB` : 'RAM 정보를 읽을 수 없습니다';
  const preset=(label, cm, mm, hc)=> h('button',{class:'btn sm',onclick:()=>{
    cacheIn.value=String(cm); mmapIn.value=String(mm); homeIn.value=String(hc);
  }}, label);
  body.append(
    h('h3',{style:{margin:'4px 0 8px'}},'메모리 설정'),
    h('p',{class:'muted',style:{fontSize:'13px',marginTop:0}},
      `${ramTxt}. 값을 올리면 목록·검색 같은 반복 조회가 빨라집니다. 저장하면 바로 적용됩니다.`),
    h('div',{class:'card-box'},
      h('div',{style:{display:'flex',gap:'8px',flexWrap:'wrap',marginBottom:'10px'}},
        preset('절약 (2GB급)', 40, 128, 20),
        preset('기본 (4~8GB)', 128, 512, 30),
        preset('넉넉 (16GB+)', 512, 2048, 60)),
      h('label',{class:'sched-row'}, h('span',{style:{flex:'1'}},'DB 페이지 캐시 (MB)'), cacheIn),
      h('label',{class:'sched-row'}, h('span',{style:{flex:'1'}},'DB mmap 크기 (MB)'), mmapIn),
      h('label',{class:'sched-row'}, h('span',{style:{flex:'1'}},'홈 화면 캐시 (초)'), homeIn),
      h('p',{class:'muted',style:{fontSize:'12px',margin:'8px 0 0'}},
        `현재 적용값: 캐시 ${(mem.applied&&mem.applied.cache_mb)||'?'}MB · mmap ${(mem.applied&&mem.applied.mmap_mb)||'?'}MB`),
      h('div',{style:{marginTop:'10px'}},
        h('button',{class:'btn primary',onclick:async(ev)=>{
          ev.target.disabled=true;
          try{
            const r=await api('/api/memory',{method:'PUT',body:{
              cache_mb:parseInt(cacheIn.value)||40, mmap_mb:parseInt(mmapIn.value)||256,
              home_cache_sec:parseInt(homeIn.value)||0}});
            toast(`적용됨 · 캐시 ${r.applied.cache_mb}MB · mmap ${r.applied.mmap_mb}MB`);
          }catch(e){ toast(e.message); }
          ev.target.disabled=false;
        }},'메모리 설정 저장'))));

  // ---- 데이터베이스 최적화 ----
  let dbi={};
  try{ dbi=await api('/api/db/info'); }catch(e){}
  const dbLbl = h('div',{class:'muted',style:{fontSize:'12.5px'}},
    `현재 크기 ${fmtSize(dbi.size||0)} · 마지막 최적화 ${dbi.last_optimize?fmtDateTime(dbi.last_optimize):'없음'}`);
  body.append(
    h('h3',{style:{margin:'4px 0 8px'}},'데이터베이스 최적화'),
    h('p',{class:'muted',style:{fontSize:'13px',marginTop:0}},
      '대량 스캔·삭제 후 빈 공간을 정리하고 조회 속도를 회복합니다. 기본 7일마다 자동 실행되며, 아래 버튼으로 즉시 실행할 수 있습니다.'),
    h('div',{class:'card-box'}, dbLbl,
      h('div',{style:{marginTop:'10px'}},
        h('button',{class:'btn primary',onclick:async(ev)=>{
          ev.target.disabled=true; ev.target.textContent='최적화 중…';
          try{
            const r=await api('/api/db/optimize',{method:'POST'});
            toast(`최적화 완료 · ${fmtSize(r.freed||0)} 확보`);
            const n=await api('/api/db/info');
            dbLbl.textContent=`현재 크기 ${fmtSize(n.size||0)} · 마지막 최적화 ${n.last_optimize?fmtDateTime(n.last_optimize):'방금'}`;
          }catch(e){ toast(e.message); }
          ev.target.disabled=false; ev.target.textContent='지금 최적화';
        }},'지금 최적화'))));

  // ---- 쓰레드 설정 (읽기용 / 작업용 분리) ----
  const readIn = h('input',{class:'input',type:'number',min:'0',max:'128',
    value:String(th.read_threads||0),style:{maxWidth:'90px'}});
  const scanIn = h('input',{class:'input',type:'number',min:'0',max:'32',
    value:String(th.scan_workers||0),style:{maxWidth:'90px'}});
  body.append(
    h('h3',{style:{margin:'4px 0 8px'}},'쓰레드 설정'),
    h('p',{class:'muted',style:{fontSize:'13px',marginTop:0}},
      `읽기용(책을 보는 요청)과 작업용(스캔)을 분리합니다. 0 이면 자동. 이 NAS 의 CPU 코어 ${th.cpu_count||'?'}개 · 자동 계산값 ${th.auto_scan_workers||'?'}개.`),
    h('div',{class:'card-box'},
      h('label',{class:'sched-row'}, h('span',{style:{flex:'1'}},'읽기용 쓰레드 (요청 처리)'), readIn),
      h('label',{class:'sched-row'}, h('span',{style:{flex:'1'}},'작업용 쓰레드 (스캔)'), scanIn),
      h('p',{class:'muted',style:{fontSize:'12px',margin:'8px 0 0'}},
        '스캔 중에도 책이 잘 열리게 하려면 작업용을 코어 수보다 낮게(예: 2~3) 두세요. 읽기용은 DB 연결 수에 맞춰 자동으로 제한됩니다.'),
      h('div',{style:{marginTop:'10px'}},
        h('button',{class:'btn primary',onclick:async(ev)=>{
          ev.target.disabled=true;
          try{
            const r=await api('/api/threads',{method:'PUT',body:{
              read_threads:parseInt(readIn.value)||0, scan_workers:parseInt(scanIn.value)||0}});
            toast(`저장됨 · 읽기 ${r.applied_read_threads||'자동'} / 작업 ${r.scan_workers||'자동'}`);
          }catch(e){ toast(e.message); }
          ev.target.disabled=false;
        }},'쓰레드 설정 저장'))
    ));

  // ---- 스캔 옵션 ----
  const OPT_DEFS = [
    ['thumbnails','표지 썸네일 생성'],
    ['page_count','페이지 수 계산 (만화·PDF)'],
    ['metadata','메타데이터 읽기 (ComicInfo·EPUB)'],
    ['filename_tags','파일명에서 태그 추출'],
    ['epub_structure','EPUB 목차·삽화 미리 분석'],
  ];
  const optBoxes = {};
  const optWrap = h('div',{class:'card-box'});
  OPT_DEFS.forEach(([k,label])=>{
    const cb = h('input',{type:'checkbox', ...(so[k]!==false?{checked:'checked'}:{})});
    optBoxes[k]=cb;
    optWrap.append(h('label',{class:'sched-row'}, cb, h('span',{},label)));
  });
  optWrap.append(h('div',{style:{marginTop:'10px'}},
    h('button',{class:'btn primary',onclick:async(ev)=>{
      ev.target.disabled=true;
      const payload={}; Object.entries(optBoxes).forEach(([k,cb])=>payload[k]=cb.checked);
      try{ await api('/api/scan/options',{method:'PUT',body:payload}); toast('스캔 옵션 저장됨'); }
      catch(e){ toast(e.message); }
      ev.target.disabled=false;
    }},'스캔 옵션 저장')));
  body.append(
    h('h3',{style:{margin:'4px 0 8px'}},'스캔 옵션'),
    h('p',{class:'muted',style:{fontSize:'13px',marginTop:0}},'스캔·예약 스캔에서 무엇을 미리 처리할지 정합니다. EPUB 목차·삽화를 미리 분석해 두면 책을 열 때 기다리지 않습니다.'),
    optWrap);

  // ---- 예약 스캔 ----
  const qOn=h('input',{type:'checkbox',...(sc.quick_enabled?{checked:'checked'}:{})});
  const qHours=h('input',{class:'input',type:'number',min:'1',max:'720',value:sc.quick_every_hours||6,style:{maxWidth:'90px'}});
  const dOn=h('input',{type:'checkbox',...(sc.deep_enabled?{checked:'checked'}:{})});
  const dDays=h('input',{class:'input',type:'number',min:'1',max:'365',value:sc.deep_every_days||7,style:{maxWidth:'90px'}});
  const dAt=h('input',{class:'input',type:'time',value:sc.deep_at||'04:00',style:{maxWidth:'120px'}});
  const saveSched=async(ev)=>{
    ev.target.disabled=true;
    try{ await api('/api/scan/schedule',{method:'PUT',body:{
      quick_enabled:qOn.checked, quick_every_hours:parseInt(qHours.value)||6,
      deep_enabled:dOn.checked, deep_every_days:parseInt(dDays.value)||7, deep_at:dAt.value||'04:00'}});
      toast('예약 스캔 저장됨'); }catch(e){ toast(e.message); } ev.target.disabled=false;
  };
  const lastLine = h('div',{class:'muted',style:{fontSize:'12px',marginTop:'6px'}},
    `마지막 빠른 스캔: ${sc.last_quick?fmtDateTime(sc.last_quick):'없음'} · 마지막 심층: ${sc.last_deep?fmtDateTime(sc.last_deep):'없음'}`);

  body.append(
    h('h3',{style:{margin:'4px 0 8px'}},'예약 스캔'),
    h('p',{class:'muted',style:{fontSize:'13px',marginTop:0}},'변경/신규 파일만 처리하는 빠른 스캔과, 모든 파일의 메타데이터·표지를 다시 확인하는 심층 스캔을 예약합니다.'),
    h('div',{class:'card-box'},
      h('label',{class:'sched-row'}, qOn, h('span',{},'빠른 예약 스캔 사용 · 매'), qHours, h('span',{},'시간마다')),
      h('label',{class:'sched-row'}, dOn, h('span',{},'심층 예약 스캔 사용 · 매'), dDays, h('span',{},'일마다'), dAt, h('span',{},'에')),
      lastLine,
      h('div',{style:{marginTop:'10px'}}, h('button',{class:'btn primary',onclick:saveSched},'예약 설정 저장'))
    ),
  );

  // ---- 태그 규칙 ----
  const trOn=h('input',{type:'checkbox',...(tr.enabled!==false?{checked:'checked'}:{})});
  const brOn=h('input',{type:'checkbox',...(tr.bracket_tags!==false?{checked:'checked'}:{})});
  const authOn=h('input',{type:'checkbox',...(tr.author_marker!==false?{checked:'checked'}:{})});
  const rangeOn=h('input',{type:'checkbox',...(tr.chapter_range!==false?{checked:'checked'}:{})});
  const rangeTagOn=h('input',{type:'checkbox',...(tr.chapter_range_tag?{checked:'checked'}:{})});
  const cleanOn=h('input',{type:'checkbox',...(tr.clean_title!==false?{checked:'checked'}:{})});
  const titleSrc=h('select',{class:'input',style:{width:'auto'}},
    h('option',{value:'auto',   selected:(tr.title_source||'auto')==='auto'},'자동 (내부 제목 우선)'),
    h('option',{value:'filename',selected:tr.title_source==='filename'},'파일명 우선'),
    h('option',{value:'embedded',selected:tr.title_source==='embedded'},'내부 제목만'));
  const exclIn=h('input',{class:'input',placeholder:'보관소, 자료실'});
  exclIn.value=(tr.exclude_folders||[]).join(', ');
  const kwArea=h('textarea',{class:'input',rows:'5',style:{fontFamily:'monospace',fontSize:'12px'},
    placeholder:'완결=완결\nBL=BL'}, );
  kwArea.value = (tr.keywords||[]).map(k=>`${k.match}=${k.tag||k.match}`).join('\n');
  const rxArea=h('textarea',{class:'input',rows:'4',style:{fontFamily:'monospace',fontSize:'12px'},
    placeholder:'정규식 => 태그 (한 줄에 하나)'});
  rxArea.value = (tr.regex||[]).map(r=> r.group? `${r.pattern} => group:${r.group}` : `${r.pattern} => ${r.tag||''}`).join('\n');
  const saveRules=async(ev)=>{
    ev.target.disabled=true;
    const keywords = kwArea.value.split('\n').map(l=>l.trim()).filter(Boolean).map(l=>{
      const i=l.indexOf('='); if(i<0) return {match:l,tag:l};
      return {match:l.slice(0,i).trim(), tag:l.slice(i+1).trim()||l.slice(0,i).trim()};
    });
    const regex = rxArea.value.split('\n').map(l=>l.trim()).filter(Boolean).map(l=>{
      const i=l.indexOf('=>'); const pat = i<0?l:l.slice(0,i).trim(); const rhs = i<0?'':l.slice(i+2).trim();
      if(rhs.startsWith('group:')) return {pattern:pat, group:parseInt(rhs.slice(6))||1};
      return {pattern:pat, tag:rhs};
    });
    try{ await api('/api/scan/tag-rules',{method:'PUT',body:{enabled:trOn.checked,bracket_tags:brOn.checked,author_marker:authOn.checked,
        chapter_range:rangeOn.checked,chapter_range_tag:rangeTagOn.checked,clean_title:cleanOn.checked,
        exclude_folders:exclIn.value.split(',').map(x=>x.trim()).filter(Boolean),
        title_source:titleSrc.value,keywords,regex}});
      toast('태그 규칙 저장됨 (다음 스캔부터 적용)'); }catch(e){ toast(e.message); } ev.target.disabled=false;
  };

  body.append(
    h('h3',{style:{margin:'20px 0 8px'}},'파일명 태그 규칙'),
    h('p',{class:'muted',style:{fontSize:'13px',marginTop:0}},'ComicInfo.xml 이 없어도 파일명에서 태그를 뽑습니다. 규칙 변경 후에는 심층 스캔(또는 새로고침)을 해야 반영됩니다.'),
    h('div',{class:'card-box'},
      h('label',{class:'sched-row'}, trOn, h('span',{},'파일명 태그 사용')),
      h('label',{class:'sched-row'}, brOn, h('span',{},'대괄호 [내용] 을 태그로 추출')),
      h('label',{class:'sched-row'}, authOn, h('span',{},'"@작가" 를 작가명으로 인식 (예: 제목 @릿테)')),
      h('label',{class:'sched-row'}, rangeOn, h('span',{},'"1-99" 을 화수 범위로 인식 (제목에서 분리)')),
      h('label',{class:'sched-row'}, rangeTagOn, h('span',{},'화수 범위를 태그로도 남기기 (1-99화·연재분)')),
      h('label',{class:'sched-row'}, cleanOn, h('span',{},'인식한 부분을 제목에서 제거')),
      h('div',{style:{marginTop:'10px'}},
        h('div',{class:'muted',style:{fontSize:'12px',marginBottom:'4px'}},'제목 출처'),
        titleSrc,
        h('p',{class:'muted',style:{fontSize:'11.5px',margin:'4px 0 0'}},
          'EPUB·ComicInfo 내부 제목이 권마다 다르게 적혀 순서가 뒤죽박죽이면 "파일명 우선"을 고르세요.')),
      h('div',{style:{marginTop:'10px'}},
        h('div',{class:'muted',style:{fontSize:'12px',marginBottom:'4px'}},
          '태그로 만들지 않을 폴더 이름 (쉼표로 구분 · 예: 보관소, 자료실)'), exclIn),
      h('div',{style:{marginTop:'8px'}}, h('div',{class:'muted',style:{fontSize:'12px',marginBottom:'4px'}},'키워드 규칙 (형식: 파일명포함어=태그)'), kwArea),
      h('div',{style:{marginTop:'8px'}}, h('div',{class:'muted',style:{fontSize:'12px',marginBottom:'4px'}},'정규식 규칙 (형식: 패턴 => 태그  또는  패턴 => group:1)'), rxArea),
      h('div',{style:{marginTop:'10px'}}, h('button',{class:'btn primary',onclick:saveRules},'태그 규칙 저장'))
    )
  );
}

/* ==========================================================================
   관리 - 중복 찾기 / 백업·복원
   ========================================================================== */
async function adminTools(body){
  clear(body);

  // ---- 중복 찾기 ----
  const dupWrap = h('div',{});
  const modeSel = h('select',{class:'input',style:{width:'auto'},onchange:()=>loadDups()},
    h('option',{value:'size_name'},'크기+파일명이 같은 것'),
    h('option',{value:'title'},'제목이 같은 것(넓게)'));
  body.append(
    h('h3',{style:{margin:'4px 0 8px'}},'중복 파일 찾기'),
    h('p',{class:'muted',style:{fontSize:'13px',marginTop:0}},
      '같은 작품이 여러 번 등록된 경우를 찾습니다. 정리해도 NAS 의 원본 파일은 삭제되지 않고 목록에서만 빠집니다(휴지통).'),
    h('div',{class:'filterbar'}, modeSel,
      h('button',{class:'btn',onclick:()=>loadDups()},'다시 검사')),
    dupWrap);

  async function loadDups(){
    clear(dupWrap).append(h('div',{class:'spinner'}));
    let j;
    try{ j = await api('/api/duplicates?mode='+modeSel.value); }
    catch(e){ clear(dupWrap).append(h('div',{class:'err'}, e.message)); return; }
    clear(dupWrap);
    if(!j.group_count){ dupWrap.append(h('div',{class:'center-pad'},'중복이 없습니다. 👍')); return; }
    dupWrap.append(h('div',{class:'muted',style:{fontSize:'13px',margin:'0 0 10px'}},
      `${j.group_count}개 그룹 · 중복으로 낭비되는 용량 약 ${fmtSize(j.wasted)}`));
    j.groups.forEach(g=>{
      const box = h('div',{class:'card-box',style:{marginBottom:'10px'}});
      box.append(h('div',{style:{fontWeight:'650',marginBottom:'6px'}}, g[0].title,
        h('span',{class:'muted',style:{fontSize:'12px',marginLeft:'6px'}}, `${g.length}건 · ${fmtSize(g[0].size)}`)));
      const boxes = [];
      g.forEach((b,i)=>{
        const cb = h('input',{type:'checkbox', ...(i>0?{checked:'checked'}:{})});
        boxes.push([cb,b]);
        box.append(h('label',{class:'order-row'}, cb,
          h('span',{style:{flex:'1',minWidth:0,fontSize:'12px',wordBreak:'break-all'}}, b.path),
          i===0?h('span',{class:'badge-pill'},'원본 추천'):null));
      });
      box.append(h('div',{style:{marginTop:'8px',display:'flex',gap:'8px'}},
        h('button',{class:'btn sm danger',onclick:async(ev)=>{
          const ids = boxes.filter(([cb])=>cb.checked).map(([,b])=>b.id);
          if(!ids.length){ toast('선택된 항목이 없습니다.'); return; }
          if(!confirm(`${ids.length}건을 휴지통으로 보낼까요? (원본 파일은 그대로 남습니다)`)) return;
          ev.target.disabled=true;
          try{ const r=await api('/api/duplicates/resolve',{method:'POST',body:{ids}});
            toast(`${r.count}건 정리됨`); loadDups(); }
          catch(e){ toast(e.message); ev.target.disabled=false; }
        }},'선택 항목 휴지통으로')));
      dupWrap.append(box);
    });
  }
  loadDups();

  // ---- 백업 / 복원 ----
  const fileIn = h('input',{type:'file',accept:'application/json,.json',style:{display:'none'},
    onchange:async(e)=>{
      const f = e.target.files && e.target.files[0];
      if(!f) return;
      try{
        const data = JSON.parse(await f.text());
        if(!confirm('백업을 복원하면 현재 별점·읽은 기록·즐겨찾기·수동 태그가 백업 내용으로 덮어써집니다. 계속할까요?')) return;
        const r = await api('/api/restore',{method:'POST',body:data});
        const a = r.applied;
        toast(`복원 완료 · 기록 ${a.progress} · 별점 ${a.ratings+a.series_ratings} · 즐겨찾기 ${a.favorites} · 태그 ${a.manual_tags}`);
      }catch(err){ toast('복원 실패: '+err.message); }
      e.target.value='';
    }});

  body.append(
    h('h3',{style:{margin:'22px 0 8px'}},'백업 / 복원'),
    h('p',{class:'muted',style:{fontSize:'13px',marginTop:0}},
      '별점·즐겨찾기·읽은 기록·수동 태그·설정을 파일로 저장합니다. 파일 경로를 기준으로 저장하므로 DB 를 새로 만들고 다시 스캔해도 되돌릴 수 있습니다. (책 파일 자체는 포함되지 않습니다)'),
    h('div',{class:'card-box'},
      h('div',{style:{display:'flex',gap:'8px',flexWrap:'wrap'}},
        h('button',{class:'btn primary',onclick:async(ev)=>{
          ev.target.disabled=true;
          try{
            const data = await api('/api/backup');
            const blob = new Blob([JSON.stringify(data,null,1)],{type:'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            const d = new Date().toISOString().slice(0,10);
            a.href=url; a.download=`librario-backup-${d}.json`; a.click();
            setTimeout(()=>URL.revokeObjectURL(url), 2000);
            const cn = data.counts;
            toast(`백업 저장됨 · 기록 ${cn.progress} · 별점 ${cn.ratings+cn.series_ratings} · 태그 ${cn.manual_tags}`);
          }catch(e){ toast(e.message); }
          ev.target.disabled=false;
        }},'백업 파일 내려받기'),
        h('button',{class:'btn',onclick:()=>fileIn.click()},'백업 파일에서 복원'),
        fileIn),
      h('p',{class:'muted',style:{fontSize:'12px',margin:'10px 0 0'}},
        '정기적으로 받아 NAS 밖(PC·클라우드)에도 보관해 두면 안전합니다.')));
}

/* ==========================================================================
   관리 - 휴지통
   ========================================================================== */
async function adminTrash(body){
  clear(body).append(h('div',{class:'spinner'}));
  let data={items:[],total:0};
  try{ data=await api('/api/trash'); }catch(e){}
  clear(body);
  const head = h('div',{style:{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:'8px'}},
    h('div',{}, h('h3',{style:{margin:0,display:'inline'}},'휴지통'), h('span',{class:'muted',style:{marginLeft:'8px',fontSize:'13px'}}, `${data.total}개`)),
    data.total? h('button',{class:'btn sm danger',onclick:async()=>{
      if(!confirm('휴지통을 비우면 항목이 영구 삭제됩니다. (원본 파일은 이미 없거나 이동됨) 계속할까요?'))return;
      try{ const r=await api('/api/trash/empty',{method:'POST'}); toast(`${r.deleted}개 영구 삭제`); adminTrash(body);}catch(e){toast(e.message);}
    }},'휴지통 비우기') : null
  );
  body.append(head, h('p',{class:'muted',style:{fontSize:'13px',marginTop:0}},'파일이 삭제/이동되면 여기로 옵니다. 별점·태그·진행률은 보존되며, 파일이 돌아오면 스캔 시 자동 복구됩니다. 영구 삭제는 여기서 수동으로만 이루어집니다.'));
  if(!data.items.length){ body.append(h('div',{class:'center-pad'},'휴지통이 비어 있습니다.')); return; }
  const list=h('div',{});
  data.items.forEach(it=>{
    list.append(h('div',{class:'list-card'},
      h('div',{class:'lc-main'},
        h('div',{class:'lc-title'}, it.title, ' ', h('span',{class:'badge-pill'}, it.format)),
        h('div',{class:'lc-sub'}, (it.series_name?it.series_name+' · ':'')+fmtSize(it.file_size)+(it.trashed_at?' · '+fmtDateTime(it.trashed_at):'')),
        h('div',{class:'lc-sub',style:{opacity:'0.7',fontSize:'11px'}}, it.path, it.file_exists?h('span',{class:'badge-pill',style:{marginLeft:'6px'}},'파일 있음'):null)
      ),
      it.file_exists? h('button',{class:'btn sm',onclick:async()=>{try{await api('/api/trash/'+it.id+'/restore',{method:'POST'});toast('복구됨');adminTrash(body);}catch(e){toast(e.message);}}},'복구') : null,
      h('button',{class:'btn sm danger',onclick:async()=>{
        if(!confirm(`'${it.title}' 을 영구 삭제할까요?`))return;
        try{await api('/api/trash/'+it.id,{method:'DELETE'});toast('영구 삭제됨');adminTrash(body);}catch(e){toast(e.message);}
      }},'영구삭제')
    ));
  });
  body.append(list);
}

/* ==========================================================================
   관리 - 분석
   ========================================================================== */
async function adminAnalytics(body){
  clear(body).append(h('div',{class:'spinner'}));
  let a=null;
  try{ a=await api('/api/analytics'); }catch(e){ clear(body).append(h('div',{class:'err'},e.message)); return; }
  clear(body);
  const t=a.totals;
  const stat=(label,val)=> h('div',{class:'stat-box'}, h('div',{class:'stat-num'}, val), h('div',{class:'stat-lbl'}, label));
  body.append(h('div',{class:'stat-grid'},
    stat('라이브러리', t.libraries), stat('시리즈', t.series), stat('책', t.books),
    stat('저장 용량', fmtSize(t.size)), stat('태그', t.tags), stat('휴지통', t.trashed),
    stat('최근 30일 추가', a.recent_added_30d), stat('내 완독', a.my_reading.completed), stat('읽는 중', a.my_reading.in_progress)
  ));

  const maxFmt = Math.max(1, ...a.by_format.map(f=>f.count));
  body.append(h('h3',{style:{margin:'18px 0 6px'}},'형식별'),
    h('div',{class:'card-box'}, ...a.by_format.map(f=> barRow(f.format.toUpperCase(), f.count, maxFmt))));

  if(a.by_library.length){
    body.append(h('h3',{style:{margin:'18px 0 6px'}},'라이브러리별'));
    const wrap=h('div',{class:'card-box'});
    a.by_library.forEach(l=> wrap.append(h('div',{class:'lib-stat-row'},
      h('div',{style:{flex:'1',minWidth:0}}, h('div',{style:{fontWeight:'600'}}, l.name, l.restricted?h('span',{class:'badge-pill warn',style:{marginLeft:'6px'}},'제한'):null),
        h('div',{class:'muted',style:{fontSize:'12px'}}, `시리즈 ${l.series} · 책 ${l.books}`)),
      h('div',{class:'muted',style:{fontSize:'13px'}}, fmtSize(l.size))
    )));
    body.append(wrap);
  }

  if(a.top_tags.length){
    const maxT=Math.max(1,...a.top_tags.map(x=>x.count));
    body.append(h('h3',{style:{margin:'18px 0 6px'}},'인기 태그'),
      h('div',{class:'card-box'}, ...a.top_tags.slice(0,12).map(x=> barRow(x.name, x.count, maxT))));
  }

  if(a.largest_books.length){
    body.append(h('h3',{style:{margin:'18px 0 6px'}},'가장 큰 파일'));
    const wrap=h('div',{class:'card-box'});
    a.largest_books.forEach(b=> wrap.append(h('div',{class:'lib-stat-row'},
      h('div',{style:{flex:'1',minWidth:0,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}, b.title),
      h('div',{class:'muted',style:{fontSize:'13px'}}, fmtSize(b.size)))));
    body.append(wrap);
  }
}

function barRow(label, val, max){
  return h('div',{class:'bar-row'},
    h('div',{class:'bar-label'}, label),
    h('div',{class:'bar-track'}, h('i',{style:{width:Math.round(val/max*100)+'%'}})),
    h('div',{class:'bar-val'}, String(val)));
}

function fmtDateTime(iso){ if(!iso) return ''; const d=new Date(iso); return d.toLocaleString('ko-KR',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}); }

function openBook(book){
  const fmt = book.format || book.fmt;
  if(fmt==='cbz' || fmt==='zip') openComicReader(book);
  else if(fmt==='epub'){
    // 큰 EPUB 은 파일 전체를 받으면 기기가 버티지 못하므로 챕터 단위 경량 리더 사용
    const big = (book.file_size||0) > (prefs.epubLiteMB||60)*1024*1024;
    if(prefs.epubLite==='never') openEpubReader(book);
    else if(big || prefs.epubLite==='always') openEpubLite(book);
    else openEpubReader(book);
  }
  else if(fmt==='pdf') openPdfReader(book);
  else if(fmt==='txt') openTxtReader(book);
  else toast('지원하지 않는 형식입니다.');
}
let progressTimer=null;
/* 다음 권 자동 이어읽기 — 마지막 페이지에서 한 번 더 넘기면 다음 권을 연다 */
async function offerNextBook(book, opener){
  if(!prefs.autoNext) return false;
  let nb = null;
  try{ nb = (await api(`/api/books/${book.id}/next`)).next; }catch(e){ return false; }
  if(!nb) { toast('시리즈의 마지막 권입니다.'); return false; }
  toast('다음 권으로 이동: ' + nb.title);
  closeOverlay();
  setTimeout(()=>{ (opener||openBook)(nb); }, 120);
  return true;
}

function saveProgress(bookId, payload){
  clearTimeout(progressTimer);
  progressTimer = setTimeout(()=>{ api('/api/books/'+bookId+'/progress',{method:'PUT',body:payload}).catch(()=>{}); }, 600);
}
function readerShell(title, opts){
  opts = opts||{};
  const top = h('div',{class:'reader-top'},
    h('button',{class:'icon-btn',html:IC.back,onclick:closeOverlay}),
    h('div',{class:'rt-title'}, title),
    ...(opts.actions||[])
  );
  const reader = h('div',{class:'reader'+(opts.themed?(' rtheme-'+prefs.theme):'')}, top);
  reader._onClose = opts.onClose;
  return {reader, top};
}

/* ---------- 만화 뷰어 ---------- */
/* 화면 터치로 이전/다음 이동. prefs.tapMode 로 좌우·상하·끄기 선택 */
function attachTapZones(reader, handlers){
  const mode = prefs.tapMode || 'lr';
  const old = reader.querySelector('.tap-zones');
  if(old) old.remove();
  if(mode === 'off') return null;
  const inv = !!prefs.tapInvert;
  const first = ()=> (inv ? handlers.next() : handlers.prev());
  const last  = ()=> (inv ? handlers.prev() : handlers.next());
  const zones = h('div',{class:'tap-zones '+(mode==='tb'?'tb':'lr')},
    h('div',{class:'z', onclick:first}),
    h('div',{class:'z mid', onclick:()=>handlers.toggleHud && handlers.toggleHud()}),
    h('div',{class:'z', onclick:last})
  );
  reader.append(zones);
  return zones;
}

async function openComicReader(book){
  const b = await api('/api/books/'+book.id);
  const pages = b.page_count||0;
  let mode = prefs.comicMode, fit = prefs.comicFit;
  let cur = (b.progress&&b.progress.page)||0;

  const settingsBtn = h('button',{class:'icon-btn',html:IC.gear});
  const {reader, top} = readerShell(b.title, {actions:[settingsBtn]});
  let curBookId = b.id;                       // 이어보기로 다음 화에 진입하면 갱신됨
  const titleEl = top.querySelector('.rt-title');
  const bodyWrap = h('div',{class:'reader-body'});
  const bottom = h('div',{class:'reader-bottom'});
  const slider = h('input',{type:'range',min:0,max:Math.max(0,pages-1),value:cur});
  const pnum = h('div',{class:'pnum'}, `${cur+1} / ${pages}`);
  bottom.append(h('div',{class:'pageslider'},
    h('button',{class:'icon-btn',html:IC.back,onclick:()=>goTo(cur-1)}),
    slider, pnum,
    h('button',{class:'icon-btn',style:{transform:'rotate(180deg)'},html:IC.back,onclick:()=>goTo(cur+1)})));
  reader.append(bodyWrap, bottom);
  openOverlay(reader);

  // 설정 패널
  const panel = comicSettingsPanel(mode, fit, (m,f)=>{ mode=m;fit=f; prefs.comicMode=m;prefs.comicFit=f;savePrefs(); rebuild(); });
  reader.append(panel.node);
  settingsBtn.addEventListener('click', ()=>panel.toggle());

  slider.addEventListener('input', e=>{ if(mode==='paged') goTo(+e.target.value); });
  slider.addEventListener('change', e=>{ if(mode==='webtoon') scrollToPage(+e.target.value); });

  function setCur(n, save=true){
    if(curBookId !== b.id){        // 이어붙인 다음 화 구간
      cur = Math.max(0, n);
      pnum.textContent = `${cur+1}`;
      if(save) saveProgress(curBookId, {page:cur});
      return;
    }
    cur = Math.max(0, Math.min(pages-1, n));
    slider.value=cur; pnum.textContent=`${cur+1} / ${pages}`;
    if(save) saveProgress(b.id, {page:cur, completed: cur>=pages-1 ? true : undefined});
  }

  let io=null;
  function rebuild(){
    if(io){io.disconnect();io=null;}
    clear(bodyWrap);
    const zoom = Math.max(50, Math.min(300, prefs.comicZoom||100));
    if(mode==='webtoon'){
      bodyWrap.className='reader-body';
      const strip = h('div',{class:'comic-webtoon fit-'+fit});
      strip.style.setProperty('--czoom', zoom+'%');
      strip.style.setProperty('--czoomf', String(zoom/100));
      for(let i=0;i<pages;i++){
        strip.append(h('img',{loading:'lazy', dataset:{page:i}, src:`/api/books/${b.id}/pages/${i}`}));
      }
      bodyWrap.append(strip);
      // 웹툰은 스크롤이 주 조작이므로 좌우 탭 영역은 두지 않고,
      // 가운데를 눌렀을 때만 상·하단 바를 켜고 끈다. 스크롤을 내리면 자동으로 숨긴다.
      const oldz = reader.querySelector('.tap-zones'); if(oldz) oldz.remove();
      const midZone = h('div',{class:'tap-mid', onclick:()=>toggleHud()});
      reader.append(midZone);
      let lastY = 0, hudTimer = null;
      bodyWrap.addEventListener('scroll', ()=>{
        const y = bodyWrap.scrollTop;
        if(y > lastY + 24){ reader.classList.add('hud-hidden'); }
        lastY = y;
        clearTimeout(hudTimer);
        hudTimer = setTimeout(()=>{ nearEndCheck(); }, 120);
      });

      io = new IntersectionObserver(entries=>{
        entries.forEach(en=>{
          if(!en.isIntersecting) return;
          const el = en.target;
          if(el.dataset.book && +el.dataset.book !== curBookId){
            curBookId = +el.dataset.book;                 // 다음 화 구간으로 진입
            titleEl.textContent = el.dataset.booktitle || titleEl.textContent;
          }
          setCur(+el.dataset.page);
        });
      }, {root:bodyWrap, threshold:0.5});
      strip.querySelectorAll('img').forEach(im=>io.observe(im));

      // 끝에 도달하면 다음 화를 이어붙여 스크롤만으로 계속 보게 한다
      let appending = false, noMore = false, tailId = b.id;
      async function nearEndCheck(){
        if(appending || noMore || !prefs.autoNext) return;
        const left = bodyWrap.scrollHeight - bodyWrap.scrollTop - bodyWrap.clientHeight;
        if(left > bodyWrap.clientHeight * 1.5) return;
        appending = true;
        try{
          const r = await api(`/api/books/${tailId}/next`);
          const nx = r.next;
          if(!nx){ noMore = true; return; }
          strip.append(h('div',{class:'next-sep'}, '다음 화 · ' + nx.title));
          const np = nx.page_count || 0;
          for(let i=0;i<np;i++){
            const im = h('img',{loading:'lazy',
              dataset:{page:i, book:String(nx.id), booktitle:nx.title},
              src:`/api/books/${nx.id}/pages/${i}`});
            strip.append(im); io.observe(im);
          }
          tailId = nx.id;
        }catch(e){ noMore = true; }
        finally{ appending = false; }
      }
      requestAnimationFrame(()=>scrollToPage(cur,false));
    }else{
      bodyWrap.className='reader-body';
      const stage = h('div',{class:'comic-paged fit-'+fit});
      stage.style.setProperty('--czoom', zoom+'%');
      stage.style.setProperty('--czoomf', String(zoom/100));
      const img = h('img',{});
      stage.append(img);
      bodyWrap.append(stage);
      attachTapZones(reader, {prev:()=>goTo(cur-1), next:()=>goTo(cur+1), toggleHud});
      bodyWrap._img = img;
      showPage();
    }
  }
  function showPage(){ if(bodyWrap._img) bodyWrap._img.src = `/api/books/${b.id}/pages/${cur}`; }
  function goTo(n){
    if(n >= pages){ offerNextBook(b, openBook); return; }   // 마지막 → 다음 권
    if(n < 0) return;
    setCur(n); if(mode==='paged'){ showPage(); bodyWrap.scrollTop=0; } else scrollToPage(n);
  }
  function scrollToPage(n, save=true){
    const el = bodyWrap.querySelector(`img[data-page="${n}"]`);
    if(el) el.scrollIntoView({block:'start'});
    if(save) setCur(n);
  }
  function toggleHud(){ reader.classList.toggle('hud-hidden'); }
  // 키보드
  reader.tabIndex=0;
  reader.addEventListener('keydown', e=>{
    if(e.key==='ArrowRight'||e.key==='ArrowDown'||e.key===' ') goTo(cur+1);
    else if(e.key==='ArrowLeft'||e.key==='ArrowUp') goTo(cur-1);
    else if(e.key==='Escape') closeOverlay();
  });
  rebuild();
  setTimeout(()=>reader.focus(),50);
}
function comicSettingsPanel(mode, fit, onChange){
  let m=mode, f=fit;
  const modeSeg = segPick(['webtoon','paged'],['웹툰(세로)','페이지'],m,v=>{m=v;onChange(m,f);});
  const fitSeg = segPick(['width','height','contain','original'],
                         ['너비','높이','화면맞춤','원본'],f,v=>{f=v;onChange(m,f);});
  const zoomLbl = h('span',{class:'muted',style:{fontSize:'12px',minWidth:'44px',textAlign:'right'}},
                    (prefs.comicZoom||100)+'%');
  const zoom = h('input',{type:'range',min:'50',max:'300',step:'5',value:String(prefs.comicZoom||100),
    style:{flex:'1',accentColor:'var(--amber)'}, oninput:e=>{
      prefs.comicZoom = +e.target.value; zoomLbl.textContent = prefs.comicZoom+'%';
      savePrefs(); onChange(m,f);
    }});
  const node = h('div',{class:'reader-settings'},
    h('div',{class:'rs-row'}, h('span',{},'보기 방식'), h('div',{class:'rs-controls'}, modeSeg)),
    h('div',{class:'rs-row'}, h('span',{},'이미지 맞춤'), h('div',{class:'rs-controls'}, fitSeg)),
    h('div',{class:'rs-row'}, h('span',{},'터치 이동'),
      h('div',{class:'rs-controls'}, segPick(['lr','tb','off'],['좌우','상하','끄기'],
        prefs.tapMode||'lr', v=>{prefs.tapMode=v;savePrefs();onChange(m,f);}))),
    h('div',{class:'rs-row'}, h('span',{},'좌우 반전'),
      h('div',{class:'rs-controls'}, segPick([false,true],['보통','반전(우철)'],
        !!prefs.tapInvert, v=>{prefs.tapInvert=v;savePrefs();onChange(m,f);}))),
    h('div',{class:'rs-row'}, h('span',{},'확대/축소'),
      h('div',{class:'rs-controls',style:{flex:'1',display:'flex',alignItems:'center',gap:'8px'}}, zoom, zoomLbl)),
    h('div',{style:{display:'flex',gap:'8px'}},
      h('button',{class:'btn sm',onclick:()=>{ prefs.comicZoom=100; zoom.value='100'; zoomLbl.textContent='100%'; savePrefs(); onChange(m,f); }},'100%'),
      h('button',{class:'btn',style:{flex:'1',justifyContent:'center'},onclick:()=>node.classList.remove('open')},'닫기'))
  );
  return {node, toggle:()=>node.classList.toggle('open')};
}

/* ---------- EPUB 뷰어 (epub.js) ---------- */
async function loadScript(src){
  return new Promise((res,rej)=>{
    if([...document.scripts].some(s=>s.src===src)) return res();
    const s=document.createElement('script'); s.src=src; s.onload=res; s.onerror=()=>rej(new Error('스크립트 로드 실패: '+src));
    document.head.append(s);
  });
}
const CDN = {
  jszip:'/assets/vendor/jszip.min.js',
  epub:'/assets/vendor/epub.min.js',
  pdf:'/assets/vendor/pdf.min.js',
  pdfworker:'/assets/vendor/pdf.worker.min.js',
};
/* EPUB 전용 터치 처리.
   오버레이(.tap-zones)를 쓰면 스크롤 제스처가 막히므로, 클릭 좌표로 영역을 판정한다.
   스크롤 모드에서는 화면 단위로 즉시 내려가고, 끝에 닿았을 때만 다음 챕터로 넘어간다. */
function attachEpubTaps(rendition, area, reader, b){
  let epubAtEnd = false;
  rendition.on('relocated', loc=>{ try{ epubAtEnd = !!loc.atEnd; }catch(e){} });
  function scroller(){
    if(area.scrollHeight - area.clientHeight > 4) return area;
    for(const el of area.querySelectorAll('*')){
      if(el.scrollHeight - el.clientHeight > 4) return el;
    }
    return area;
  }
  function handle(ev){
    const mode = prefs.tapMode || 'lr';
    if(mode === 'off') return;
    const r = area.getBoundingClientRect();
    const w = r.width, hh = r.height;
    // 아이프레임 내부 클릭은 좌표계가 area 와 동일하다
    const x = ev.clientX, y = ev.clientY;
    let zone;
    if(mode === 'tb') zone = y < hh*0.3 ? 'prev' : (y > hh*0.7 ? 'next' : 'mid');
    else              zone = x < w*0.3  ? 'prev' : (x > w*0.7  ? 'next' : 'mid');
    if(zone === 'mid'){ reader.classList.toggle('hud-hidden'); return; }
    if(prefs.tapInvert) zone = (zone === 'prev') ? 'next' : 'prev';

    if(forceScroll || prefs.epubFlow === 'scrolled'){
      const sc = scroller();
      const step = Math.max(120, sc.clientHeight - 56);
      const atEnd = sc.scrollTop + sc.clientHeight >= sc.scrollHeight - 6;
      const atTop = sc.scrollTop <= 2;
      if(zone === 'next'){
        if(atEnd){ if(epubAtEnd) offerNextBook(b, openBook); else rendition.next(); }
        else { sc.scrollTop = sc.scrollTop + step; }   // 애니메이션 없이 즉시 이동
      }else{
        if(atTop){ rendition.prev(); }
        else { sc.scrollTop = sc.scrollTop - step; }
      }
      return;
    }
    if(zone === 'next'){ if(epubAtEnd) offerNextBook(b, openBook); else rendition.next(); }
    else rendition.prev();
  }
  // 본문(아이프레임) 내부 클릭
  rendition.on('rendered', (section, view)=>{
    try{
      const d = view && (view.document || (view.contents && view.contents.document));
      if(d) d.addEventListener('click', handle);
    }catch(e){}
  });
  // 본문 바깥 여백 클릭
  area.addEventListener('click', handle);
  return handle;
}

/* ==========================================================================
   대용량 EPUB용 경량 리더
   파일 전체(1~2GB)를 받지 않고 서버에서 챕터 하나씩만 받아 표시한다.
   ========================================================================== */
async function openEpubLite(book){
  const b = await api('/api/books/'+book.id);
  const aaBtn = h('button',{class:'icon-btn',html:IC.aa});
  const imgBtn = h('button',{class:'icon-btn',html:IC.image,title:'삽화'});
  const tocBtn = h('button',{class:'icon-btn',html:IC.list,title:'목차'});
  const {reader} = readerShell(b.title, {themed:true, actions:[tocBtn, imgBtn, aaBtn]});
  const area = h('div',{id:'epub-area', class:'epub-lite'});
  const bottom = h('div',{class:'reader-bottom'});
  const slider = h('input',{type:'range',min:'0',max:'100',value:'0',class:'pslider'});
  const lbl = h('span',{class:'plabel'},'');
  const preLbl = h('span',{class:'pre-badge'},'');
  bottom.append(h('div',{class:'pageslider'},
    h('button',{class:'icon-btn',html:IC.prev,onclick:()=>goPrev()}),
    slider, lbl, preLbl,
    h('button',{class:'icon-btn',html:IC.next,onclick:()=>goNext()})));
  reader.append(area, bottom);
  openOverlay(reader);

  let cur = 0, part = 0, parts = 1, total = 0, chapters = [];
  const cache = new Map();          // "index:part" -> 응답
  const CACHE_MAX = 24;
  let prefetching = false;

  function ckey(i,p){ return i+':'+p; }
  async function fetchUnit(i, p){
    const k = ckey(i,p);
    if(cache.has(k)) return cache.get(k);
    const j = await api(`/api/books/${b.id}/chapter/${i}?part=${p}`);
    cache.set(k, j);
    if(cache.size > CACHE_MAX){ cache.delete(cache.keys().next().value); }
    return j;
  }
  // 읽는 동안 뒤쪽 조각을 미리 받아둔다 (받아지는 즉시 바로 읽을 수 있음)
  async function prefetchAhead(){
    const n = prefs.epubPrefetch|0;
    if(!n || prefetching) return;
    prefetching = true;
    try{
      let i = cur, p = part, done = 0;
      while(done < n){
        const cu = cache.get(ckey(i,p));
        const np = cu ? cu.parts : parts;
        if(p + 1 < np){ p += 1; } else { i += 1; p = 0; }
        if(i >= total) break;
        if(!cache.has(ckey(i,p))){
          preLbl.textContent = `미리 받는 중 ${done+1}/${n}`;
          try{ await fetchUnit(i,p); }catch(e){ break; }
        }
        done += 1;
      }
    } finally {
      prefetching = false;
      preLbl.textContent = '';
    }
  }
  try{
    const t = await api('/api/books/'+b.id+'/toc');
    chapters = t.chapters || []; total = chapters.length || t.spine_len || 0;
  }catch(e){}
  // 저장된 위치 복원 (형식: "lite:12@0.35")
  let startFrac = 0;
  const pos = b.progress && b.progress.position;
  let startPart = 0;
  if(pos && String(pos).startsWith('lite:')){
    const m = String(pos).slice(5).split('@');
    const cp = String(m[0]).split('.');
    cur = parseInt(cp[0]) || 0; startPart = parseInt(cp[1]) || 0;
    startFrac = parseFloat(m[1]) || 0;
  }

  applyLiteTheme();
  function applyLiteTheme(){
    const t = {light:{bg:'#faf7f2',color:'#22201c'}, sepia:{bg:'#f4ecd8',color:'#3b3226'},
               dark:{bg:'#16171c',color:'#c9c6be'}}[prefs.theme] || {bg:'#16171c',color:'#c9c6be'};
    area.style.background = t.bg; area.style.color = t.color;
    area.style.fontFamily = prefs.fontFamily==='serif'
      ? 'Georgia, "Noto Serif KR", serif' : '-apple-system, "Noto Sans KR", sans-serif';
    area.style.fontSize = (prefs.fontSize||110)+'%';
    area.style.lineHeight = String(prefs.lineHeight||1.7);
  }

  async function go(i, frac, p){
    p = p || 0;
    if(!total || i<0 || i>=total){
      if(i>=total && total) toast('마지막 장입니다.');
      return;
    }
    const cached = cache.has(ckey(i,p));
    if(!cached) clear(area).append(h('div',{class:'spinner'}));
    let j;
    try{ j = await fetchUnit(i,p); }
    catch(e){ clear(area).append(h('div',{class:'center-pad'},'챕터를 불러오지 못했습니다: '+e.message)); return; }
    cur = i; part = j.part||0; parts = j.parts||1;
    const body = h('div',{class:'lite-body'});
    body.innerHTML = j.html;   // 서버에서 script/on* 제거 후 전달
    clear(area).append(body);
    area.scrollTop = frac ? Math.round(area.scrollHeight*frac) : 0;
    const pct = total? Math.round(((i+1)/total)*100) : 0;
    slider.value = pct;
    lbl.textContent = parts>1 ? `${i+1}/${total} (${part+1}/${parts})` : `${i+1}/${total}`;
    saveProgress(b.id, {position:`lite:${i}.${part}@0`,
                        completed: (i+1>=total && part+1>=parts)?true:undefined});
    prefetchAhead();
  }
  // 다음/이전: 같은 챕터에 조각이 남아 있으면 조각 먼저
  function goNext(){ if(part+1 < parts) go(cur, 0, part+1); else go(cur+1, 0, 0); }
  function goPrev(){ if(part > 0) go(cur, 0, part-1); else go(cur-1, 0, 0); }
  // 스크롤 위치도 주기적으로 저장
  let sTimer=null;
  area.addEventListener('scroll', ()=>{
    clearTimeout(sTimer);
    sTimer=setTimeout(()=>{
      const frac = area.scrollHeight>area.clientHeight
        ? (area.scrollTop/(area.scrollHeight-area.clientHeight)) : 0;
      saveProgress(b.id, {position:`lite:${cur}.${part}@${frac.toFixed(3)}`});
    }, 800);
  });
  slider.addEventListener('change', e=>{
    const i = Math.min(total-1, Math.max(0, Math.round((+e.target.value/100)*total)-1));
    go(i);
  });

  // 터치: 스크롤이 남아 있으면 화면 단위 이동, 끝이면 다음 챕터
  const rend = { next: goNext, prev: goPrev };
  attachEpubTaps({on:()=>{}, next:rend.next, prev:rend.prev}, area, reader, true);

  tocBtn.addEventListener('click', ()=>openEpubTocLite(b.id, chapters, cur, go));
  imgBtn.addEventListener('click', ()=>openEpubImagesLite(b.id, chapters, go));
  const panel = textSettingsPanel(applyLiteTheme, ()=>{}, true, null);
  reader.append(panel.node);
  aaBtn.addEventListener('click', panel.toggle);

  await go(cur, startFrac, startPart);
}

/* 경량 리더용 목차 */
function openEpubTocLite(bookId, chapters, cur, go){
  const listWrap = h('div',{class:'toc-list'});
  const search = h('input',{class:'input',placeholder:`챕터 검색 (${chapters.length}개)`,style:{marginBottom:'10px'}});
  const inner = h('div',{}, h('h3',{style:{marginTop:0}},'목차'), search, listWrap);
  openSheet(inner);
  let curEl=null;
  function draw(f){
    clear(listWrap);
    const q=(f||'').trim().toLowerCase();
    const shown = q? chapters.filter(c=>String(c.title).toLowerCase().includes(q)) : chapters;
    if(!shown.length){ listWrap.append(h('div',{class:'center-pad'},'일치하는 챕터가 없습니다.')); return; }
    shown.forEach(c=>{
      const isCur = c.i===cur;
      const row=h('div',{class:'toc-row'+(isCur?' cur':''), onclick:()=>{ closeOverlay(); go(c.i); }},
        h('span',{class:'toc-num'}, String(c.i+1)), h('span',{class:'toc-title'}, c.title));
      if(isCur) curEl=row;
      listWrap.append(row);
    });
  }
  search.addEventListener('input',()=>draw(search.value));
  draw('');
  if(curEl) setTimeout(()=>{ try{curEl.scrollIntoView({block:'center'});}catch(e){} },30);
}

/* 경량 리더용 삽화 */
async function openEpubImagesLite(bookId, chapters, go){
  const grid=h('div',{class:'img-grid'});
  const inner=h('div',{}, h('h3',{style:{marginTop:0}},'삽화'),
    h('p',{class:'muted',style:{fontSize:'12.5px',margin:'2px 0 12px'}},'이미지를 누르면 해당 챕터로 이동합니다.'), grid);
  openSheet(inner);
  grid.append(h('div',{class:'spinner'}));
  let j;
  try{ j=await api(`/api/books/${bookId}/epub-images`); }
  catch(e){ clear(grid).append(h('div',{class:'center-pad'},e.message)); return; }
  const list=j.images||[];
  clear(grid);
  if(!list.length){ grid.append(h('div',{class:'center-pad'},'이 책에는 삽화가 없습니다.')); return; }
  const byHref = {}; chapters.forEach(c=>{ byHref[c.href]=c.i; });
  list.slice(0,200).forEach(it=>{
    grid.append(h('div',{class:'img-cell',title:it.title||'',onclick:()=>{
      closeOverlay(); const i=byHref[it.chapter]; if(i!=null) go(i); else toast('이동할 수 없습니다.');
    }}, h('img',{src:`/api/books/${bookId}/epub-thumb?href=${encodeURIComponent(it.href)}`,loading:'lazy',alt:''})));
  });
}

async function openEpubReader(book){
  const b = await api('/api/books/'+book.id);
  const aaBtn = h('button',{class:'icon-btn',html:IC.aa});
  const imgBtn = h('button',{class:'icon-btn',html:IC.image,title:'삽화'});
  const tocBtn = h('button',{class:'icon-btn',html:IC.list,title:'목차'});
  const {reader} = readerShell(b.title, {themed:true, actions:[tocBtn, imgBtn, aaBtn]});
  const area = h('div',{id:'epub-area'});
  const bottom = h('div',{class:'reader-bottom'});
  const slider = h('input',{type:'range',min:0,max:100,value:0,style:{width:'100%',accentColor:'var(--amber)'}});
  const lbl = h('div',{class:'pnum'},'');
  bottom.append(h('div',{class:'pageslider'},
    h('button',{class:'icon-btn',html:IC.back,onclick:()=>rendition.prev()}), slider, lbl,
    h('button',{class:'icon-btn',style:{transform:'rotate(180deg)'},html:IC.back,onclick:()=>rendition.next()})));
  reader.append(area, bottom);
  openOverlay(reader);
  area.append(h('div',{class:'spinner'}));

  let rendition=null, bookObj=null;
  try{
    await loadScript(CDN.jszip); await loadScript(CDN.epub);
  }catch(e){ clear(area).append(h('div',{class:'center-pad'},'EPUB 뷰어 로딩 실패. 페이지를 새로고침해 보세요.')); return; }

  // 중요: /api/books/{id}/file 은 확장자가 없어 epub.js 가 '폴더'로 오인 → 화면이 비어버림.
  // 파일을 직접 받아 ArrayBuffer(바이너리)로 넘겨야 정상 렌더링됨.
  try{
    const resp = await fetch(`/api/books/${b.id}/file`, {credentials:'same-origin'});
    if(!resp.ok) throw new Error('HTTP '+resp.status);
    const buf = await resp.arrayBuffer();
    clear(area);
    bookObj = ePub(buf);
  }catch(e){
    clear(area).append(h('div',{class:'center-pad'},'EPUB 파일을 불러오지 못했습니다: '+e.message));
    return;
  }

  try{
    rendition = bookObj.renderTo(area, {
      width:'100%', height:'100%', spread:'none',
      flow: prefs.epubFlow==='scrolled'?'scrolled-doc':'paginated',
      allowScriptedContent:false,
    });
    applyEpubTheme(rendition);
    const startCfi = (b.progress && b.progress.position) || undefined;
    try{
      await rendition.display(startCfi);
    }catch(e){
      // 저장된 위치가 깨졌으면 처음부터
      await rendition.display();
    }
  }catch(e){
    clear(area).append(h('div',{class:'center-pad'},
      h('p',{},'EPUB 렌더링 실패: '+e.message),
      h('button',{class:'btn',style:{marginTop:'10px'},onclick:()=>{
        prefs.epubFlow='scrolled'; savePrefs(); closeOverlay(); openEpubReader(book);
      }},'스크롤 모드로 다시 열기')));
    return;
  }

  // ---- 진행률 ----
  // 주의: locations.generate() 는 모든 챕터를 파싱합니다. 수백 화짜리 책에서는
  // 휴대폰이 멈추거나 화면이 비어버리므로, 큰 책은 스파인(챕터) 위치 기준으로 계산합니다.
  const spineLen = (bookObj.spine && bookObj.spine.spineItems) ? bookObj.spine.spineItems.length : 0;
  const HEAVY = spineLen > 80;
  let useLocations = false;

  const pctFromSpine = (loc)=>{
    if(!spineLen) return 0;
    const idx = (loc && loc.start && typeof loc.start.index === 'number') ? loc.start.index : 0;
    return Math.round(((idx + 1) / spineLen) * 100);
  };

  rendition.on('relocated', loc=>{
    let p;
    if(useLocations && bookObj.locations && bookObj.locations.length()){
      p = Math.round((bookObj.locations.percentageFromCfi(loc.start.cfi) || 0) * 100);
    }else{
      p = pctFromSpine(loc);
    }
    slider.value = p;
    lbl.textContent = p + '%' + (HEAVY && spineLen ? ` (${(loc.start&&loc.start.index!=null?loc.start.index+1:1)}/${spineLen})` : '');
    saveProgress(b.id, {position: loc.start.cfi, completed: loc.atEnd ? true : undefined});
  });

  if(!HEAVY){
    bookObj.ready
      .then(()=>bookObj.locations.generate(1600))
      .then(()=>{ useLocations = true; })
      .catch(()=>{});
  }

  slider.addEventListener('change', e=>{
    const v = +e.target.value;
    if(useLocations && bookObj.locations && bookObj.locations.length()){
      rendition.display(bookObj.locations.cfiFromPercentage(v/100));
    }else if(spineLen){
      const idx = Math.min(spineLen-1, Math.max(0, Math.round(v/100*spineLen)-1));
      const item = bookObj.spine.spineItems[idx];
      if(item) rendition.display(item.href);
    }
  });

  // 키보드 (HUD 토글은 attachEpubTaps 의 '중앙' 영역에서만 처리)
  const keyh = e=>{ if(e.key==='ArrowRight')rendition.next(); else if(e.key==='ArrowLeft')rendition.prev(); else if(e.key==='Escape')closeOverlay(); };
  document.addEventListener('keydown', keyh);
  reader._onClose = ()=>{ document.removeEventListener('keydown',keyh); try{bookObj.destroy();}catch(e){} };

  // 설정 패널
  const panel = textSettingsPanel(()=>applyEpubTheme(rendition), ()=>{
    rendition.flow(prefs.epubFlow==='scrolled'?'scrolled-doc':'paginated');
  }, false, null);
  reader.append(panel.node);
  aaBtn.addEventListener('click', panel.toggle);

  // 목차 / 삽화 (서버가 미리 분석한 데이터를 즉시 사용)
  let curHref = null;
  rendition.on('relocated', loc=>{ try{ curHref = loc.start.href; }catch(e){} });
  tocBtn.addEventListener('click', ()=>openEpubToc(b.id, rendition, curHref));
  imgBtn.addEventListener('click', ()=>openEpubImages(b.id, rendition));

  // 화면 터치로 페이지/챕터 이동 (스크롤을 막지 않는 방식)
  attachEpubTaps(rendition, area, reader, b);
}

/* EPUB 챕터 목록 — 스캔 때 미리 분석해 둔 목차를 즉시 표시 */
async function openEpubToc(bookId, rendition, curHref){
  const listWrap = h('div',{class:'toc-list'});
  const inner = h('div',{},
    h('h3',{style:{marginTop:0}},'목차'),
    listWrap);
  openSheet(inner);
  listWrap.append(h('div',{class:'spinner'}));
  let j;
  try{ j = await api(`/api/books/${bookId}/toc`); }
  catch(e){ clear(listWrap).append(h('div',{class:'center-pad'}, e.message)); return; }
  clear(listWrap);
  const chapters = j.chapters||[];
  if(!chapters.length){ listWrap.append(h('div',{class:'center-pad'},'목차 정보가 없습니다.')); return; }
  const search = h('input',{class:'input',placeholder:`챕터 검색 (${chapters.length}개)`,style:{marginBottom:'10px'}});
  inner.insertBefore(search, listWrap);
  let curEl = null;
  function draw(filter){
    clear(listWrap);
    const f = (filter||'').trim().toLowerCase();
    const shown = f ? chapters.filter(c=>String(c.title).toLowerCase().includes(f)) : chapters;
    if(!shown.length){ listWrap.append(h('div',{class:'center-pad'},'일치하는 챕터가 없습니다.')); return; }
    shown.forEach(c=>{
      const isCur = curHref && c.href===curHref;
      const row = h('div',{class:'toc-row'+(isCur?' cur':''), onclick:()=>{
        closeOverlay();
        try{ rendition.display(c.href); }catch(e){ toast('이동할 수 없습니다.'); }
      }}, h('span',{class:'toc-num'}, String(c.i+1)), h('span',{class:'toc-title'}, c.title));
      if(isCur) curEl = row;
      listWrap.append(row);
    });
  }
  search.addEventListener('input', ()=>draw(search.value));
  draw('');
  if(curEl) setTimeout(()=>{ try{ curEl.scrollIntoView({block:'center'}); }catch(e){} }, 30);
}

/* EPUB 삽화 목록 — 서버가 미리 뽑아둔 목록을 즉시 표시, 클릭 시 해당 챕터로 이동 */
async function openEpubImages(bookId, rendition){
  const grid = h('div',{class:'img-grid'});
  const inner = h('div',{},
    h('h3',{style:{marginTop:0}},'삽화'),
    h('p',{class:'muted',style:{fontSize:'12.5px',margin:'2px 0 12px'}},'이미지를 누르면 해당 챕터로 이동합니다.'),
    grid);
  openSheet(inner);
  grid.append(h('div',{class:'spinner'}));
  let j;
  try{ j = await api(`/api/books/${bookId}/epub-images`); }
  catch(e){ clear(grid).append(h('div',{class:'center-pad'}, e.message)); return; }
  const list = j.images||[];
  clear(grid);
  if(!list.length){ grid.append(h('div',{class:'center-pad'},'이 책에는 삽화가 없습니다.')); return; }
  // 썸네일(스캔 때 미리 생성)을 사용해 원본을 받지 않는다.
  // 개수가 많으면 한 번에 다 붙이지 않고 나눠서 붙여 첫 화면을 빠르게 띄운다.
  const PAGE = 60;
  let shown = 0;
  const moreWrap = h('div',{style:{gridColumn:'1/-1',textAlign:'center',padding:'8px 0'}});
  function addBatch(){
    const slice = list.slice(shown, shown + PAGE);
    slice.forEach(it=>{
      const url = `/api/books/${bookId}/epub-thumb?href=${encodeURIComponent(it.href)}`;
      grid.insertBefore(h('div',{class:'img-cell', title: it.title||'', onclick:()=>{
        closeOverlay();
        try{ rendition.display(it.chapter); }catch(e){ toast('이동할 수 없습니다.'); }
      }}, h('img',{src:url, loading:'lazy', decoding:'async', alt:''})), moreWrap);
    });
    shown += slice.length;
    clear(moreWrap);
    if(shown < list.length){
      moreWrap.append(h('button',{class:'btn sm',onclick:addBatch},
        `더 보기 (${shown}/${list.length})`));
    }
  }
  grid.append(moreWrap);
  addBatch();
}
function applyEpubTheme(rendition){
  const themes = {
    light:{bg:'#f5f0e6', color:'#2a2620'},
    sepia:{bg:'#f3e9d2', color:'#4a3f2a'},
    dark:{bg:'#16171c', color:'#c9c6be'},
  };
  const t = themes[prefs.theme]||themes.dark;
  const fam = prefs.fontFamily==='serif' ? '"Noto Serif KR",serif' : '"Noto Sans KR",sans-serif';
  rendition.themes.register('md', {
    'body':{ 'background':t.bg+'!important', 'color':t.color+'!important',
      'font-family':fam+'!important', 'line-height':prefs.lineHeight+'!important',
      'padding':'0 6px' },
    'p':{ 'line-height':prefs.lineHeight+'!important' },
    'a':{ 'color':'#d9973f!important' },
    // 큰 표지/삽화가 페이지를 밀어내 빈 화면이 되는 것을 방지
    'img, svg, image':{ 'max-width':'100%!important', 'max-height':'95vh!important',
      'height':'auto!important', 'object-fit':'contain' },
    'table, pre':{ 'max-width':'100%!important' },
  });
  rendition.themes.select('md');
  rendition.themes.fontSize(prefs.fontSize+'%');
  const reader = rendition.manager && rendition.manager.container ? rendition.manager.container.closest('.reader') : null;
  if(reader){ reader.className='reader rtheme-'+prefs.theme; }
}

/* ---------- PDF 뷰어 (pdf.js) ---------- */
async function openPdfReader(book){
  const b = await api('/api/books/'+book.id);
  const {reader} = readerShell(b.title, {});
  const bodyWrap = h('div',{class:'reader-body',style:{background:'#333',textAlign:'center'}});
  const bottom = h('div',{class:'reader-bottom'});
  const slider = h('input',{type:'range',min:1,max:1,value:1});
  const pnum = h('div',{class:'pnum'},'');
  bottom.append(h('div',{class:'pageslider'},
    h('button',{class:'icon-btn',html:IC.back,onclick:()=>render(cur-1)}), slider, pnum,
    h('button',{class:'icon-btn',style:{transform:'rotate(180deg)'},html:IC.back,onclick:()=>render(cur+1)})));
  reader.append(bodyWrap, bottom);
  openOverlay(reader);
  bodyWrap.append(h('div',{class:'spinner'}));

  try{ await loadScript(CDN.pdf); }
  catch(e){ clear(bodyWrap).append(h('div',{class:'center-pad'},'PDF 뷰어 로딩 실패. 인터넷 연결을 확인하세요.')); return; }
  pdfjsLib.GlobalWorkerOptions.workerSrc = CDN.pdfworker;

  let pdf=null, cur=(b.progress&&b.progress.page? b.progress.page+1:1), rendering=false;
  const canvas = h('canvas',{style:{maxWidth:'100%',height:'auto'}});
  try{
    pdf = await pdfjsLib.getDocument({url:`/api/books/${b.id}/file`, withCredentials:true}).promise;
  }catch(e){ clear(bodyWrap).append(h('div',{class:'center-pad'},'PDF를 열 수 없습니다: '+e.message)); return; }
  slider.max = pdf.numPages; cur=Math.min(cur, pdf.numPages);
  clear(bodyWrap).append(canvas);
  slider.addEventListener('change', e=>render(+e.target.value));
  const keyh=e=>{ if(e.key==='ArrowRight')render(cur+1); else if(e.key==='ArrowLeft')render(cur-1); else if(e.key==='Escape')closeOverlay(); };
  document.addEventListener('keydown',keyh);
  reader._onClose=()=>document.removeEventListener('keydown',keyh);
  bodyWrap.addEventListener('click', e=>{ if(e.target===bodyWrap) reader.classList.toggle('hud-hidden'); });

  async function render(n){
    if(rendering||n<1||n>pdf.numPages) return; rendering=true; cur=n;
    slider.value=n; pnum.textContent=`${n} / ${pdf.numPages}`;
    const page = await pdf.getPage(n);
    const scale = Math.min(2, (bodyWrap.clientWidth-8)/page.getViewport({scale:1}).width) * (window.devicePixelRatio||1);
    const vp = page.getViewport({scale});
    canvas.width=vp.width; canvas.height=vp.height;
    canvas.style.width=(vp.width/(window.devicePixelRatio||1))+'px';
    await page.render({canvasContext:canvas.getContext('2d'), viewport:vp}).promise;
    saveProgress(b.id,{page:n-1, completed:n>=pdf.numPages?true:undefined});
    rendering=false;
  }
  render(cur);
}

/* ---------- TXT 뷰어 ---------- */
async function openTxtReader(book){
  const b = await api('/api/books/'+book.id);
  const aaBtn = h('button',{class:'icon-btn',html:IC.aa});
  const {reader} = readerShell(b.title, {themed:true, actions:[aaBtn]});
  const area = h('div',{id:'txt-area'});
  const content = h('div',{class:'txt-content'});
  area.append(content);
  reader.append(area);
  openOverlay(reader);
  content.append(h('div',{class:'spinner'}));
  applyTxtStyle(content, area, reader);

  let text='';
  try{ text = await (await fetch('/api/books/'+b.id+'/content',{credentials:'same-origin'})).text(); }
  catch(e){ clear(content).append('불러오기 실패'); return; }
  content.textContent = text;

  // 위치 복원 (백분율)
  const startPct = (b.progress && b.progress.position && b.progress.position.endsWith('%')) ? parseFloat(b.progress.position) : 0;
  requestAnimationFrame(()=>{ if(startPct>0) area.scrollTop = (area.scrollHeight-area.clientHeight)*(startPct/100); });

  let st=null;
  area.addEventListener('scroll', ()=>{
    reader.classList.remove('hud-hidden');
    clearTimeout(st);
    st=setTimeout(()=>{
      const max=area.scrollHeight-area.clientHeight;
      const pct = max>0? (area.scrollTop/max*100):0;
      saveProgress(b.id, {position: pct.toFixed(1)+'%', completed: pct>=99?true:undefined});
    }, 500);
  });
  area.addEventListener('click', ()=>reader.classList.toggle('hud-hidden'));

  const panel = textSettingsPanel(()=>applyTxtStyle(content, area, reader), null, true);
  reader.append(panel.node);
  aaBtn.addEventListener('click', panel.toggle);
}
function applyTxtStyle(content, area, reader){
  content.style.fontFamily = prefs.fontFamily==='serif' ? '"Noto Serif KR",serif' : 'var(--ui)';
  content.style.fontSize = (prefs.fontSize/100*17)+'px';
  content.style.lineHeight = prefs.lineHeight;
  reader.className='reader rtheme-'+prefs.theme;
}

/* ---------- 공용: 글자 설정 패널 (EPUB/TXT) ---------- */
function textSettingsPanel(apply, onFlowChange, isTxt, onTapChange){
  const sizeVal = h('span',{class:'val'}, prefs.fontSize+'%');
  const lhVal = h('span',{class:'val'}, prefs.lineHeight.toFixed(1));
  const stepper = (getV,setV,min,max,step,valEl,fmt)=> h('div',{class:'stepper'},
    h('button',{onclick:()=>{const v=Math.max(min,+(getV()-step).toFixed(2));setV(v);valEl.textContent=fmt(v);apply();}},'−'),
    valEl,
    h('button',{onclick:()=>{const v=Math.min(max,+(getV()+step).toFixed(2));setV(v);valEl.textContent=fmt(v);apply();}},'+'));

  const famSeg = segPick(['sans','serif'],['고딕','명조'],prefs.fontFamily,v=>{prefs.fontFamily=v;savePrefs();apply();});
  const themeSw = h('div',{style:{display:'flex',gap:'8px'}},
    ...[['light','#f5f0e6'],['sepia','#f3e9d2'],['dark','#16171c']].map(([id,c])=>
      h('button',{class:'theme-swatch'+(prefs.theme===id?' on':''),style:{background:c},onclick:e=>{
        prefs.theme=id;savePrefs();[...e.target.parentNode.children].forEach(x=>x.className='theme-swatch');e.target.className='theme-swatch on';apply();
      }})));

  const rows = [
    h('div',{class:'rs-row'}, h('span',{},'글자 크기'),
      h('div',{class:'rs-controls'}, stepper(()=>prefs.fontSize,v=>{prefs.fontSize=v;savePrefs();},70,220,10,sizeVal,v=>v+'%'))),
    h('div',{class:'rs-row'}, h('span',{},'줄 간격'),
      h('div',{class:'rs-controls'}, stepper(()=>prefs.lineHeight,v=>{prefs.lineHeight=v;savePrefs();},1.2,2.4,0.1,lhVal,v=>(+v).toFixed(1)))),
    h('div',{class:'rs-row'}, h('span',{},'글꼴'), h('div',{class:'rs-controls'}, famSeg)),
    h('div',{class:'rs-row'}, h('span',{},'테마'), h('div',{class:'rs-controls'}, themeSw)),
    h('div',{class:'rs-row'}, h('span',{},'터치 이동'),
      h('div',{class:'rs-controls'}, segPick(['lr','tb','off'],['좌우','상하','끄기'],
        prefs.tapMode||'lr', v=>{ prefs.tapMode=v; savePrefs(); if(onTapChange) onTapChange(); }))),
  ];
  if(!isTxt && onFlowChange){
    rows.push(h('div',{class:'rs-row'}, h('span',{},'페이지 방식'),
      h('div',{class:'rs-controls'}, segPick(['paginated','scrolled'],['쪽넘김','스크롤'],prefs.epubFlow,v=>{prefs.epubFlow=v;savePrefs();onFlowChange();}))));
  }
  const node = h('div',{class:'reader-settings'}, ...rows,
    h('button',{class:'btn',style:{width:'100%',justifyContent:'center'},onclick:()=>node.classList.remove('open')},'닫기'));
  return {node, toggle:()=>node.classList.toggle('open')};
}

/* ==========================================================================
   시작
   ========================================================================== */
boot();

/* PWA 서비스워커 — 새 버전 배포 시 강력 새로고침 없이 자동 반영 */
if('serviceWorker' in navigator){
  let swReloaded = false;
  // 새 서비스워커가 제어를 넘겨받으면 한 번만 자동 새로고침
  navigator.serviceWorker.addEventListener('controllerchange', ()=>{
    if(swReloaded) return; swReloaded = true;
    location.reload();
  });
  window.addEventListener('load', ()=>{
    // updateViaCache:'none' → sw.js 자체가 브라우저 캐시에 묶이지 않음
    navigator.serviceWorker.register('/sw.js', {updateViaCache:'none'}).then(reg=>{
      reg.update().catch(()=>{});
      // 주기적 + 앱으로 돌아올 때 새 버전 확인
      setInterval(()=>reg.update().catch(()=>{}), 30*60*1000);
      document.addEventListener('visibilitychange', ()=>{
        if(document.visibilityState==='visible') reg.update().catch(()=>{});
      });
      reg.addEventListener('updatefound', ()=>{
        const nw = reg.installing;
        if(!nw) return;
        nw.addEventListener('statechange', ()=>{
          // 새 버전 설치 완료 + 기존 SW 가 제어 중 → 즉시 교체
          if(nw.state==='installed' && navigator.serviceWorker.controller){
            try{ nw.postMessage({type:'SKIP_WAITING'}); }catch(e){}
          }
        });
      });
    }).catch(()=>{});
  });
}
