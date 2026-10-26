'use strict';
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const iconPaths = {
  dashboard:'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  sparkles:'<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z"/><path d="m20 2 .5 1.5L22 4l-1.5.5L20 6l-.5-1.5L18 4l1.5-.5Z"/>',
  folder:'<path d="M3 7a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v9H3Z"/><path d="M3 11h18"/>',
  history:'<path d="M3 10a9 9 0 1 1 1 8M3 4v6h6M12 7v5l3 2"/>',
  settings:'<path d="m9 3 1 2h4l1-2 3 2-.5 2 2 3 2 .5v3l-2 .5-2 3 .5 2-3 2-1-2h-4l-1 2-3-2 .5-2-2-3L2 13.5v-3l2.5-.5 2-3L6 5Z"/><circle cx="12" cy="12" r="3"/>',
  refresh:'<path d="M20 8a8 8 0 0 0-14-3L3 8m0-5v5h5M4 16a8 8 0 0 0 14 3l3-3m0 5v-5h-5"/>',
  arrow:'<path d="M4 12h15m-5-5 5 5-5 5"/>',
  'arrow-up':'<path d="M12 20V4m-6 6 6-6 6 6"/>',
  clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  users:'<circle cx="9" cy="8" r="3"/><path d="M3 21v-2a6 6 0 0 1 12 0v2M16 5a3 3 0 0 1 0 6m2 3a5 5 0 0 1 3 5v2"/>',
  book:'<path d="M12 5C9 3 5 3 2 4v15c3-1 7-1 10 1m0-15c3-2 7-2 10-1v15c-3-1-7-1-10 1Z"/>',
  calendar:'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v5m10-5v5M3 11h18M7 15h2m4 0h2m-8 3h2"/>',
  download:'<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
  layers:'<path d="m12 3 10 6-10 6L2 9Zm-10 10 10 6 10-6M2 17l10 6 10-6"/>',
  shield:'<path d="m12 2 8 4v6c0 5-5 8-8 10-3-2-8-5-8-10V6Z"/><path d="m8 12 3 3 5-6"/>',
  plus:'<path d="M12 5v14M5 12h14"/>',
  search:'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>'
};
const svg = name => `<svg viewBox="0 0 24 24" aria-hidden="true">${iconPaths[name] || iconPaths.book}</svg>`;
$$('[data-icon]').forEach(node => {node.innerHTML = svg(node.dataset.icon);});
const state = {view:'agents', agentId:'analysis', summary:null, year:'', offset:0, limit:30, rows:[], total:0, conversationId:null, messages:[], busy:false, health:null, edit:null, deleteAction:null};
const names = {agents:'에이전트 허브',calendar:'월별 수업 블록',materials:'과목별 교재 슬라이드',dashboard:'교육운영 대시보드',chat:'강사 AI 비서',data:'교육 실적 관리',history:'이전 대화 기록'};
let toastTimer;
const number = value => new Intl.NumberFormat('ko-KR', {maximumFractionDigits:2}).format(value);
const times = row => (row.schedule_units || []).map(unit => `${unit.start_time}–${unit.end_time}`).join(' / ');
const savedTheme = localStorage.getItem('academy_theme');
function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  $('#theme-toggle').setAttribute('aria-pressed', String(theme === 'dark'));
  $('#theme-toggle').textContent = theme === 'dark' ? '밝게' : '어둡게';
  $('#theme-toggle').setAttribute('aria-label', theme === 'dark' ? '밝은 화면으로 전환' : '어두운 화면으로 전환');
}
setTheme(savedTheme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
$('#theme-toggle').onclick = () => {const theme=document.documentElement.dataset.theme==='dark'?'light':'dark';localStorage.setItem('academy_theme',theme);setTheme(theme);};

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function toast(message) {
  clearTimeout(toastTimer); $('#toast').textContent = message; $('#toast').hidden = false;
  toastTimer = setTimeout(() => {$('#toast').hidden = true;}, 5500);
}
function notice(message) {$('#notice').textContent = message; $('#notice').hidden = !message;}
function apiBase() {return (sessionStorage.getItem('academy_api_url') || window.ACADEMY_CONFIG?.API_BASE_URL || '').replace(/\/$/,'');}
async function api(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 65000);
  const headers = {'Accept':'application/json', ...options.headers};
  if (options.body) headers['Content-Type'] = 'application/json';
  const token = sessionStorage.getItem('academy_access_key');
  if (token) headers.Authorization = `Bearer ${token}`;
  try {
    const response = await fetch(apiBase() + path, {...options, headers, signal:controller.signal});
    let payload;
    try {payload = await response.json();} catch {throw new Error('서비스 주소를 확인해 주세요. 올바른 데이터 응답을 받지 못했습니다.');}
    if (!response.ok) {
      const detail = Array.isArray(payload.detail) ? payload.detail.map(item=>item.msg).join(' / ') : payload.detail;
      const error = new Error(detail || '요청을 처리하지 못했습니다.');
      error.status = response.status;
      throw error;
    }
    return payload;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('첫 연결에 시간이 걸리고 있습니다. 서버가 잠들어 있었다면 약 1분 후 새로고침해 주세요.');
    if (error instanceof TypeError) throw new Error('서비스에 연결할 수 없습니다. 서비스 주소와 서버 실행 상태를 확인해 주세요.');
    throw error;
  } finally {clearTimeout(timer);}
}
function periodQuery(extra = {}) {
  const params = new URLSearchParams(extra);
  if (state.year) {params.set('date_from', `${state.year}-01-01`); params.set('date_to', `${state.year}-12-31`);}
  return params.toString() ? '?' + params : '';
}
async function navigate(view) {
  if (!names[view]) view = 'dashboard';
  state.view = view;
  $$('.view').forEach(node => {node.hidden = node.id !== `view-${view}`;});
  $$('.nav-item').forEach(node => {const active = node.dataset.view === view; node.classList.toggle('active',active); if(active) node.setAttribute('aria-current','page'); else node.removeAttribute('aria-current');});
  $('#page-name').textContent = names[view];
  if (location.hash !== '#' + view) history.replaceState(null,'','#' + view);
  try {
    if (view === 'data') await loadData();
    if (view === 'history') await loadHistory();
    if (window.AcademyWorkspace) await window.AcademyWorkspace.onNavigate(view);
  } catch(error) {toast(error.message);}
}
function empty(message, description = '') {const node=element('div','empty-state');node.append(element('strong','',message));if(description) node.append(element('span','',description));return node;}

