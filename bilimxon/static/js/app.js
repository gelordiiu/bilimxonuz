/* ═══════════════════════════════════════════════
   Bilimxon v5 — app.js
   Asl dizayn + Games + Notifications
═══════════════════════════════════════════════ */

/* ─── API ─── */
async function api(url, opts) {
  opts = opts || {};
  if (!opts.headers) opts.headers = {};
  if (opts.body && typeof opts.body !== 'string' && !(opts.body instanceof FormData)) {
    opts.body = JSON.stringify(opts.body);
  }
  if (opts.body && typeof opts.body === 'string' && !opts.headers['Content-Type']) {
    opts.headers['Content-Type'] = 'application/json';
  }
  const res = await fetch(url, opts);
  const ct = res.headers.get('content-type') || '';
  let data = {};
  try { data = ct.includes('application/json') ? await res.json() : {_text: await res.text()}; } catch(e){}
  if (!res.ok) throw new Error(data.error || data.message || ('HTTP '+res.status));
  if (data.error) throw new Error(data.error);
  return data;
}

/* ─── Me cache ─── */
let _me = null;
let _meLoading = false;
let _meCallbacks = [];
async function getMe(force) {
  if (_me && !force) return _me;
  return new Promise(function(resolve) {
    _meCallbacks.push(resolve);
    if (_meLoading && !force) return;
    _meLoading = true;
    api('/api/me').then(function(data) {
      _me = data;
      _meLoading = false;
      var cbs = _meCallbacks.splice(0);
      cbs.forEach(function(cb){ cb(data); });
    }).catch(function() {
      var data = {logged_in:false};
      _me = data;
      _meLoading = false;
      var cbs = _meCallbacks.splice(0);
      cbs.forEach(function(cb){ cb(data); });
    });
  });
}

/* ─── Toast ─── */
let _toast = null, _tTimer = null;
function showToast(msg, type, dur) {
  type = type||'info'; dur = dur||3000;
  if (!_toast) {
    _toast = document.createElement('div');
    _toast.id = 'bxToast';
    document.body.appendChild(_toast);
    var s = document.createElement('style');
    s.textContent = '#bxToast{position:fixed;bottom:24px;right:20px;z-index:99999;font-family:Outfit,sans-serif;font-size:.9rem;font-weight:600;display:flex;align-items:center;gap:10px;padding:12px 18px;border-radius:14px;box-shadow:0 8px 28px rgba(0,0,0,.4);max-width:340px;color:white;line-height:1.4;transition:opacity .3s ease;}.notif-item{display:flex;align-items:flex-start;gap:10px;padding:11px 14px;cursor:pointer;border-bottom:1px solid #F3F4F6;transition:.15s;}.notif-item:hover{background:#F9FAFB;}.notif-item.unread{background:#EFF6FF;}.notif-icon{font-size:1.1rem;flex-shrink:0;margin-top:2px;}.notif-title{font-size:.83rem;font-weight:700;color:#1B2A4A;margin-bottom:2px;}.notif-body{font-size:.76rem;color:#6B7280;line-height:1.4;}.notif-time{font-size:.68rem;color:#9CA3AF;margin-top:3px;}.topbar-icon-btn{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.12);color:rgba(255,255,255,.7);width:36px;height:36px;border-radius:10px;cursor:pointer;font-size:1rem;display:flex;align-items:center;justify-content:center;position:relative;transition:.15s;}.topbar-icon-btn:hover{background:rgba(255,255,255,.15);color:white;}';
    document.head.appendChild(s);
  }
  var bg = {success:'linear-gradient(135deg,#14532d,#166534)',error:'linear-gradient(135deg,#7f1d1d,#991b1b)',info:'linear-gradient(135deg,#1e3a5f,#1d4ed8)',warning:'linear-gradient(135deg,#78350f,#b45309)'};
  var ic = {success:'✅',error:'❌',info:'ℹ️',warning:'⚠️'};
  _toast.style.background = bg[type]||bg.info;
  _toast.style.opacity = '1';
  _toast.style.display = 'flex';
  _toast.innerHTML = '<span>'+ic[type]+'</span><span>'+msg+'</span>';
  clearTimeout(_tTimer);
  _tTimer = setTimeout(function(){_toast.style.opacity='0';setTimeout(function(){if(_toast)_toast.style.display='none';},300);}, dur);
}

/* ─── Modal ─── */
function openModal(html, persistent) {
  document.querySelector('.modal-overlay') && document.querySelector('.modal-overlay').remove();
  var ov = document.createElement('div');
  ov.className = 'modal-overlay';
  ov.innerHTML = '<div class="modal-box">'+html+'</div>';
  ov.addEventListener('click', function(e){if(e.target===ov && !persistent)closeModal();});
  document.body.appendChild(ov);
  document.body.style.overflow = 'hidden';
  ov.querySelectorAll('.modal-close').forEach(function(b){b.addEventListener('click',closeModal);});
}
function closeModal() {
  var ov = document.querySelector('.modal-overlay');
  if(ov) ov.remove();
  document.body.style.overflow = '';
}
function confirmDialog(msg, yes, no) {
  return new Promise(function(resolve){
    openModal('<div class="modal-header"><span class="modal-title">⚠️ Tasdiqlash</span><button class="modal-close">✕</button></div><p style="color:var(--gray-600);margin:0 0 20px;line-height:1.6;">'+msg+'</p><div class="modal-footer"><button class="btn btn-outline modal-close" id="cnNo">'+(no||"Yo'q")+'</button><button class="btn btn-danger" id="cnYes">'+(yes||'Ha')+'</button></div>');
    document.getElementById('cnYes').onclick = function(){closeModal();resolve(true);};
    document.getElementById('cnNo').onclick  = function(){closeModal();resolve(false);};
  });
}

/* ─── Progress Bar ─── */
function makeProgressBar(pct, color) {
  var p = Math.min(100,Math.max(0,pct||0));
  return '<div class="progress-bar"><div class="progress-fill" style="width:'+p+'%;'+(color?'background:'+color:'')+'""></div></div>';
}

/* ─── Lang ─── */
async function setLang(lang) {
  // Set cookie first
  document.cookie = 'lang='+lang+';path=/;max-age=31536000;SameSite=Lax';
  // Then update server session (don't await - just fire and forget to avoid timing issues)
  api('/api/set-lang',{method:'POST',body:JSON.stringify({lang})}).catch(function(){});
  // Small delay before reload to ensure cookie is set
  setTimeout(function(){ location.reload(); }, 100);
}

/* ─── Notifications ─── */
var _nc = 0, _ncPrev = -1, _sseActive = false;
async function _loadNC() {
  try {
    var d = await api('/api/notifications/count');
    var newCount = d.count||0;
    var b = document.getElementById('notifBadge');
    if(b){b.textContent=newCount>9?'9+':newCount;b.style.display=newCount>0?'flex':'none';}
    // Only show toast if SSE is NOT active (avoid duplicates)
    if(!_sseActive && newCount > _ncPrev && _ncPrev >= 0) {
      try {
        var nd = await api('/api/notifications');
        var ns = nd.notifications||[];
        if(ns.length && !ns[0].is_read) {
          showToast(ns[0].title + (ns[0].body ? ': '+ns[0].body.slice(0,40) : ''), 'info', 5000);
        }
      } catch(e){}
    }
    _ncPrev = newCount;
    _nc = newCount;
  }catch(e){}
}

