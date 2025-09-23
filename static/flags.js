/* Feature Flags Management UI (vanilla JS, Tailwind/Tailux styles) */
(function () {
  const headersAdmin = { 'Content-Type': 'application/json', 'X-User-Role': 'admin', 'X-User-Id': '42' };
  const state = {
    env: 'staging',
    query: '',
    group: '',
    fstate: '',
    flags: [],
    selected: new Set(),
    collapsedGroups: new Set(),
    currentFlag: null,
    historyFor: null,
    view: 'flags',
    audit: [],
  };

  const app = document.getElementById('app');
  app.innerHTML = `
    <div class="flex items-center gap-3">
      <div class="flex items-center gap-3">
        <a id="tab-flags" href="/management" class="text-sm font-medium text-blue-700">Flags</a>
        <a id="tab-audit" href="/management/audit" class="text-sm text-gray-600 hover:text-blue-700">Audit</a>
      </div>
      <input id="search" class="border rounded px-3 py-2 w-64" placeholder="Поиск по ключу/описанию" />
      <select id="state" class="border rounded px-2 py-2">
        <option value="">State</option>
        <option value="on">On</option>
        <option value="off">Off</option>
        <option value="scheduled">Scheduled</option>
      </select>
      <select id="group" class="border rounded px-2 py-2">
        <option value="">Group</option>
        <option>UI</option>
        <option>Content</option>
        <option>Payments</option>
        <option>AI</option>
        <option>System</option>
      </select>
      <div class="ml-auto flex items-center gap-2 text-sm">
        <label class="inline-flex items-center gap-1"><input type="radio" name="env" value="staging" checked/> Staging</label>
        <label class="inline-flex items-center gap-1"><input type="radio" name="env" value="production"/> Production</label>
      </div>
      <button id="btn-create" class="btn btn-primary">Создать флаг</button>
      <button id="btn-export" class="btn btn-ghost">Export</button>
      <label class="btn btn-ghost cursor-pointer">Import<input id="file-import" type="file" accept="application/json" class="hidden"/></label>
    </div>

    <div id="batchbar" class="hidden mt-3 flex items-center gap-2">
      <div class="text-sm text-gray-600"><span id="sel-count">0</span> выбрано</div>
      <button class="btn btn-ghost" data-batch="enable">Enable</button>
      <button class="btn btn-ghost" data-batch="disable">Disable</button>
      <button class="btn btn-ghost" data-batch="audience_all">Audience: All</button>
      <button class="btn btn-ghost" data-batch="audience_premium">Audience: Premium</button>
      <button class="btn btn-ghost" data-batch="audience_off">Audience: Off</button>
      <button class="btn btn-ghost" data-batch="pin">Pin</button>
      <button class="btn btn-ghost" data-batch="unpin">Unpin</button>
      <button id="btn-clear" class="btn btn-ghost">Clear</button>
    </div>

    <div id="list" class="mt-3 border rounded overflow-hidden"></div>
    <div id="audit" class="mt-3 hidden"></div>

    <div id="backdrop" class="backdrop"></div>
    <aside id="drawer" class="drawer">
      <div class="p-4 border-b flex items-center justify-between">
        <div class="font-semibold">Редактирование флага</div>
        <button id="close-drawer" class="icon-btn">✕</button>
      </div>
      <div class="p-4 space-y-3 text-sm overflow-y-auto h-[calc(100%-56px)]">
        <div>
          <label class="block text-xs text-gray-500">Preset (при создании)</label>
          <select id="f-preset" class="w-full border rounded px-2 py-1">
            <option value="">—</option>
            <option value="toggle">Toggle</option>
            <option value="kill-switch">Kill-switch</option>
            <option value="gradual-rollout">Gradual rollout</option>
          </select>
        </div>
        <div>
          <label class="block text-xs text-gray-500">Key</label>
          <input id="f-key" class="w-full border rounded px-2 py-1 bg-gray-100" readonly />
        </div>
        <div>
          <label class="block text-xs text-gray-500">Название</label>
          <input id="f-title" class="w-full border rounded px-2 py-1" />
        </div>
        <div>
          <label class="block text-xs text-gray-500">Описание</label>
          <textarea id="f-desc" class="w-full border rounded px-2 py-1" rows="2"></textarea>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs text-gray-500">Группа</label>
            <select id="f-group" class="w-full border rounded px-2 py-1">
              <option>UI</option><option>Content</option><option>Payments</option><option>AI</option><option>System</option>
            </select>
          </div>
          <div>
            <label class="block text-xs text-gray-500">Аудитория</label>
            <select id="f-aud" class="w-full border rounded px-2 py-1">
              <option value="off">Off</option><option value="all">All</option><option value="premium">Premium</option>
            </select>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs text-gray-500">State</label>
            <select id="f-state" class="w-full border rounded px-2 py-1">
              <option value="off">Off</option><option value="on">On</option><option value="scheduled">Scheduled</option>
            </select>
          </div>
          <div class="flex items-end gap-2">
            <label class="inline-flex items-center gap-2"><input id="f-pin" type="checkbox"/> Pin</label>
          </div>
        </div>
        <div class="border rounded p-3">
          <div class="font-medium mb-2">Rollout</div>
          <label class="inline-flex items-center gap-2"><input id="r-enabled" type="checkbox"/> Enabled</label>
          <div class="mt-2 grid grid-cols-3 gap-3">
            <div class="col-span-2"><input id="r-perc" type="range" min="0" max="100" value="0" class="w-full" oninput="document.getElementById('r-perc-val').textContent=this.value+'%';"/></div>
            <div><span id="r-perc-val" class="inline-block w-12 text-right">0%</span></div>
          </div>
          <div class="mt-2">
            <label class="block text-xs text-gray-500">Segments (CSV)</label>
            <input id="r-seg" class="w-full border rounded px-2 py-1" placeholder="beta,internal" />
          </div>
        </div>
        <div class="border rounded p-3">
          <div class="font-medium mb-2">Зависимости</div>
          <input id="f-deps" class="w-full border rounded px-2 py-1" placeholder="flag.a,flag.b" />
        </div>
        <div class="border rounded p-3">
          <div class="font-medium mb-2">Планирование (UTC)</div>
          <div class="grid grid-cols-2 gap-3">
            <div><label class="block text-xs text-gray-500">Start at</label><input id="s-start" type="datetime-local" class="w-full border rounded px-2 py-1"/></div>
            <div><label class="block text-xs text-gray-500">End at</label><input id="s-end" type="datetime-local" class="w-full border rounded px-2 py-1"/></div>
          </div>
        </div>
        <div class="flex gap-2">
          <button id="btn-save" class="btn btn-primary">Сохранить</button>
          <button id="btn-test" class="btn btn-ghost">Применить и протестировать на себе</button>
        </div>
      </div>
    </aside>
    <aside id="sidebar" class="sidebar">
      <div class="p-4 border-b flex items-center justify-between">
        <div class="font-semibold">История</div>
        <button id="close-sidebar" class="icon-btn">✕</button>
      </div>
      <div id="history" class="p-3 text-sm overflow-y-auto h-[calc(100%-56px)]"></div>
    </aside>
  `;

  // Elements
  const E = (id) => document.getElementById(id);
  const listEl = E('list');
  const batchEl = E('batchbar');

  // Router and UI toggles
  function detectView() {
    const path = window.location.pathname;
    if (path.endsWith('/management/audit')) state.view = 'audit'; else state.view = 'flags';
    document.getElementById('tab-flags').className = state.view==='flags' ? 'text-sm font-medium text-blue-700' : 'text-sm text-gray-600 hover:text-blue-700';
    document.getElementById('tab-audit').className = state.view==='audit' ? 'text-sm font-medium text-blue-700' : 'text-sm text-gray-600 hover:text-blue-700';
    E('search').placeholder = state.view==='audit' ? 'Поиск по actor/action/resource' : 'Поиск по ключу/описанию';
    E('state').parentElement.style.display = state.view==='flags' ? '' : 'none';
    E('group').parentElement.style.display = state.view==='flags' ? '' : 'none';
    E('btn-create').style.display = state.view==='flags' ? '' : 'none';
    E('btn-export').style.display = state.view==='flags' ? '' : 'none';
    E('file-import').parentElement.style.display = state.view==='flags' ? '' : 'none';
    E('batchbar').style.display = state.view==='flags' ? '' : 'none';
    E('list').style.display = state.view==='flags' ? '' : 'none';
    E('audit').style.display = state.view==='audit' ? '' : 'none';
  }

  // Events
  E('search').addEventListener('input', () => { state.query = E('search').value.trim(); load(); });
  E('group').addEventListener('change', () => { state.group = E('group').value; load(); });
  E('state').addEventListener('change', () => { state.fstate = E('state').value; load(); });
  for (const r of document.querySelectorAll('input[name=env]')) { r.addEventListener('change', () => { state.env = r.value; state.selected.clear(); updateBatchBar(); load(); }); }
  E('btn-create').addEventListener('click', () => openCreate());
  E('btn-export').addEventListener('click', () => exportEnv());
  E('file-import').addEventListener('change', (e) => importEnv(e.target.files?.[0]));
  E('btn-clear').addEventListener('click', () => { state.selected.clear(); updateBatchBar(); render(); });
  batchEl.addEventListener('click', (e) => { const a = e.target.closest('[data-batch]'); if (!a) return; doBatch(a.getAttribute('data-batch')); });
  E('close-drawer').addEventListener('click', closeDrawer);
  E('close-sidebar').addEventListener('click', closeSidebar);
  E('btn-save').addEventListener('click', saveEdit);
  E('btn-test').addEventListener('click', testOnSelf);

  // Rendering
  function render() { if (state.view==='audit') { renderAudit(); return; } renderFlags(); }

  function renderFlags() {
    // Grouping
    const groups = new Map();
    for (const f of state.flags) { const g = f.group || 'Other'; if (!groups.has(g)) groups.set(g, []); groups.get(g).push(f); }
    let html = '';
    html += `<table class="table min-w-full text-sm"><thead class="bg-gray-100 text-left text-xs uppercase text-gray-600"><tr>
      <th class="p-2"><input id="sel-all" type="checkbox"/></th>
      <th>Key</th><th>Название</th><th>Audience</th><th>State</th><th>%</th><th>Last change</th><th></th></tr></thead>`;
    html += '<tbody>';
    for (const [g, arr] of groups) {
      const collapsed = state.collapsedGroups.has(g);
      html += `<tr class="group-header"><td colspan="8" class="cursor-pointer" data-group="${g}">`+
              `<span class="mr-2">${collapsed ? '▸' : '▾'}</span>${g} <span class="text-gray-400">(${arr.length})</span></td></tr>`;
      if (collapsed) continue;
      for (const f of arr) {
        const selected = state.selected.has(f.key);
        const depCount = (f.depends_on||[]).length;
        const hasSched = (f.schedule?.start_at || f.schedule?.end_at);
        const audChip = f.audience==='off'?'chip chip-off':(f.audience==='all'?'chip chip-all':'chip chip-premium');
        const stateChip = f.state==='scheduled'?'chip chip-scheduled':'';
        html += `<tr class="hover:bg-gray-50">
          <td><input type="checkbox" data-key="${f.key}" ${selected?'checked':''}/></td>
          <td>
            <div class="flex items-center gap-2">
              <button class="icon-btn" title="${f.pinned?'Unpin':'Pin'}" data-pin="${f.key}">${f.pinned?'★':'☆'}</button>
              <div>
                <div class="font-mono text-blue-600">${f.key}</div>
                <div class="text-[10px] text-gray-500">${f.group||''}</div>
              </div>
              ${depCount?`<span class="text-[10px] text-gray-500" title="Depends on: ${(f.depends_on||[]).join(', ')}">⛓ ${depCount}</span>`:''}
              ${hasSched?`<span class="text-[10px] text-amber-600" title="Scheduled">🕒</span>`:''}
            </div>
          </td>
          <td>
            <div class="text-sm font-medium truncate max-w-[280px]">${f.title||''}</div>
            <div class="text-xs text-gray-500 truncate max-w-[280px]">${f.description||''}</div>
          </td>
          <td>
            <select class="text-sm border rounded px-2 py-1" data-edit="audience" data-key="${f.key}">
              <option value="off" ${f.audience==='off'?'selected':''}>Off</option>
              <option value="all" ${f.audience==='all'?'selected':''}>All</option>
              <option value="premium" ${f.audience==='premium'?'selected':''}>Premium</option>
            </select>
            <span class="ml-2 ${audChip}">${f.audience[0].toUpperCase()+f.audience.slice(1)}</span>
          </td>
          <td>
            <label class="inline-flex items-center cursor-pointer">
              <input type="checkbox" class="sr-only" data-toggle="${f.key}" ${f.state==='on'?'checked':''}/>
              <div class="w-9 h-5 bg-gray-300 data-[on=true]:bg-blue-600 rounded-full transition relative">
                <div class="h-4 w-4 bg-white rounded-full absolute top-0.5 left-0.5 transition-transform" data-knob="${f.key}" style="transform:${f.state==='on'?'translateX(16px)':'translateX(0)'}"></div>
              </div>
            </label>
            ${f.state==='scheduled'?`<span class="ml-2 ${stateChip}">Scheduled</span>`:''}
          </td>
          <td class="text-xs text-gray-600">${(f.rollout?.enabled? (f.rollout.percentage+'%'):'—')}</td>
          <td class="text-xs text-gray-500">${new Date(f.updated_at).toLocaleString()}</td>
          <td class="text-right">
            <button class="text-xs text-gray-600 hover:text-blue-600" data-edit-open="${f.key}">Редактировать</button>
            <span class="mx-1 text-gray-300">|</span>
            <button class="text-xs text-gray-600 hover:text-blue-600" data-history="${f.key}">История</button>
          </td>
        </tr>`;
      }
    }
    html += '</tbody></table>';
    listEl.innerHTML = html;
    // Bind dynamic events
    const selAll = document.getElementById('sel-all'); if (selAll) selAll.addEventListener('change', () => { toggleAll(selAll.checked); });
    for (const cb of listEl.querySelectorAll('input[type=checkbox][data-key]')) { cb.addEventListener('change', () => { cb.checked ? state.selected.add(cb.getAttribute('data-key')) : state.selected.delete(cb.getAttribute('data-key')); updateBatchBar(); }); }
    for (const pin of listEl.querySelectorAll('[data-pin]')) pin.addEventListener('click', () => togglePin(pin.getAttribute('data-pin')));
    for (const sel of listEl.querySelectorAll('select[data-edit="audience"]')) sel.addEventListener('change', () => updateField(sel.getAttribute('data-key'), 'audience', sel.value));
    for (const t of listEl.querySelectorAll('input[type=checkbox][data-toggle]')) t.addEventListener('change', () => updateField(t.getAttribute('data-toggle'), 'state', t.checked?'on':'off'));
    for (const o of listEl.querySelectorAll('[data-edit-open]')) o.addEventListener('click', () => openEdit(o.getAttribute('data-edit-open')));
    for (const h of listEl.querySelectorAll('[data-history]')) h.addEventListener('click', () => openHistory(h.getAttribute('data-history')));
    for (const gh of listEl.querySelectorAll('[data-group]')) gh.addEventListener('click', () => { const g=gh.getAttribute('data-group'); if (state.collapsedGroups.has(g)) state.collapsedGroups.delete(g); else state.collapsedGroups.add(g); render(); });
    updateBatchBar();
  }

  function renderAudit() {
    const el = E('audit');
    let html = '';
    html += '<div class="border rounded p-3">';
    html += '<div class="font-medium mb-2">Audit log (recent)</div>';
    html += '<table class="min-w-full text-sm"><thead class="bg-gray-100 text-left text-xs uppercase text-gray-600">';
    html += '<tr><th class="p-2">Time</th><th class="p-2">Actor</th><th class="p-2">Action</th><th class="p-2">Resource</th></tr></thead><tbody>';
    for (const a of state.audit) { html += `<tr class="hover:bg-gray-50"><td class="p-2">${new Date(a.created_at).toLocaleString()}</td><td class="p-2">${a.actor}</td><td class="p-2">${a.action}</td><td class="p-2">${a.key} (${a.env})</td></tr>`; }
    if (state.audit.length===0) { html += '<tr><td class="p-3 text-gray-500 text-sm" colspan="4">No events</td></tr>'; }
    html += '</tbody></table></div>';
    el.innerHTML = html;
  }

  function toggleAll(on) { if (on) for (const f of state.flags) state.selected.add(f.key); else state.selected.clear(); updateBatchBar(); render(); }
  function updateBatchBar() { const c = state.selected.size; E('sel-count').textContent = String(c); batchEl.classList.toggle('hidden', c===0); }

  // Data loads
  async function loadFlags() {
    const params = new URLSearchParams({ env: state.env }); if (state.query) params.set('query', state.query); if (state.group) params.set('group', state.group); if (state.fstate) params.set('state', state.fstate);
    const res = await fetch('/management/flags?' + params.toString()); state.flags = await res.json(); render();
  }
  async function loadAudit() {
    const params = new URLSearchParams(); if (state.env) params.set('env', state.env); params.set('limit','200');
    const res = await fetch('/management/audit/logs?' + params.toString()); const items = await res.json();
    const q = (state.query||'').toLowerCase(); state.audit = items.filter(a => { if (!q) return true; const txt = `${a.actor} ${a.action} ${a.key}`.toLowerCase(); return txt.includes(q); });
    renderAudit();
  }

  async function updateField(key, field, value) {
    const params = new URLSearchParams({ env: state.env }); const confirmProd = state.env==='production' && ((field==='state' && value==='on'));
    if (confirmProd && !confirm('Подтвердить включение на production?')) return; if (confirmProd) params.set('confirm','true');
    const body = {}; body[field] = value; await fetch(`/management/flags/${encodeURIComponent(key)}?` + params.toString(), { method:'PATCH', headers: headersAdmin, body: JSON.stringify(body) }); await loadFlags();
  }
  async function togglePin(key) { const f = state.flags.find(x=>x.key===key); if (!f) return; await updateField(key, 'pinned', !f.pinned); }
  async function doBatch(action) {
    if (state.env==='production' && (action==='enable'|| action==='audience_all' || action==='audience_premium')) { if (!confirm('Подтвердить массовое включение на production?')) return; }
    const params = new URLSearchParams(); if (state.env==='production' && (action==='enable'|| action==='audience_all'|| action==='audience_premium')) params.set('confirm','true');
    await fetch('/management/flags/batch' + (params.toString()?('?'+params.toString()):''), { method:'POST', headers: headersAdmin, body: JSON.stringify({ keys: Array.from(state.selected), env: state.env, action }) }); state.selected.clear(); updateBatchBar(); await loadFlags();
  }

  // Create / Edit Drawer
  function openCreate() { state.currentFlag = { key: '', title: '', description: '', group:'UI', state:'off', audience:'off', rollout:{enabled:false,percentage:0,segments:[]}, depends_on:[], schedule:{start_at:null, end_at:null}, env: state.env, pinned:false }; fillDrawer(state.currentFlag, true); openDrawer(); }
  async function openEdit(key) { const res = await fetch(`/management/flags/${encodeURIComponent(key)}?env=${state.env}`); if (!res.ok) return alert('Flag not found'); const flag = await res.json(); state.currentFlag = flag; fillDrawer(flag, false); openDrawer(); }
  function fillDrawer(f, isCreate) {
    E('f-key').value = f.key; E('f-key').readOnly = !isCreate; E('f-preset').parentElement.style.display = isCreate ? '' : 'none';
    E('f-title').value = f.title || ''; E('f-desc').value = f.description || ''; E('f-group').value = f.group || 'UI'; E('f-aud').value = f.audience || 'off'; E('f-state').value = f.state || 'off'; E('f-pin').checked = !!f.pinned;
    E('r-enabled').checked = !!(f.rollout && f.rollout.enabled); E('r-perc').value = String((f.rollout && f.rollout.percentage) || 0); document.getElementById('r-perc-val').textContent = ((f.rollout && f.rollout.percentage) || 0) + '%'; E('r-seg').value = (f.rollout && (f.rollout.segments||[]).join(',')) || '';
    const toLocal = (iso) => { if (!iso) return ''; const d = new Date(iso); const tz = new Date(d.getTime() - d.getTimezoneOffset()*60000); return tz.toISOString().slice(0,16); };
    E('s-start').value = toLocal(f.schedule?.start_at); E('s-end').value = toLocal(f.schedule?.end_at);
  }
  function openDrawer() { E('drawer').classList.add('open'); E('backdrop').classList.add('open'); }
  function closeDrawer() { E('drawer').classList.remove('open'); E('backdrop').classList.remove('open'); }
  async function saveEdit() {
    const payload = { title: E('f-title').value, description: E('f-desc').value, group: E('f-group').value, audience: E('f-aud').value, state: E('f-state').value, pinned: E('f-pin').checked, rollout: { enabled: E('r-enabled').checked, percentage: parseInt(E('r-perc').value||'0'), segments: E('r-seg').value.split(',').map(s=>s.trim()).filter(Boolean) }, depends_on: E('f-deps').value.split(',').map(s=>s.trim()).filter(Boolean), schedule: { start_at: toISO(E('s-start').value), end_at: toISO(E('s-end').value) }, };
    const confirmProd = state.env==='production' && (payload.state==='on' || payload.schedule.start_at); const params = new URLSearchParams({ env: state.env }); if (confirmProd) { if (!confirm('Подтвердить изменение production?')) return; params.set('confirm','true'); }
    if (state.currentFlag && state.currentFlag.key) { await fetch(`/management/flags/${encodeURIComponent(state.currentFlag.key)}?`+params.toString(), { method:'PATCH', headers: headersAdmin, body: JSON.stringify(payload) }); }
    else { const preset = E('f-preset').value || null; const body = { key: E('f-key').value, title: payload.title, description: payload.description, group: payload.group, env: state.env, preset }; await fetch('/management/flags', { method:'POST', headers: headersAdmin, body: JSON.stringify(body) }); }
    closeDrawer(); await loadFlags();
  }
  function toISO(localValue) { if (!localValue) return null; const d = new Date(localValue); return new Date(d.getTime() - d.getTimezoneOffset()*60000).toISOString(); }
  async function testOnSelf() { if (!state.currentFlag) return; const plan = prompt('Ваш план? free/premium/premium_plus','premium'); const res = await fetch('/management/eval', { method:'POST', headers: headersAdmin, body: JSON.stringify({ env: state.env, key: state.currentFlag.key, user:{ id:'42', plan: plan||'premium' } }) }); const data = await res.json(); alert('Enabled for you: '+ (data.enabled ? 'YES' : 'NO')); }

  // History sidebar
  async function openHistory(key) { state.historyFor = key; const params = new URLSearchParams({ env: state.env }); const [auditRes, revRes] = await Promise.all([ fetch(`/management/flags/${encodeURIComponent(key)}/audit?`+params.toString()), fetch(`/management/flags/${encodeURIComponent(key)}/revisions?`+params.toString()), ]); const [audit, revs] = [await auditRes.json(), await revRes.json()]; const container = E('history'); let html = ''; html += `<div class="mb-3"><span class="font-mono text-blue-600">${key}</span> — ${state.env}</div>`; html += '<div class="font-medium mb-1">Revisions</div>'; html += '<div class="space-y-2">'; for (const r of revs.slice().reverse()) { const idx = r.index; const dt = new Date(r.updated_at).toLocaleString(); html += `<div class="border rounded p-2 flex items-center justify-between text-xs"><div><span class="text-gray-600">#${idx}</span> — ${dt} — <span class="text-gray-600">${r.updated_by}</span> — state: ${r.state}, audience: ${r.audience}</div><div class="flex items-center gap-2"><button class="btn btn-ghost" data-rollback="${idx}">Rollback</button></div></div>`; } html += '</div>'; html += '<div class="font-medium mt-4 mb-1">Последние операции</div>'; html += '<div class="space-y-1">'; for (const a of audit) { html += `<div class="text-xs text-gray-700">${new Date(a.created_at).toLocaleString()} — ${a.actor} — ${a.action}</div>`; } html += '</div>'; container.innerHTML = html; for (const b of container.querySelectorAll('[data-rollback]')) b.addEventListener('click', () => doRollback(parseInt(b.getAttribute('data-rollback'), 10))); openSidebar(); }
  function openSidebar() { E('sidebar').classList.add('open'); E('backdrop').classList.add('open'); }
  function closeSidebar() { E('sidebar').classList.remove('open'); E('backdrop').classList.remove('open'); }
  async function doRollback(index) { const params = new URLSearchParams({ env: state.env, to: String(index) }); if (state.env==='production') { if (!confirm('Подтвердить откат на production?')) return; params.set('confirm','true'); } await fetch(`/management/flags/${encodeURIComponent(state.historyFor)}/rollback?`+params.toString(), { method:'POST', headers: headersAdmin }); await loadFlags(); await openHistory(state.historyFor); }

  // Import/Export
  async function exportEnv() { const res = await fetch(`/management/flags/export?env=${state.env}`); const data = await res.json(); const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `flags_${state.env}.json`; a.click(); URL.revokeObjectURL(url); }
  async function importEnv(file) { if (!file) return; const text = await file.text(); let data; try { data = JSON.parse(text); } catch { return alert('Invalid JSON'); } if (data && data.env && data.env !== state.env) { if (!confirm(`Импорт из ${data.env} в ${state.env}. Продолжить?`)) return; } const params = new URLSearchParams(); if (state.env==='production') { if (!confirm('Подтвердить импорт в production?')) return; params.set('confirm','true'); } await fetch('/management/flags/import' + (params.toString()?('?'+params.toString()):''), { method:'POST', headers: headersAdmin, body: JSON.stringify({ env: state.env, flags: (data.flags||[]) }) }); await loadFlags(); }

  // Unified load by view
  async function load() { detectView(); if (state.view==='audit') await loadAudit(); else await loadFlags(); }
  load();
})();