async function refresh() {
  $('#refresh-button').disabled = true;
  const slowNotice = setTimeout(() => notice('첫 연결을 준비하고 있어요. 무료 서버가 쉬고 있었다면 1분 정도 걸릴 수 있습니다. 잠시 기다려 주세요.'), 8000);
  try {
    const health = await api('/health'); state.health = health;
    $('#connection-status').classList.toggle('disconnected', !health.database_configured);
    $('#connection-status').lastChild.textContent = health.database_configured ? (health.database_mode === 'emulator' ? '로컬 Firestore 연결' : 'Firestore 연결') : '데이터 연결 준비';
    $('#chat-availability').textContent = health.ai_configured ? '교육운영 요약을 바탕으로 답변해요' : 'AI 연결 준비 중 · 데이터 기능은 사용할 수 있어요';
    if (!health.database_configured) throw new Error('교육 데이터 저장소를 연결할 준비 중입니다. Firebase 설정을 완료하면 저장된 기록이 표시됩니다.');
    const summary = await api('/api/data/summary' + periodQuery()); state.summary = summary; renderSummary();
    clearTimeout(slowNotice);
    notice(health.database_mode === 'emulator' ? '로컬 Firestore에서 실제 교육 기록을 불러왔습니다. 인터넷 데이터베이스 연결은 계정 설정 후 이어서 진행합니다.' : '');
    await loadRecent();
    if (state.view === 'data') await loadData();
    if (state.view === 'history') await loadHistory();
    if (window.AcademyWorkspace && ['calendar','materials'].includes(state.view)) await window.AcademyWorkspace.onNavigate(state.view);
    return true;
  } catch(error) {
    notice(error.message);
    $('#connection-status').classList.add('disconnected');
    $('#connection-status').lastChild.textContent = '연결 확인 필요';
    $('#recent-list').replaceChildren(empty('교육 기록 연결을 기다리고 있어요','연결되면 최근 수업을 확인할 수 있습니다.'));
    return false;
  } finally {clearTimeout(slowNotice);$('#refresh-button').disabled = false;}
}
function renderSummary() {
  const s = state.summary;
  if (!s) return;
  $('#stat-hours').textContent = number(s.metrics.total); $('#stat-students').textContent = number(s.students.total);
  $('#stat-courses').textContent = number(s.course_count); $('#stat-days').textContent = number(s.teaching_days);
  const period = s.period.start ? `${s.period.start} — ${s.period.end}` : '저장된 교육 기록이 없습니다';
  $('#period-caption').textContent = `${period} · 보유 기록 기준`;
  $('#stat-record-count').textContent = `교육일별 기록 ${number(s.count)}건이 담겨 있어요`;
  $('#satisfaction-value').textContent = s.satisfaction.average === null ? '미입력' : `${number(s.satisfaction.average)}점`;
  $('#satisfaction-count').textContent = `${s.satisfaction.scored_courses}개 과정 · 미입력 제외`;
  $('#context-period').textContent = period; $('#context-count').textContent = `${number(s.count)}건`; $('#context-hours').textContent = `${number(s.metrics.total)}시간`;
  const trend = s.trend;
  const trendText = trend.percent === null ? trend.label : `${trend.label} · ${number(Math.abs(trend.percent))}% (${trend.from_month} → ${trend.to_month})`;
  $('#summary-average').textContent = `${number(s.metrics.average)}시간`;
  $('#summary-max').textContent = `${number(s.metrics.max)}시간`;
  $('#summary-min').textContent = `${number(s.metrics.min)}시간`;
  $('#summary-trend').textContent = trendText;
  $('#context-average').textContent = `${number(s.metrics.average)}시간 / 기록`;
  $('#context-range').textContent = `${number(s.metrics.min)} ~ ${number(s.metrics.max)}시간`;
  $('#context-trend').textContent = trendText;
  const chart = $('#monthly-chart'); chart.replaceChildren();
  const months = s.monthly.slice(-12); const max = Math.max(1,...months.map(m=>m.hours));
  if (!months.length) chart.append(empty('표시할 교육 기록이 없습니다'));
  for (const month of months) {
    const column = element('div','chart-column'); column.title = `${month.month}: ${number(month.hours)}시간`;
    column.append(element('span','chart-value',number(month.hours)));
    const bar = element('div','chart-bar'); bar.style.height = `${Math.max(2,month.hours/max*112)}px`;column.append(bar);
    column.append(element('span','chart-month',month.month.slice(2).replace('-','.')));chart.append(column);
  }
  chart.setAttribute('aria-label','월별 교육시간: ' + months.map(m=>`${m.month} ${m.hours}시간`).join(', '));
  const modes = $('#mode-list'); modes.replaceChildren();
  for (const mode of s.by_mode.sort((a,b)=>b.count-a.count)) {
    const row = element('div','mode-row'); const head=element('div','mode-row-head');head.append(element('span','',mode.mode),element('strong','',`${number(mode.count)}건 · ${Math.round(mode.count/s.count*100)}%`));
    const track=element('div','mode-track'); const fill=element('span');fill.style.width=`${mode.count/s.count*100}%`;track.append(fill);row.append(head,track);modes.append(row);
  }
  window.AcademyWorkspace?.summaryChanged(s);
}
async function loadRecent() {
  const response = await api('/api/data' + periodQuery({limit:5})); const list = $('#recent-list');list.replaceChildren();
  if (!response.items.length) list.append(empty('새로운 교육 기록을 추가해 보세요'));
  for (const row of response.items) {
    const item=element('div','recent-row');const icon=element('span','recent-row-icon');icon.innerHTML=svg('book');
    const copy=element('div');copy.style.minWidth='0';const title=element('div','recent-row-title',row.course_title);title.title=row.course_title;copy.append(title,element('div','recent-row-sub',`${row.date} ${times(row)} · ${row.mode || '기타'}`));
    item.append(icon,copy,element('span','recent-row-hours',`${number(row.value)}시간`));list.append(item);
  }
}
async function loadData() {
  const extra={limit:state.limit,offset:state.offset};
  if ($('#record-search').value.trim()) extra.search=$('#record-search').value.trim();
  if ($('#mode-filter').value) extra.mode=$('#mode-filter').value;
  const query=new URLSearchParams(periodQuery(extra).slice(1));
  const selectedDate=$('#record-date-filter').value;
  if(selectedDate){query.set('date_from',selectedDate);query.set('date_to',selectedDate);}
  const result=await api('/api/data?'+query);state.rows=result.items;state.total=result.total;
  const body=$('#data-body');body.replaceChildren();
  for(const row of state.rows) {
    const tr=element('tr');const dateCell=element('td','',row.date);if(times(row))dateCell.append(element('small','record-time',times(row)));tr.append(dateCell);
    const info=element('td');info.append(element('strong','',row.course_title || '교육 기록'));const memo=element('small','',row.memo);memo.title=row.memo;info.append(memo);tr.append(info);
    const mode=element('td');const tag=element('span','mode-tag',row.mode || '기타');tag.dataset.mode=row.mode;mode.append(tag);tr.append(mode,element('td','',`${number(row.value)}h`));
    const actions=element('td');const buttons=element('div','row-actions');const edit=element('button','','수정');edit.setAttribute('aria-label',`${row.date} ${row.course_title} 수정`);edit.onclick=()=>openRecord(row);
    const remove=element('button','','삭제');remove.setAttribute('aria-label',`${row.date} ${row.course_title} 삭제`);remove.onclick=()=>confirmDelete(async()=>{await api('/api/data/'+encodeURIComponent(row.id),{method:'DELETE'});if(state.offset && state.rows.length===1)state.offset=Math.max(0,state.offset-state.limit);await refresh();toast('교육 기록을 목록과 집계에서 제외했습니다.');});
    buttons.append(edit,remove);actions.append(buttons);tr.append(actions);body.append(tr);
  }
  if(!state.rows.length){const tr=element('tr');const td=element('td');td.colSpan=5;td.append(empty('검색된 교육 기록이 없습니다'));tr.append(td);body.append(tr);}
  $('#table-count').textContent=`총 ${number(state.total)}건`;$('#page-caption').textContent=`${Math.floor(state.offset/state.limit)+1} / ${Math.max(1,Math.ceil(state.total/state.limit))} 페이지`;
  $('#previous-page').disabled=state.offset===0;$('#next-page').disabled=state.offset+state.limit>=state.total;
}
function openRecord(row=null,{fromPlan=false}={}) {
  state.edit=fromPlan?null:row;const form=$('#record-form');form.reset();$('#record-dialog-title').textContent=fromPlan?'계획에서 실적 등록 준비':row?'교육 기록 수정':'교육 기록 추가';
  for(const field of ['course_title','date','value','mode','venue','memo','students']) if(row && row[field]!==undefined) form.elements[field].value=row[field];
  if(!row)form.elements.date.value=new Date().toLocaleDateString('en-CA');
  $('#students-field').hidden=Boolean(row?.course_id);form.elements.course_title.disabled=Boolean(row?.course_id);
  $('#record-source-note').textContent=row?.source_file?`원본: ${row.source_file} · 과정 인원과 원본 교육일정은 보존됩니다.`:'';
  $('#plan-actual-confirmation').hidden=!fromPlan;
  $('#plan-actual-confirm').required=fromPlan;
  if(fromPlan){form.elements.students.value='';form.elements.students.required=true;$('#record-source-note').textContent='날짜·시간·장소는 계획 기준 초안입니다. 실제 교육시간과 교육생 수를 확인한 뒤 저장하세요. 계획 인원을 실적에 자동 복사하지 않습니다. 승인 상태도 자동 변경하지 않습니다.';}
  else form.elements.students.required=false;
  $('#record-dialog').showModal();
}
$('#record-form').addEventListener('submit',async event=>{
  event.preventDefault();const form=event.currentTarget;const values=Object.fromEntries(new FormData(form));values.value=Number(values.value);
  if($('#plan-actual-confirm').required&&!$('#plan-actual-confirm').checked){$('#plan-actual-confirm').reportValidity();return;}
  if(state.edit?.course_id)delete values.students;else values.students=Number(values.students || 0);
  const button=$('#record-submit');button.disabled=true;
  try {await api('/api/data'+(state.edit?'/'+encodeURIComponent(state.edit.id):''),{method:state.edit?'PUT':'POST',body:JSON.stringify(values)});$('#record-dialog').close();await refresh();toast('교육 기록을 저장하고 요약을 갱신했습니다.');}
  catch(error){toast(error.message);}finally{button.disabled=false;}
});
function confirmDelete(action){state.deleteAction=action;$('#confirm-dialog').showModal();}
$('#cancel-delete').onclick=()=>{$('#confirm-dialog').close();state.deleteAction=null;};
$('#confirm-delete').onclick=async()=>{const action=state.deleteAction;$('#confirm-dialog').close();state.deleteAction=null;if(action)try{await action();}catch(error){toast(error.message);}};
function renderMessages() {
  updateChatControls();
  const container=$('#messages');
  if(!state.messages.length){$('#chat-welcome').hidden=false;$$('.message',container).forEach(n=>n.remove());return;}
  $('#chat-welcome').hidden=true;$$('.message',container).forEach(n=>n.remove());
  for(const message of state.messages)container.append(element('div',`message ${message.role}`,message.content));
  container.scrollTop=container.scrollHeight;
}
function updateChatControls(){
  $('#send-button').disabled=state.busy;
  $('#save-chat').disabled=state.busy||!state.conversationId||!state.messages.length;
}
async function saveCurrentChat(){
  if(state.busy||!state.conversationId||!state.messages.length)return;
  state.busy=true;updateChatControls();$('#save-chat').textContent='저장 중…';
  try{
    const saved=await api('/api/conversations',{method:'POST',body:JSON.stringify({id:state.conversationId,
      title:(state.messages.find(m=>m.role==='user')?.content||'교육 기록 대화').slice(0,50),messages:state.messages})});
    state.messages=saved.messages;renderMessages();$('#saved-indicator').textContent='✓ 대화를 수동 저장했습니다';toast('현재 대화와 도구 호출 이력을 저장했습니다.');
  }catch(error){toast(error.message);$('#saved-indicator').textContent='수동 저장 실패 · 다시 시도해 주세요';}
  finally{state.busy=false;$('#save-chat').textContent='대화 저장';updateChatControls();}
}
function newChat(){if(state.busy){toast('현재 답변을 기다린 뒤 새 대화를 시작해 주세요.');return;}state.messages=[];state.conversationId=null;renderMessages();$('#saved-indicator').textContent='대화는 답변 후 자동 저장돼요';navigate('chat');$('#chat-input').focus();}
async function ask(question) {
  await navigate('chat');$('#chat-input').value=question;$('#chat-input').focus();
}
$('#chat-form').addEventListener('submit',async event=>{
  event.preventDefault();if(state.busy)return;const input=$('#chat-input');const message=input.value.trim();if(!message)return;
  if(!state.summary){toast('먼저 교육 데이터를 연결해 주세요.');return;}
  state.busy=true;$('#send-button').disabled=true;state.messages.push({role:'user',content:message});renderMessages();input.value='';
  window.AcademyWorkspace?.chatState('working','교육 기록을 바탕으로 답변을 준비하고 있어요.');
  const pending=element('div','message assistant pending','교육 기록을 살펴보고 있어요…');$('#messages').append(pending);$('#messages').scrollTop=$('#messages').scrollHeight;
  const payload={message,conversation_id:state.conversationId,agent_id:state.agentId};if(state.year){payload.date_from=`${state.year}-01-01`;payload.date_to=`${state.year}-12-31`;}
  try{const response=await api('/api/chat',{method:'POST',body:JSON.stringify(payload)});state.conversationId=response.conversation_id;if(response.user_message)state.messages[state.messages.length-1].content=response.user_message;state.messages.push({role:'assistant',content:response.answer});$('#saved-indicator').textContent='✓ 대화가 저장되었습니다';renderMessages();if(response.privacy_notice)toast(response.privacy_notice);window.AcademyWorkspace?.chatState('success','답변과 대화를 저장했어요.');}
  catch(error){pending.remove();state.messages.pop();renderMessages();input.value=message;toast(error.message);$('#saved-indicator').textContent='저장되지 않았습니다 · 다시 시도해 주세요';window.AcademyWorkspace?.chatState('error','연결을 확인해 주세요. 답변은 저장되지 않았어요.');}
  finally{state.busy=false;updateChatControls();input.focus();}
});
$('#chat-input').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();$('#chat-form').requestSubmit();}});
async function loadHistory() {
  const response=await api('/api/conversations');const list=$('#history-list');list.replaceChildren();
  if(!response.items.length){list.append(empty('아직 저장된 대화가 없어요','AI 비서와 첫 이야기를 나눠 보세요.'));return;}
  for(const row of response.items){
    const card=element('article','history-card');const top=element('div','history-card-top');const icon=element('span');icon.innerHTML=svg('history');top.append(icon,element('span','',row.agent_id==='report'?'캔디봄 · 보고서 도우미와의 대화':'캔디빛 · 교육 분석 비서와의 대화'));card.append(top,element('h3','',row.title),element('p','',`${new Date(row.updated_at).toLocaleString('ko-KR')} · 메시지 ${row.message_count}개`));
    const actions=element('div','history-actions');const remove=element('button','button secondary','삭제');remove.onclick=()=>confirmDelete(async()=>{await api('/api/conversations/'+row.id,{method:'DELETE'});if(state.conversationId===row.id){state.conversationId=null;state.messages=[];renderMessages();}await loadHistory();toast('대화 기록을 삭제했습니다.');});
    const load=element('button','button primary','대화 이어가기 ↗');load.onclick=async()=>{if(state.busy){toast('진행 중인 답변을 기다려 주세요.');return;}try{const detail=await api('/api/conversations/'+row.id);state.conversationId=detail.id;state.messages=detail.messages;state.agentId=detail.agent_id || 'analysis';window.AcademyWorkspace?.setChatAgent(state.agentId,false);renderMessages();$('#saved-indicator').textContent='✓ 저장된 대화를 불러왔습니다';await navigate('chat');}catch(error){toast(error.message);}};
    actions.append(remove,load);card.append(actions);list.append(card);
  }
}
$$('[data-view]').forEach(button=>button.onclick=()=>navigate(button.dataset.view));
$$('[data-go]').forEach(button=>button.onclick=()=>navigate(button.dataset.go));
$$('[data-question]').forEach(button=>button.onclick=()=>ask(button.dataset.question));
$$('[data-close]').forEach(button=>button.onclick=()=>$('#'+button.dataset.close).close());
$('#hero-chat').onclick=()=>navigate('chat');$('#report-question').onclick=()=>ask('기록에 근거한 강사 활동 보고서 초안을 작성해 줘.');
$('#new-chat').onclick=newChat;$('#history-new-chat').onclick=newChat;$('#add-data').onclick=()=>openRecord();
$('#save-chat').onclick=saveCurrentChat;
$('#refresh-button').onclick=()=>refresh();
async function changeYear(event){state.year=event.target.value;state.offset=0;$('#year-filter').value=state.year;$('#chat-year-filter').value=state.year;await refresh();}
$('#year-filter').onchange=changeYear;
$('#chat-year-filter').onchange=changeYear;
$('#search-form').onsubmit=async event=>{event.preventDefault();state.offset=0;try{await loadData();}catch(error){toast(error.message);}};
$('#mode-filter').onchange=()=>$('#search-form').requestSubmit();
$('#previous-page').onclick=async()=>{state.offset=Math.max(0,state.offset-state.limit);try{await loadData();}catch(error){toast(error.message);}};
$('#next-page').onclick=async()=>{state.offset+=state.limit;try{await loadData();}catch(error){toast(error.message);}};
function settingsError(message){let box=$('#settings-error');if(!box){box=element('p','form-error');box.id='settings-error';box.setAttribute('role','alert');$('#settings-form .dialog-actions').before(box);}box.textContent=message;box.hidden=!message;}
function openConnectionSettings(){settingsError('');$('#api-url').value=apiBase();$('#access-key').value=sessionStorage.getItem('academy_access_key') || '';if(!$('#settings-dialog').open)$('#settings-dialog').showModal();$('#access-key').focus();}
$('#settings-button').onclick=openConnectionSettings;
$('#top-settings-button').onclick=$('#settings-button').onclick;
$('#settings-form').onsubmit=async event=>{
  event.preventDefault();const url=$('#api-url').value.trim().replace(/\/$/,'');
  if(url&&!/^https?:\/\//.test(url)){settingsError('http:// 또는 https://로 시작하는 서비스 주소를 입력해 주세요.');return;}
  const button=$('#settings-form button[type=submit]');button.disabled=true;button.textContent='연결 확인 중…';settingsError('');
  sessionStorage.setItem('academy_api_url',url);sessionStorage.setItem('academy_access_key',$('#access-key').value.trim());
  try{if(await refresh()){$('#settings-dialog').close();window.dispatchEvent(new Event('academy:connected'));}else settingsError($('#notice').textContent||'연결 정보를 확인해 주세요.');}
  finally{button.disabled=false;button.textContent='연결하기';}
};
$('#export-button').onclick=async()=>{try{const data=await api('/api/data/export'+periodQuery());const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json;charset=utf-8'});const url=URL.createObjectURL(blob);const link=element('a');link.href=url;link.download=`academy-data-${state.year || 'all'}.json`;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('교육 데이터를 JSON 파일로 내보냈습니다.');}catch(error){toast(error.message);}};
window.addEventListener('hashchange',()=>navigate(location.hash.slice(1)));
async function start(){await refresh();await navigate(location.hash.slice(1)||'agents');}
start();