async function openNotifications() {
  var panel = document.getElementById('notifPanel');
  if(!panel) return;
  if(panel.style.display!=='none'){panel.style.display='none';return;}
  panel.style.display = 'block';
  panel.innerHTML = '<div style="padding:20px;text-align:center;"><div class="spinner" style="margin:0 auto;width:24px;height:24px;border-width:3px;border-color:rgba(27,42,74,.1);border-top-color:#1B2A4A;"></div></div>';
  try {
    var data = await api('/api/notifications');
    var ns = data.notifications||[];
    var icons = {friend_req:'\u{1F465}',friend_acc:'\u2705',game_approved:'\u{1F3AE}',game_rejected:'\u274C',message:'\u{1F4AC}',gift:'\u{1F381}',system:'\u{1F514}'};
    var typeColors = {friend_req:'#3B82F6',friend_acc:'#22C55E',game_approved:'#C9A84C',game_rejected:'#EF4444',message:'#8B5CF6',gift:'#F59E0B',system:'#6B7280'};
    if(!ns.length){
      panel.innerHTML = '<div style="padding:36px 20px;text-align:center;"><div style="font-size:2.8rem;margin-bottom:12px;">\u{1F515}</div><div style="color:#9CA3AF;font-size:.9rem;font-weight:600;">Bildirishnoma yo\'q</div></div>';
      return;
    }
    panel.innerHTML = '<div style="padding:14px 16px 10px;display:flex;align-items:center;justify-content:space-between;border-bottom:1.5px solid #F3F4F6;position:sticky;top:0;background:white;z-index:1;border-radius:18px 18px 0 0;">'
      + '<span style="font-weight:800;font-size:.95rem;color:#1B2A4A;">\u{1F514} Bildirishnomalar</span>'
      + '<button onclick="markAllRead()" style="font-size:.75rem;color:#1B2A4A;background:rgba(27,42,74,.07);border:none;cursor:pointer;font-weight:700;padding:4px 10px;border-radius:8px;">Hammasini o\'qi</button>'
      + '</div>'
      + ns.map(function(n){
          var ic = icons[n.notif_type]||'\u{1F514}';
          var col = typeColors[n.notif_type]||'#6B7280';
          var senderHtml = n.sender_username
            ? '<a href="/profile/'+n.sender_username+'" onclick="event.stopPropagation()" style="color:'+col+';font-weight:700;font-size:.75rem;text-decoration:none;">@'+n.sender_username+'</a> &middot; '
            : '';
          var bg = n.is_read ? 'white' : '#EFF6FF';
          return '<div onclick="clickNotif('+n.id+',\''+( n.ref_url||'')+'\')" style="display:flex;align-items:flex-start;gap:12px;padding:13px 16px;cursor:pointer;border-bottom:1px solid #F9FAFB;background:'+bg+'" onmouseover="this.style.background=\'#F9FAFB\'" onmouseout="this.style.background=\''+bg+'\'">'
            + '<div style="width:42px;height:42px;border-radius:13px;background:'+col+'1A;display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0;">'+ic+'</div>'
            + '<div style="flex:1;min-width:0;">'
            + '<div style="font-size:.87rem;font-weight:700;color:#1B2A4A;margin-bottom:3px;line-height:1.3;">'+n.title+'</div>'
            + (n.body?'<div style="font-size:.79rem;color:#6B7280;line-height:1.4;margin-bottom:4px;">'+n.body+'</div>':'')
            + '<div style="font-size:.71rem;color:#9CA3AF;">'+senderHtml+timeAgo(n.created_at)+'</div>'
            + '</div>'
            + (n.is_read?'':'<div style="width:9px;height:9px;border-radius:50%;background:#1B2A4A;flex-shrink:0;margin-top:7px;"></div>')
            + '</div>';
        }).join('');
    await api('/api/notifications/mark-read',{method:'POST',body:JSON.stringify({})});
    _nc=0; var b=document.getElementById('notifBadge'); if(b)b.style.display='none';
  }catch(e){panel.innerHTML='<div style="padding:16px;color:#EF4444;font-size:.82rem;text-align:center;">'+e.message+'</div>';}
}
async function markAllRead(){
  try{
    await api('/api/notifications/mark-read',{method:'POST',body:JSON.stringify({})});
    _nc=0;_ncPrev=0;
    var b=document.getElementById('notifBadge');if(b)b.style.display='none';
    // Visually mark all as read in the panel
    var panel=document.getElementById('notifPanel');
    if(panel){
      panel.querySelectorAll('[style*="EFF6FF"]').forEach(function(el){el.style.background='white';});
      panel.querySelectorAll('[style*="width:9px"]').forEach(function(el){el.style.display='none';});
    }
  }catch(e){}
}
function clickNotif(id,url){
  var p=document.getElementById('notifPanel');if(p)p.style.display='none';
  if(url&&url!=='undefined'&&url!=='')window.location.href=url;
}
function timeAgo(ts){
  if(!ts) return '';
  try{
    var str=(ts+'').trim().replace(' ','T');
    if(!str.endsWith('Z')&&!str.includes('+'))str+='Z';
    var d=new Date(str);
    if(isNaN(d.getTime()))return '';
    var s=Math.floor((Date.now()-d.getTime())/1000);
    if(s<0)s=0;
    var isRU=(document.cookie.match(/lang=([^;]+)/)||[])[1]==='ru';
    if(isRU){
      if(s<5)return 'только что';
      if(s<60)return s+' сек. назад';
      if(s<3600)return Math.floor(s/60)+' мин. назад';
      if(s<86400)return Math.floor(s/3600)+' ч. назад';
      if(s<2592000)return Math.floor(s/86400)+' дн. назад';
      return d.toLocaleDateString('ru-RU',{day:'2-digit',month:'short'});
    }
    if(s<5)return 'Hozir';
    if(s<60)return s+' soniya oldin';
    if(s<3600)return Math.floor(s/60)+' daq. oldin';
    if(s<86400)return Math.floor(s/3600)+' soat oldin';
    if(s<2592000)return Math.floor(s/86400)+' kun oldin';
    return d.toLocaleDateString('uz-UZ',{day:'2-digit',month:'short'});
  }catch(e){return '';}
}

/* ─── TOP BAR ─── */
async function renderTopbar() {
  var nav = document.getElementById('topbar');
  if(!nav) return;
  var me = await getMe();
  var loggedIn = me.logged_in;
  var isAdmin = me.role==='admin'||me.role==='moderator';
  var path = window.location.pathname;

  var loggedLinks = [
    {href:'/dashboard',   label:t('nav_dashboard')||'Dashboard',  icon:''},
    {href:'/#courses',    label:t('nav_courses')||'Kurslar',       icon:''},
    {href:'/games',       label:t('nav_games')||"O'yinlar",        icon:''},
    {href:'/leaderboard', label:t('nav_leaderboard')||'Reyting',   icon:''},
    {href:'/problems',    label:t('nav_problems')||'Masalalar',    icon:''},
    {href:'/blog',        label:t('nav_blog')||'Blog',             icon:''},
    {href:'/social',      label:t('nav_social')||"Do'stlar",       icon:''},
    {href:'/groups',      label:t('nav_groups')||'Guruhlar',       icon:''},
    {href:'/store',       label:t('nav_store')||"Do'kon",          icon:''},
    {href:'/chat',        label:t('nav_chat')||'Chat',             icon:''},
    {href:'/streak',      label:'🔥 Streak',                        icon:''},
  ];
  var guestLinks = [
    {href:'/',            label:'Bosh sahifa', icon:'🏠'},
    {href:'/#courses',    label:'Kurslar',     icon:'📚'},
    {href:'/leaderboard', label:'Reyting',     icon:'🏆'},
  ];
  var links = loggedIn ? loggedLinks : guestLinks;

  function isAct(href){var h=href.split('#')[0];if(h==='/')return path==='/';return path===h||path.startsWith(h+'/');}

  nav.innerHTML = '<div class="topbar-inner">'
    + '<a class="topbar-brand" href="/"><img src="/static/images/logo.png" alt="B" class="topbar-logo" onerror="this.style.display=\'none\'"><span class="topbar-name">Bilimxon</span></a>'
    + '<div class="topbar-links" id="tbLinks">'+links.map(function(l){return '<a class="topbar-link'+(isAct(l.href)?' active':'')+'" href="'+l.href+'">'+l.icon+' '+l.label+'</a>';}).join('')+'</div>'
    + '<div class="topbar-right">'
    + (loggedIn
      ? '<div class="topbar-points">⭐ <span id="navPts">...</span></div>'
        + '<div style="position:relative;"><button class="topbar-icon-btn" id="notifBtn" onclick="openNotifications()" title="Bildirishnomalar">🔔<span id="notifBadge" style="display:none;position:absolute;top:-5px;right:-5px;min-width:16px;height:16px;background:#EF4444;color:white;border-radius:999px;font-size:.58rem;font-weight:800;align-items:center;justify-content:center;padding:0 3px;border:2px solid #0d1b2e;"></span></button></div>'
        + (isAdmin?'<a class="topbar-admin-btn" href="/admin">👑 Admin</a>':'')
        + '<a class="topbar-avatar" href="/profile/'+me.username+'" id="navAv">'+(me.username||'?')[0].toUpperCase()+'</a>'
        + '<button class="topbar-logout" onclick="doLogout()" title="Chiqish">↩</button>'
        + '<div class="lang-switcher"><button class="lang-btn'+(CURRENT_LANG==='uz'?' active':'')+'" onclick="setLang(\'uz\')">UZ</button><button class="lang-btn'+(CURRENT_LANG==='ru'?' active':'')+'" onclick="setLang(\'ru\')">RU</button><button class="lang-btn'+(CURRENT_LANG==='en'?' active':'')+'" onclick="setLang(\'en\')">EN</button></div>'
      : '<div class="lang-switcher"><button class="lang-btn'+(CURRENT_LANG==='uz'?' active':'')+'" onclick="setLang(\'uz\')">UZ</button><button class="lang-btn'+(CURRENT_LANG==='ru'?' active':'')+'" onclick="setLang(\'ru\')">RU</button><button class="lang-btn'+(CURRENT_LANG==='en'?' active':'')+'" onclick="setLang(\'en\')">EN</button></div>'
        + '<a class="btn btn-primary btn-sm" href="/login">Kirish</a>')
    + (loggedIn ? '<a class="topbar-icon-btn" href="/settings" title="Sozlamalar" style="text-decoration:none;">⚙️</a>' : '')
    + '<button class="topbar-menu-btn" onclick="toggleMenu()">☰</button>'
    + '</div></div>'
    + '<div id="notifPanel" style="display:none;position:fixed;top:68px;right:12px;width:360px;max-width:calc(100vw - 24px);background:white;border-radius:18px;box-shadow:0 16px 48px rgba(0,0,0,.28);border:1px solid #E5E7EB;z-index:99999;max-height:500px;overflow-y:auto;"></div>'
    + '<div class="topbar-mobile" id="topbarMobile" style="display:none;">'
    + links.map(function(l){return '<a class="mobile-link" href="'+l.href+'">'+l.icon+' '+l.label+'</a>';}).join('')
    + (isAdmin?'<a class="mobile-link" href="/admin">👑 Admin Panel</a>':'')
    + (loggedIn?'<a class="mobile-link" href="/profile/'+me.username+'">👤 @'+me.username+'</a><a class="mobile-link" href="#" onclick="doLogout()">↩ Chiqish</a>':'<a class="mobile-link" href="/login" style="color:#C9A84C;font-weight:800;">🔑 Kirish / Ro\'yxatdan O\'tish</a>')
    + '</div>';

  // Close notif on outside click
  document.addEventListener('click', function(e){
    var panel=document.getElementById('notifPanel'), btn=document.getElementById('notifBtn');
    if(panel&&btn&&!panel.contains(e.target)&&!btn.contains(e.target)) panel.style.display='none';
  });

  if(loggedIn){
    // Load profile data and notifications in parallel (non-blocking)
    Promise.all([
      api('/api/profile/'+me.username),
      api('/api/notifications/count')
    ]).then(function(results){
      var u=results[0], nc=results[1];
      var el=document.getElementById('navPts'); if(el) el.textContent=(u.points||0).toLocaleString();
      var av=document.getElementById('navAv'); if(av&&u.avatar) av.innerHTML='<img src="'+u.avatar+'" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">';
      var cnt=nc.count||0;
      var b=document.getElementById('notifBadge');
      if(b){b.textContent=cnt>9?'9+':cnt;b.style.display=cnt>0?'flex':'none';}
      _nc=cnt; _ncPrev=cnt;
    }).catch(function(){});
    // Start SSE + fallback polling
    _startSSE();
    setInterval(_loadNC, 30000);
  }
}

function _startSSE() {
  if(typeof EventSource === 'undefined') return;
  try {
    var es = new EventSource('/api/notifications/stream');
    es.onopen = function() { _sseActive = true; };
    es.onmessage = function(e) {
      try {
        var n = JSON.parse(e.data);
        _nc++;
        _ncPrev = _nc;
        var b = document.getElementById('notifBadge');
        if(b){b.textContent=_nc>9?'9+':_nc;b.style.display='flex';}
        var icons = {friend_req:'👥',friend_acc:'✅',game_approved:'🎮',game_rejected:'❌',message:'💬',gift:'🎁',system:'🔔'};
        var icon = icons[n.notif_type]||'🔔';
        showToast(icon+' '+n.title+(n.body?': '+n.body.slice(0,50):''), n.notif_type==='game_rejected'?'warning':'info', 5500);
      }catch(err){}
    };
    es.onerror = function(){ _sseActive = false; es.close(); };
  } catch(err) { _sseActive = false; }
}

function toggleMenu(){var m=document.getElementById('topbarMobile');if(m)m.style.display=m.style.display==='none'?'block':'none';}

async function doLogout(){
  try{await api('/api/logout',{method:'POST'});}catch(e){}
  _me=null; window.location.href='/login';
}

/* ─── Apply Theme Settings ─── */
function applyToPage(cfg) {
  if (!cfg) return;
  var root = document.documentElement;
  if (cfg.bg) document.body.style.background = cfg.bg;
  if (cfg.accent1 && cfg.accent2) {
    root.style.setProperty('--gold', cfg.accent1);
    root.style.setProperty('--gold-light', cfg.accent1);
    root.style.setProperty('--gold-dark', cfg.accent2);
    root.style.setProperty('--navy', cfg.accent2);
  }
  if (cfg.font) document.body.style.fontFamily = cfg.font;
  if (cfg.radius) root.style.setProperty('--radius', cfg.radius + 'px');
  if (cfg.fontSize) root.style.setProperty('font-size', cfg.fontSize + 'px');
}

function _loadAndApplySettings() {
  try {
    var s = localStorage.getItem('bx_settings_v1');
    if (s) applyToPage(JSON.parse(s));
  } catch(e) {}
}
_loadAndApplySettings();

/* ─── DOMContentLoaded ─── */
document.addEventListener('DOMContentLoaded', function(){
  renderTopbar();
  if(typeof applyI18n==='function') applyI18n();
});

/* ─────────────────────────────────────────
   SOURCE CODE PROTECTION
   ───────────────────────────────────────── */
(function() {
  // Disable right-click context menu
  document.addEventListener('contextmenu', function(e) {
    e.preventDefault();
    return false;
  });

  // Disable dangerous keyboard shortcuts
  document.addEventListener('keydown', function(e) {
    var key = e.key ? e.key.toLowerCase() : '';
    var ctrl = e.ctrlKey || e.metaKey;

    // Ctrl+U (view source), Ctrl+S (save), Ctrl+Shift+I/J/C (DevTools)
    if (ctrl && key === 'u') { e.preventDefault(); return false; }
    if (ctrl && key === 's') { e.preventDefault(); return false; }
    if (ctrl && e.shiftKey && (key === 'i' || key === 'j' || key === 'c')) { e.preventDefault(); return false; }
    if (ctrl && e.shiftKey && key === 'k') { e.preventDefault(); return false; }
    // F12 DevTools
    if (e.key === 'F12') { e.preventDefault(); return false; }
    // Ctrl+P (print - shows source)
    if (ctrl && key === 'p') { e.preventDefault(); return false; }
  }, true);

  // Clear console periodically  
  var _consoleClear = setInterval(function() {
    try { console.clear(); } catch(e) {}
  }, 2000);

  // Console warning
  setTimeout(function() {
    try {
      console.log('%c⛔ TO\'XTAN!', 'color:red;font-size:24px;font-weight:900;');
      console.log('%cBu joy faqat dasturchilar uchun. Kodlarni nusxalash taqiqlangan.', 'color:#ff6b6b;font-size:14px;');
    } catch(e) {}
  }, 500);

  // Disable text selection on right-click
  document.addEventListener('selectstart', function(e) {
    if (e.shiftKey) return;
    // Allow selection in inputs/textareas
    var tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea') return;
  });
})();

/* ─────────────────────────────────────────
   MOBILE RESPONSIVE GLOBAL FIXES
   ───────────────────────────────────────── */
(function addMobileStyles() {
  var style = document.createElement('style');
  style.textContent = `
    /* ── Mobile Nav ── */
    @media (max-width: 768px) {
      .topbar-links { display: none !important; }
      .topbar-brand .topbar-name { font-size: .85rem; }
      .topbar-inner { padding: 0 12px; }
    }
    /* ── Hamburger for mobile ── */
    .mob-menu-btn {
      display: none;
      background: rgba(255,255,255,.08);
      border: none; color: #fff;
      width: 36px; height: 36px;
      border-radius: 8px; font-size: 1.1rem;
      cursor: pointer; align-items: center;
      justify-content: center;
    }
    @media (max-width: 768px) {
      .mob-menu-btn { display: flex !important; }
    }
    /* Mobile slide menu */
    .mob-menu-overlay {
      display: none; position: fixed;
      inset: 0; background: rgba(0,0,0,.6);
      z-index: 888; top: var(--topbar-h, 60px);
    }
    .mob-menu-overlay.open { display: block; }
    .mob-menu {
      position: fixed; top: var(--topbar-h, 60px);
      left: 0; bottom: 0; width: 280px;
      background: #0d1117; z-index: 889;
      overflow-y: auto; transform: translateX(-100%);
      transition: transform .25s ease;
      border-right: 1px solid #21262d;
      padding: 16px 0 40px;
    }
    .mob-menu.open { transform: translateX(0); }
    .mob-menu a {
      display: flex; align-items: center; gap: 12px;
      padding: 12px 20px; color: #e6edf3;
      text-decoration: none; font-size: .9rem;
      font-weight: 600; transition: .15s;
      border-radius: 0;
    }
    .mob-menu a:hover, .mob-menu a.active {
      background: rgba(255,255,255,.06); color: #fff;
    }
    .mob-menu .mob-sep {
      height: 1px; background: #21262d;
      margin: 8px 16px;
    }

    /* ── General mobile fixes ── */
    @media (max-width: 600px) {
      /* Blog layout */
      .page { flex-direction: column; }
      .sidebar { display: none !important; }
      .g-sidebar { display: none !important; }
      /* Games grid */
      .g-grid-lg { grid-template-columns: repeat(2, 1fr) !important; gap: 3px !important; }
      /* Profile */
      .channel-inner { padding: 12px 14px 0; }
      .ch-avatar { width: 72px !important; height: 72px !important; }
      .ch-name { font-size: 1.1rem !important; }
      .ch-actions { flex-wrap: wrap; gap: 6px; }
      .ch-btn { padding: 7px 12px; font-size: .78rem; }
      .ch-tabs { padding: 0; }
      .ch-tab { padding: 10px 12px; font-size: .8rem; }
      .ch-content { padding: 14px 14px 60px; }
      /* Problems */
      .problems-wrap { padding-left: 12px; padding-right: 12px; }
      /* Shorts player full screen on mobile */
      #shortsPlayer { top: 0 !important; }
      .sp-video-wrap { max-width: 100% !important; }
      .sp-nav { right: 8px; top: auto; bottom: 55%; }
    }

    @media (max-width: 480px) {
      .stats-cards { grid-template-columns: 1fr 1fr !important; }
      .vid-grid { grid-template-columns: 1fr 1fr !important; }
      .page-title { font-size: 1.2rem; }
      .feed-wrap { padding: 12px 8px 80px; }
      .video-grid { padding: 0 6px 16px; }
      .section-head { padding: 14px 12px 10px; }
      .cat-bar { padding: 10px 10px; }
      .feed-tabs { padding: 0 10px; }
    }
  `;
  document.head.appendChild(style);
})();

/* ─────────────────────────────────────────
   MOBILE HAMBURGER MENU
   ───────────────────────────────────────── */
function initMobileMenu() {
  if (window.innerWidth > 768) return;
  if (document.getElementById('mobMenuBtn')) return;

  var topbarRight = document.querySelector('.topbar-right');
  if (!topbarRight) return;

  var btn = document.createElement('button');
  btn.className = 'mob-menu-btn';
  btn.id = 'mobMenuBtn';
  btn.innerHTML = '☰';
  btn.title = 'Menyu';
  topbarRight.insertBefore(btn, topbarRight.firstChild);

  var overlay = document.createElement('div');
  overlay.className = 'mob-menu-overlay';
  overlay.id = 'mobMenuOverlay';

  var menu = document.createElement('div');
  menu.className = 'mob-menu';
  menu.id = 'mobMenu';

  var links = [
    {href:'/dashboard', icon:'📊', label:'Dashboard'},
    {href:'/#courses', icon:'📚', label:'Kurslar'},
    {href:'/games', icon:'🎮', label:"O'yinlar"},
    {href:'/leaderboard', icon:'🏆', label:'Reyting'},
    {href:'/problems', icon:'🧩', label:'Masalalar'},
    {href:'/blog', icon:'📰', label:'Blog & Shorts'},
    {href:'/social', icon:'👥', label:"Do'stlar"},
    {href:'/groups', icon:'🌐', label:'Guruhlar'},
    {href:'/store', icon:'🛒', label:"Do'kon"},
    {href:'/chat', icon:'💬', label:'Chat'},
    {href:'/settings', icon:'⚙️', label:'Sozlamalar'},
  ];
  var path = window.location.pathname;
  menu.innerHTML = links.map(function(l) {
    var active = (l.href === path || path.startsWith(l.href+'/')) ? ' active' : '';
    return '<a href="'+l.href+'" class="'+active+'"><span style="font-size:1.1rem;width:24px;text-align:center;">'+l.icon+'</span>'+l.label+'</a>';
  }).join('<div class="mob-sep"></div>');

  document.body.appendChild(overlay);
  document.body.appendChild(menu);

  function toggle(open) {
    menu.classList.toggle('open', open);
    overlay.classList.toggle('open', open);
    btn.innerHTML = open ? '✕' : '☰';
  }
  btn.addEventListener('click', function() { toggle(!menu.classList.contains('open')); });
  overlay.addEventListener('click', function() { toggle(false); });
}

document.addEventListener('DOMContentLoaded', function() {
  setTimeout(initMobileMenu, 300);
});
window.addEventListener('resize', function() {
  if (window.innerWidth > 768) {
    var m = document.getElementById('mobMenu');
    if (m) m.classList.remove('open');
    var o = document.getElementById('mobMenuOverlay');
    if (o) o.classList.remove('open');
  }
});

/* ─────────────────────────────────────────
   FLOATING SUPPORT WIDGET
   ───────────────────────────────────────── */
(function initSupportWidget() {
  // Wait for DOM
  function buildWidget() {
    if(document.getElementById('supportWidgetBtn')) return;

    var style = document.createElement('style');
    style.textContent = `
      #supportWidgetBtn {
        position: fixed; bottom: 24px; right: 24px; z-index: 8000;
        width: 48px; height: 48px; border-radius: 50%;
        background: linear-gradient(135deg,#1B3A6B,#C9A84C);
        border: none; color: #fff; font-size: 1.2rem;
        cursor: pointer; box-shadow: 0 4px 16px rgba(0,0,0,.35);
        display: flex; align-items: center; justify-content: center;
        transition: .2s; font-family: inherit;
      }
      #supportWidgetBtn:hover { transform: scale(1.1); }
      #supportWidgetPanel {
        position: fixed; bottom: 82px; right: 24px; z-index: 8001;
        width: 340px; max-width: calc(100vw - 32px);
        background: #161b22; border: 1px solid #21262d; border-radius: 16px;
        box-shadow: 0 12px 40px rgba(0,0,0,.5);
        display: none; flex-direction: column;
        font-family: 'Outfit', sans-serif; overflow: hidden;
      }
      #supportWidgetPanel.open { display: flex; }
      .sw-head {
        padding: 14px 16px; background: linear-gradient(135deg,#0d1b3e,#1a1040);
        display: flex; align-items: center; justify-content: space-between;
        border-bottom: 1px solid #21262d;
      }
      .sw-head-title { font-weight: 800; color: #fff; font-size: .9rem; }
      .sw-close { background: none; border: none; color: #aaa; cursor: pointer; font-size: 1rem; padding: 4px; }
      .sw-body { padding: 14px; overflow-y: auto; max-height: 420px; }
      .sw-tabs { display: flex; gap: 6px; margin-bottom: 12px; }
      .sw-tab {
        flex: 1; padding: 7px 4px; border-radius: 10px; text-align: center;
        border: 1.5px solid #21262d; background: transparent; color: #888;
        font-size: .72rem; font-weight: 700; cursor: pointer; transition: .15s;
        font-family: inherit;
      }
      .sw-tab.active { border-color: #C9A84C; color: #C9A84C; background: rgba(201,168,76,.08); }
      .sw-label { font-size: .72rem; font-weight: 700; color: #666; text-transform: uppercase; letter-spacing: .04em; margin-bottom: 5px; display: block; }
      .sw-input { width: 100%; background: #0d1117; border: 1.5px solid #21262d; border-radius: 8px; padding: 8px 11px; color: #fff; font-size: .82rem; font-family: inherit; outline: none; box-sizing: border-box; }
      .sw-input:focus { border-color: #444; }
      .sw-input::placeholder { color: #444; }
      .sw-textarea { resize: vertical; min-height: 80px; }
      .sw-hint { background: rgba(201,168,76,.06); border: 1px solid rgba(201,168,76,.12); border-radius: 8px; padding: 8px 10px; font-size: .73rem; color: rgba(255,255,255,.45); margin-bottom: 10px; line-height: 1.4; }
      .sw-send { width: 100%; padding: 10px; background: linear-gradient(135deg,#C9A84C,#8B6914); border: none; border-radius: 10px; color: #fff; font-weight: 800; cursor: pointer; font-family: inherit; font-size: .85rem; margin-top: 8px; }
      .sw-send:disabled { opacity: .45; cursor: not-allowed; }
      .sw-vacancy-list { display: flex; flex-direction: column; gap: 8px; }
      .sw-vacancy-item { background: rgba(255,255,255,.04); border: 1px solid #21262d; border-radius: 10px; padding: 10px 12px; }
      .sw-vacancy-title { font-weight: 800; color: #fff; font-size: .85rem; margin-bottom: 4px; }
      .sw-vacancy-desc { font-size: .75rem; color: #888; margin-bottom: 6px; line-height: 1.4; }
      .sw-vacancy-req { font-size: .72rem; color: #C9A84C; }
      .sw-my-tickets { margin-top: 12px; border-top: 1px solid #21262d; padding-top: 12px; }
      .sw-ticket-item { background: rgba(255,255,255,.03); border-radius: 8px; padding: 8px 10px; margin-bottom: 6px; border-left: 2px solid #333; }
      .sw-ticket-status-open { color: #fbbf24; font-size: .65rem; font-weight: 800; }
      .sw-ticket-status-resolved { color: #4ade80; font-size: .65rem; font-weight: 800; }
    `;
    document.head.appendChild(style);

    // Create button
    var btn = document.createElement('button');
    btn.id = 'supportWidgetBtn';
    btn.title = 'Yordam';
    btn.innerHTML = '🛠️';

    // Create panel
    var panel = document.createElement('div');
    panel.id = 'supportWidgetPanel';
    panel.innerHTML = `
      <div class="sw-head">
        <span class="sw-head-title">🛠️ Qo'llab-Quvvatlash</span>
        <button class="sw-close" onclick="document.getElementById('supportWidgetPanel').classList.remove('open')">✕</button>
      </div>
      <div class="sw-body" id="swBody">
        <div class="sw-tabs">
          <button class="sw-tab active" onclick="_swTab('bug',this)">🐛 Bug</button>
          <button class="sw-tab" onclick="_swTab('question',this)">❓ Savol</button>
          <button class="sw-tab" onclick="_swTab('vacancy',this)">💼 Ish</button>
        </div>
        <div id="swFormWrap">
          <div class="sw-hint" id="swHint">🐛 <strong style="color:rgba(255,255,255,.8);">Bug:</strong> Nima xato yuz berdi, qaysi sahifada? Moderatorgа yetkaziladi.</div>
          <label class="sw-label">Mavzu</label>
          <input class="sw-input" id="swSubject" placeholder="Qisqa mavzu..." style="margin-bottom:8px;">
          <label class="sw-label" id="swMsgLabel">Xabar</label>
          <textarea class="sw-input sw-textarea" id="swMessage" placeholder="Batafsil yozing..."></textarea>
          <button class="sw-send" id="swSendBtn" onclick="_swSend()">📤 Yuborish</button>
        </div>
        <div id="swVacancyWrap" style="display:none;">
          <div class="sw-hint">💼 Quyidagi bo'sh lavozimlardan birini tanlang va ariza qoldiring.</div>
          <div class="sw-vacancy-list" id="swVacancyList">
            <div style="color:#555;font-size:.8rem;text-align:center;padding:10px;">Yuklanmoqda...</div>
          </div>
          <div id="swVacancyForm" style="display:none;margin-top:10px;">
            <input type="hidden" id="swVacTitle">
            <div style="background:rgba(201,168,76,.08);border:1px solid rgba(201,168,76,.2);border-radius:10px;padding:10px 12px;font-size:.8rem;color:#C9A84C;font-weight:800;margin-bottom:10px;display:flex;align-items:center;gap:6px;" id="swVacSelected">💼</div>
            <label class="sw-label">Telegram username *</label>
            <div style="position:relative;margin-bottom:8px;">
              <span style="position:absolute;left:10px;top:50%;transform:translateY(-50%);color:#555;font-size:.85rem;">@</span>
              <input class="sw-input" id="swVacTelegram" placeholder="username" style="padding-left:26px;">
            </div>
            <label class="sw-label">Tajriba va ko'nikmalar</label>
            <textarea class="sw-input sw-textarea" id="swVacMessage" placeholder="Tajribangiz, ko'nikmalaringiz, nima qila olasiz..."></textarea>
            <div style="background:rgba(42,171,238,.08);border-radius:8px;padding:8px 10px;font-size:.72rem;color:rgba(255,255,255,.45);margin-top:8px;line-height:1.4;">
              ✈️ Admin telegram orqali siz bilan bog'lanadi. Telegram username to'g'ri kiriting.
            </div>
            <div style="display:flex;gap:6px;margin-top:8px;">
              <button onclick="document.getElementById('swVacancyForm').style.display='none';document.getElementById('swVacancyList').style.display='';" style="flex:1;padding:8px;background:rgba(255,255,255,.06);border:1px solid #21262d;border-radius:8px;color:#aaa;cursor:pointer;font-family:inherit;font-size:.78rem;">← Orqaga</button>
              <button class="sw-send" style="flex:2;margin-top:0;" onclick="_swSendVacancy()">📤 Ariza yuborish</button>
            </div>
          </div>
        </div>
        <div class="sw-my-tickets" id="swMyTickets"></div>
      </div>`;

    document.body.appendChild(btn);
    document.body.appendChild(panel);

    btn.addEventListener('click', function() {
      panel.classList.toggle('open');
      if(panel.classList.contains('open')) {
        _swLoadTickets();
        // Load vacancies if on vacancy tab
      }
    });

    // Close on outside click
    document.addEventListener('click', function(e) {
      // Don't close if clicking inside panel or on the open button
      if(!panel.contains(e.target) && e.target !== btn && !btn.contains(e.target)) {
        panel.classList.remove('open');
      }
    });

    // Load vacancies
    fetch('/api/vacancies').then(r=>r.json()).then(vacs => {
      var list = document.getElementById('swVacancyList');
      if(!list) return;
      if(!vacs.length) {
        list.innerHTML = '<div style="color:#555;font-size:.78rem;text-align:center;padding:12px;">Hozircha bo\'sh lavozim yo\'q</div>';
        return;
      }
      list.innerHTML = vacs.map(v => `<div class="sw-vacancy-item">
        <div class="sw-vacancy-title">${v.title}</div>
        ${v.description ? `<div class="sw-vacancy-desc">${v.description}</div>` : ''}
        ${v.requirements ? `<div class="sw-vacancy-req">📋 ${v.requirements}</div>` : ''}
        <button data-vtitle="${v.title.replace(/"/g,'&quot;')}" data-vid="${v.id}" onclick="_swSelectVacancy(this.dataset.vtitle,this.dataset.vid)" style="margin-top:8px;padding:5px 12px;background:linear-gradient(135deg,#C9A84C,#8B6914);border:none;border-radius:8px;color:#fff;font-size:.72rem;font-weight:800;cursor:pointer;font-family:inherit;">Ariza qoldirish →</button>
      </div>`).join('');
    }).catch(()=>{});
  }

  window._swCurrentType = 'bug';
  var HINTS = {
    bug: '🐛 <strong style="color:rgba(255,255,255,.8);">Bug:</strong> Nima xato yuz berdi, qaysi sahifada? Moderatorgа yetkaziladi.',
    question: '❓ <strong style="color:rgba(255,255,255,.8);">Savol:</strong> Savolingizni yozing. Moderator javob beradi.',
  };
  var MSG_LABELS = {bug:'Xato tavsifi', question:'Savolingiz'};

  window._swTab = function(type, el) {
    window._swCurrentType = type;
    document.querySelectorAll('.sw-tab').forEach(b => b.classList.remove('active'));
    el.classList.add('active');
    var formWrap = document.getElementById('swFormWrap');
    var vacWrap = document.getElementById('swVacancyWrap');
    if(type === 'vacancy') {
      formWrap.style.display = 'none'; vacWrap.style.display = '';
      // Reset vacancy form state
      var vForm = document.getElementById('swVacancyForm');
      var vList = document.getElementById('swVacancyList');
      if(vForm) vForm.style.display = 'none';
      if(vList) vList.style.display = '';
      // Reload vacancies fresh
      _swLoadVacancies();
    } else {
      formWrap.style.display = ''; vacWrap.style.display = 'none';
      document.getElementById('swHint').innerHTML = HINTS[type]||'';
      document.getElementById('swMsgLabel').textContent = MSG_LABELS[type]||'Xabar';
    }
  };

  window._swLoadVacancies = function() {
    var list = document.getElementById('swVacancyList');
    if(!list) return;
    list.innerHTML = '<div style="color:#555;font-size:.8rem;text-align:center;padding:10px;">Yuklanmoqda...</div>';
    fetch('/api/vacancies').then(r=>r.json()).then(vacs => {
      if(!vacs.length) {
        list.innerHTML = '<div style="color:#555;font-size:.78rem;text-align:center;padding:12px;">Hozircha bo\'sh lavozim yo\'q</div>';
        return;
      }
      list.innerHTML = vacs.map(v => `<div class="sw-vacancy-item">
        <div class="sw-vacancy-title">${v.title}</div>
        ${v.description ? `<div class="sw-vacancy-desc">${v.description}</div>` : ''}
        ${v.requirements ? `<div class="sw-vacancy-req">📋 ${v.requirements}</div>` : ''}
        <button data-vtitle="${v.title.replace(/"/g,'&quot;')}" data-vid="${v.id}" onclick="_swSelectVacancy(this.dataset.vtitle,this.dataset.vid)" style="margin-top:8px;padding:6px 14px;background:linear-gradient(135deg,#C9A84C,#8B6914);border:none;border-radius:8px;color:#fff;font-size:.75rem;font-weight:800;cursor:pointer;font-family:inherit;width:100%;">💼 Ariza qoldirish →</button>
      </div>`).join('');
    }).catch(()=>{
      if(list) list.innerHTML = '<div style="color:#f87171;font-size:.78rem;text-align:center;padding:12px;">Yuklab bo\'lmadi</div>';
    });
  };

  window._swSelectVacancy = function(title, vacId) {
    document.getElementById('swVacTitle').value = title;
    document.getElementById('swVacSelected').innerHTML = '💼 ' + title;
    document.getElementById('swVacancyList').style.display = 'none';
    document.getElementById('swVacancyForm').style.display = '';
    // Clear previous inputs
    var tg = document.getElementById('swVacTelegram');
    var msg = document.getElementById('swVacMessage');
    if(tg) tg.value = '';
    if(msg) msg.value = '';
    setTimeout(() => document.getElementById('swVacTelegram')?.focus(), 100);
  };

  window._swSend = async function() {
    var subject = document.getElementById('swSubject')?.value.trim();
    var message = document.getElementById('swMessage')?.value.trim();
    if(!subject) { alert('Mavzu kiriting!'); return; }
    if(!message) { alert('Xabar yozing!'); return; }
    var btn = document.getElementById('swSendBtn');
    btn.disabled = true; btn.textContent = '⏳...';
    try {
      var r = await fetch('/api/support/submit', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({type:window._swCurrentType, subject, message})});
      var d = await r.json();
      if(d.success) {
        document.getElementById('swSubject').value = '';
        document.getElementById('swMessage').value = '';
        document.getElementById('swBody').innerHTML = '<div style="text-align:center;padding:30px 20px;"><div style="font-size:2.5rem;margin-bottom:12px;">✅</div><div style="font-weight:800;color:#fff;margin-bottom:6px;">Yuborildi!</div><div style="font-size:.8rem;color:#888;">Tez orada javob beramiz.</div><button onclick="document.getElementById(\'supportWidgetPanel\').classList.remove(\'open\')" style="margin-top:14px;padding:8px 20px;background:rgba(255,255,255,.08);border:1px solid #21262d;border-radius:8px;color:#aaa;cursor:pointer;font-family:inherit;">Yopish</button></div>';
      } else { alert(d.error || 'Xato'); btn.disabled=false; btn.textContent='📤 Yuborish'; }
    } catch(e) { alert('Xato: ' + e.message); btn.disabled=false; btn.textContent='📤 Yuborish'; }
  };

  window._swSendVacancy = async function() {
    var title = document.getElementById('swVacTitle').value;
    var telegram = (document.getElementById('swVacTelegram')?.value || '').trim().replace(/^@/,'');
    var message = (document.getElementById('swVacMessage')?.value || '').trim();
    if(!telegram) { 
      document.getElementById('swVacTelegram').style.borderColor = '#f87171';
      alert('Telegram username kiriting!'); 
      document.getElementById('swVacTelegram').focus();
      return; 
    }
    var fullMsg = 'Telegram: @' + telegram + (message ? '\n\n' + message : '');
    try {
      var r = await fetch('/api/support/submit', {
        method:'POST', 
        headers:{'Content-Type':'application/json'}, 
        body:JSON.stringify({type:'vacancy', subject:'Vakansiya: ' + title, message: fullMsg})
      });
      var d = await r.json();
      if(d.success) {
        document.getElementById('swBody').innerHTML = '<div style="text-align:center;padding:30px 20px;"><div style="font-size:2.5rem;margin-bottom:12px;">✅</div><div style="font-weight:800;color:#fff;margin-bottom:8px;">Ariza yuborildi!</div><div style="font-size:.8rem;color:#aaa;line-height:1.5;">Bilimxon jamoasi <strong style="color:#fff;">@' + telegram + '</strong> telegram orqali siz bilan bog\'lanadi.</div><button onclick="document.getElementById(\'supportWidgetPanel\').classList.remove(\'open\')" style="margin-top:16px;padding:8px 20px;background:rgba(255,255,255,.08);border:1px solid #21262d;border-radius:8px;color:#aaa;cursor:pointer;font-family:inherit;">Yopish</button></div>';
      } else alert(d.error || 'Xato');
    } catch(e) { alert('Xato: ' + e.message); }
  };

  window._swLoadTickets = async function() {
    var el = document.getElementById('swMyTickets');
    if(!el) return;
    try {
      var r = await fetch('/api/support/tickets');
      if(!r.ok) { el.innerHTML=''; return; }
      var tickets = await r.json();
      if(!tickets.length) { el.innerHTML=''; return; }
      el.innerHTML = '<div style="font-size:.7rem;font-weight:700;color:#555;text-transform:uppercase;margin-bottom:8px;">Mening murojaatlarim</div>' +
        tickets.slice(0,3).map(t => `<div class="sw-ticket-item">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;">
            <span style="font-size:.78rem;font-weight:700;color:#fff;">${t.subject}</span>
            <span class="${t.status==='resolved'?'sw-ticket-status-resolved':'sw-ticket-status-open'}">${t.status==='resolved'?'✅':'⏳'}</span>
          </div>
          ${t.reply ? `<div style="font-size:.72rem;color:#4ade80;margin-top:4px;"><strong>Javob:</strong> ${t.reply}</div>` : ''}
        </div>`).join('');
    } catch(e) { el.innerHTML=''; }
  };

  if(document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', buildWidget);
  } else {
    setTimeout(buildWidget, 500);
  }
})();

/* ─────────────────────────────────────────
   COOKIE / PRIVACY ONBOARDING WIDGET
   ───────────────────────────────────────── */
(function initOnboarding() {
  // Check if already accepted
  if (document.cookie.includes('bx_privacy=1')) return;

  var STEPS = [
    {
      icon: '👋',
      title: "Bilimxon-ga xush kelibsiz!",
      body: "O'zbekistonning #1 IT ta'lim platformasi. HTML, Python, JavaScript va boshqa zamonaviy texnologiyalarni bepul, qiziqarli tarzda o'rganing.",
      btn: "Davom etish →",
      sub: '<a href="/about" style="color:#C9A84C;font-size:.75rem;">Biz haqimizda</a>'
    },
    {
      icon: '🍪',
      title: "Cookie va Maxfiylik",
      body: "Bilimxon tizim ishlashi uchun zarur cookie fayllardan foydalanadi (sessiya, til). Ma'lumotlaringiz xavfsiz saqlanadi va hech kimga sotilmaydi.",
      btn: "Roziman →",
      sub: '<a href="/cookie" style="color:#C9A84C;font-size:.75rem;">Cookie</a> · <a href="/privacy" style="color:#C9A84C;font-size:.75rem;">Maxfiylik</a>'
    },
    {
      icon: '📄',
      title: "Foydalanish Shartlari",
      body: "Platforma qoidalari: hurmatli muloqot, halol foydalanish. Parollar shifrlangan, ma'lumotlar himoyalangan. Qoidalarni buzish hisobni bloklaydi.",
      btn: "Qabul qilaman →",
      sub: '<a href="/terms" style="color:#C9A84C;font-size:.75rem;">Shartlarni o\'qish</a>'
    },
    {
      icon: '🚀',
      title: "Boshlashga tayyormisiz?",
      body: "Bepul ro'yxatdan o'ting va 50+ kurs, 500+ masala, AI yordamchi va ko'p narsaga kirish oling!\n\n📧 bilimxon5@gmail.com   ✈️ @bilimxonuz",
      btn: "🎉 Boshlash!",
      sub: '<a href="/contact" style="color:#C9A84C;font-size:.75rem;">Aloqa</a> · <a href="/about" style="color:#C9A84C;font-size:.75rem;">Biz haqimizda</a>'
    }
  ];

  var currentStep = 0;

  function buildOnboarding() {
    if (document.getElementById('bxOnboarding')) return;

    var style = document.createElement('style');
    style.textContent = `
      #bxOnboardingOverlay {
        position:fixed;inset:0;background:rgba(0,0,0,.72);z-index:8500;
        display:flex;align-items:center;justify-content:center;
        padding:20px;
        backdrop-filter:blur(4px);
        animation:bxFadeIn .3s ease;
      }
      @keyframes bxFadeIn{from{opacity:0}to{opacity:1}}
      #bxOnboarding {
        width:420px;max-width:calc(100vw - 32px);
        background:linear-gradient(145deg,#161b22,#0d1117);
        border:1px solid rgba(201,168,76,.25);
        border-radius:20px;
        box-shadow:0 20px 60px rgba(0,0,0,.6),0 0 0 1px rgba(255,255,255,.05);
        font-family:'Outfit',sans-serif;
        overflow:hidden;
        animation:bxSlideUp .35s cubic-bezier(.34,1.56,.64,1);
      }
      @keyframes bxSlideUp{from{transform:translateY(40px);opacity:0}to{transform:translateY(0);opacity:1}}
      .bx-ob-head {
        padding:20px 20px 0;
        display:flex;align-items:center;justify-content:space-between;
      }
      .bx-ob-dots {
        display:flex;gap:5px;
      }
      .bx-ob-dot {
        width:6px;height:6px;border-radius:3px;
        background:rgba(255,255,255,.15);
        transition:.3s;
      }
      .bx-ob-dot.active {
        background:#C9A84C;width:18px;
      }
      .bx-ob-dot.done {
        background:rgba(201,168,76,.4);
      }
      .bx-ob-skip {
        background:none;border:none;color:rgba(255,255,255,.3);
        font-size:.72rem;cursor:pointer;font-family:inherit;padding:2px 6px;
      }
      .bx-ob-skip:hover{color:rgba(255,255,255,.6);}
      .bx-ob-body {
        padding:16px 20px 20px;
      }
      .bx-ob-icon {
        font-size:2.8rem;margin-bottom:12px;display:block;
        animation:bxPop .4s cubic-bezier(.34,1.56,.64,1);
      }
      @keyframes bxPop{from{transform:scale(.5);opacity:0}to{transform:scale(1);opacity:1}}
      .bx-ob-title {
        font-size:1rem;font-weight:800;color:#fff;margin-bottom:10px;line-height:1.3;
      }
      .bx-ob-text {
        font-size:.82rem;color:rgba(255,255,255,.6);line-height:1.65;margin-bottom:16px;
        white-space:pre-line;
      }
      .bx-ob-btn {
        width:100%;padding:12px;
        background:linear-gradient(135deg,#C9A84C,#8B6914);
        border:none;border-radius:12px;color:#fff;
        font-weight:800;font-size:.88rem;cursor:pointer;
        font-family:inherit;transition:.15s;margin-bottom:8px;
      }
      .bx-ob-btn:hover{opacity:.9;transform:translateY(-1px);}
      .bx-ob-sub {text-align:center;}
      @media(max-width:500px){
        #bxOnboardingOverlay{padding:16px;align-items:center;justify-content:center;}
        #bxOnboarding{width:calc(100vw - 32px);}
      }
    `;
    document.head.appendChild(style);

    var overlay = document.createElement('div');
    overlay.id = 'bxOnboardingOverlay';

    var box = document.createElement('div');
    box.id = 'bxOnboarding';
    overlay.appendChild(box);
    document.body.appendChild(overlay);

    renderStep();
  }

  function renderStep() {
    var box = document.getElementById('bxOnboarding');
    if (!box) return;
    var s = STEPS[currentStep];
    var total = STEPS.length;

    var dots = STEPS.map(function(_, i) {
      var cls = i === currentStep ? 'active' : (i < currentStep ? 'done' : '');
      return '<div class="bx-ob-dot ' + cls + '"></div>';
    }).join('');

    box.innerHTML = `
      <div class="bx-ob-head">
        <div class="bx-ob-dots">${dots}</div>
        <button class="bx-ob-skip" onclick="window._bxObSkip()">O'tkazib yuborish</button>
      </div>
      <div class="bx-ob-body">
        <span class="bx-ob-icon">${s.icon}</span>
        <div class="bx-ob-title">${s.title}</div>
        <div class="bx-ob-text">${s.body}</div>
        <button class="bx-ob-btn" onclick="window._bxObNext()">${s.btn}</button>
        <div class="bx-ob-sub">${s.sub}</div>
      </div>`;
  }

  window._bxObNext = function() {
    currentStep++;
    if (currentStep >= STEPS.length) {
      acceptAndClose();
    } else {
      renderStep();
    }
  };

  window._bxObSkip = function() {
    acceptAndClose();
  };

  function acceptAndClose() {
    document.cookie = 'bx_privacy=1;path=/;max-age=31536000;SameSite=Lax';
    var overlay = document.getElementById('bxOnboardingOverlay');
    if (overlay) {
      overlay.style.animation = 'bxFadeIn .25s ease reverse forwards';
      setTimeout(function() { overlay.remove(); }, 250);
    }
  }

  // Show after 1.5 seconds
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      setTimeout(buildOnboarding, 1500);
    });
  } else {
    setTimeout(buildOnboarding, 1500);
  }
})();
