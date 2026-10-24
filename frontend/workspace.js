(() => {
  'use strict';
  const agents = {
    calendar:{name:'모모',role:'일정 매니저',color:'mint',intro:'월별 기록을 펼쳐 날짜와 시간대별 수업을 정리해요.',action:'월별 수업 정리',tag:'SCHEDULE'},
    materials:{name:'루미',role:'교재 사서',color:'lilac',intro:'흩어진 슬라이드를 과목별로 연결하고 찾아드려요.',action:'교재 슬라이드 찾기',tag:'LIBRARY'},
    analysis:{name:'코코',role:'교육 분석 비서',color:'peach',intro:'교육시간과 운영 기록에서 의미 있는 흐름을 찾아요.',action:'교육 기록 분석하기',tag:'INSIGHTS'},
    report:{name:'보리',role:'보고서 도우미',color:'butter',intro:'차곡차곡 쌓인 수업을 활동 보고서로 풀어드려요.',action:'활동 보고서 준비',tag:'REPORT'}
  };
  let calendarData=null,selectedMonth=null,subjectGroups=[],slideBlob=null,calendarSequence=0,slideSequence=0;
  const statusLabels={idle:'기다리고 있어요',ready:'함께 시작해요',working:'도와드리는 중',success:'정리가 끝났어요',error:'연결을 확인해요'};
  const svgStart='<svg class="character-svg" viewBox="0 0 160 160" aria-hidden="true"><ellipse cx="80" cy="145" rx="38" ry="6" fill="#d7d2e3" opacity=".35"/><g class="char-body" stroke="#655b79" stroke-width="2.2" stroke-linejoin="round">';
  const svgEnd='</g><g class="char-sparkles" stroke="none" fill="#c6ad78"><path d="m132 24 3 7 7 3-7 3-3 7-3-7-7-3 7-3Z"/><circle cx="21" cy="75" r="3"/></g></svg>';
  function character(id){
    const eyes='<g class="char-eyes" stroke="none" fill="#5c536b"><ellipse cx="64" cy="69" rx="3.5" ry="5"/><ellipse cx="96" cy="69" rx="3.5" ry="5"/></g>';
    const blush='<ellipse cx="50" cy="82" rx="8" ry="4" fill="#efaeb3" opacity=".55" stroke="none"/><ellipse cx="110" cy="82" rx="8" ry="4" fill="#efaeb3" opacity=".55" stroke="none"/>';
    let body='';
    if(id==='calendar')body='<ellipse cx="59" cy="30" rx="12" ry="25" fill="#b4deca" transform="rotate(-12 59 30)"/><ellipse cx="98" cy="30" rx="12" ry="25" fill="#b4deca" transform="rotate(12 98 30)"/><path d="M49 110q-7 17 4 28h19l5-15h7l5 15h20q9-13-1-28" fill="#a9d4c1"/><ellipse cx="80" cy="73" rx="47" ry="41" fill="#c7e8d9"/>'+eyes+blush+'<path d="m73 82 7 6 7-6" fill="none"/><g class="char-hand"><ellipse cx="122" cy="109" rx="10" ry="16" fill="#b4deca" transform="rotate(-30 122 109)"/></g><rect x="43" y="100" width="63" height="40" rx="7" fill="#fffdf7"/><path d="M43 112h63m-48-16v11m33-11v11" fill="none"/><path d="m61 125 7 6 18-12" fill="none" stroke="#74ac93" stroke-width="4"/>';
    if(id==='materials')body='<path d="M40 66 40 23l27 18q14-4 27 0l27-18v43" fill="#cab5e5"/><ellipse cx="80" cy="89" rx="48" ry="51" fill="#d6c6ed"/><path d="M49 133q-4 12 13 10m35-10q20 11 17-3" fill="#edc99e"/><ellipse cx="60" cy="70" rx="20" ry="24" fill="#fffaf4"/><ellipse cx="100" cy="70" rx="20" ry="24" fill="#fffaf4"/>'+eyes+'<path d="m73 82 7 10 7-10Z" fill="#edc99e"/><g class="char-hand"><ellipse cx="122" cy="103" rx="11" ry="23" fill="#c4acdf" transform="rotate(-25 122 103)"/></g><path d="M38 108q22-8 42 3 22-11 42-3v31q-20-7-42 3-20-10-42-3Z" fill="#fff9e9"/><path d="M80 111v31M47 119l24 3m-24 6 24 3m18-9 23-3m-23 12 23-3" fill="none" stroke="#b2a0cd"/>';
    if(id==='analysis')body='<path d="M78 26V13" fill="none"/><circle class="char-antenna" cx="78" cy="12" r="6" fill="#b7d9cf"/><rect x="37" y="34" width="86" height="65" rx="24" fill="#f3c9b5"/><rect x="48" y="45" width="64" height="43" rx="17" fill="#fff7f0"/>'+eyes+'<path d="M71 80q9 6 18 0" fill="none"/><rect x="45" y="100" width="70" height="37" rx="12" fill="#f6d3c3"/><rect x="59" y="109" width="42" height="19" rx="5" fill="#fff9ee"/><path d="m65 122 7-5 7 2 14-7" fill="none" stroke="#92b7a6" stroke-width="3"/><path d="m58 136-2 8m48-8 2 8" fill="none" stroke-width="8"/><g class="char-hand"><path d="m119 104 14-10 5 9-14 13" fill="#f3c9b5"/></g><path d="m41 104-13 8 3 12 14-9" fill="#f3c9b5"/>';
    if(id==='report')body='<circle cx="46" cy="39" r="17" fill="#e8ca86"/><circle cx="113" cy="39" r="17" fill="#e8ca86"/><ellipse cx="80" cy="73" rx="46" ry="42" fill="#f5dfa7"/>'+eyes+blush+'<ellipse cx="80" cy="83" rx="14" ry="10" fill="#fff4d6" stroke="none"/><path d="m76 79 4 4 4-4m-4 4v5" fill="none"/><path d="M51 106q-10 20-2 34h23l4-13h8l5 13h23q5-19-4-34" fill="#edcf91"/><rect x="47" y="102" width="58" height="39" rx="5" fill="#fffdf4"/><path d="M58 114h32m-32 9h25m-25 8h19" stroke="#c6b58b"/><g class="char-hand"><ellipse cx="121" cy="111" rx="10" ry="17" fill="#f0d49b" transform="rotate(25 121 111)"/><path d="m104 118 21-34 7 4-21 34-9 5Z" fill="#bdabd6"/></g>';
    return svgStart+body+svgEnd;
  }
  function charNode(id,className='') {const node=element('div',`agent-character ${className}`);node.dataset.characterId=id;node.dataset.state='idle';node.innerHTML=character(id);return node;}
  function setAgentState(id,status,message,showDock=true){
    $$(`[data-character-id="${id}"]`).forEach(node=>{node.dataset.state=status;});
    const card=$(`[data-agent-card="${id}"]`);if(card){$('.agent-state-label',card).textContent=statusLabels[status];card.dataset.state=status;}
    if(showDock){const agent=agents[id];$('#activity-character').replaceChildren(charNode(id));$('#activity-character .agent-character').dataset.state=status;$('#activity-name').textContent=`${agent.name} · ${agent.role}`;$('#activity-message').textContent=message;$('#agent-activity').hidden=false;}
  }
  async function runAgent(id,work){setAgentState(id,'working',id==='calendar'?'날짜와 시간대별 수업을 정리하고 있어요.':'연결된 과목과 교재를 찾고 있어요.');try{await work();setAgentState(id,'success',id==='calendar'?'월을 선택해 수업 기록을 펼쳐보세요.':'과목별로 연결된 교재를 준비했어요.');}catch(error){setAgentState(id,'error',error.message);throw error;}}
  async function launchAgent(id){
    if(state.busy){toast('진행 중인 답변을 기다려 주세요.');return;}
    if(id==='calendar'||id==='materials'){await navigate(id);return;}
    setChatAgent(id,true);await navigate('chat');
    if(id==='report')$('#chat-input').value='선택 기간의 교육 기록에 근거해 강사 활동 보고서 초안을 작성해 줘. 기준 기간, 주요 실적, 해석과 제안을 구분해 줘.';
    setAgentState(id,'ready',id==='report'?'보고서 질문을 준비했어요. 보내기를 누르면 작성할게요.':'교육 기록을 함께 살펴볼게요. 질문을 입력해 주세요.');$('#chat-input').focus();
  }
  function renderAgents(){
    const grid=$('#agent-grid');
    for(const [id,agent] of Object.entries(agents)){
      const card=element('article',`agent-card ${agent.color}`);card.dataset.agentCard=id;card.dataset.state='idle';
      const top=element('div','agent-card-top');top.append(element('span','',agent.tag),element('span','agent-state-label',statusLabels.idle));
      const visual=element('button','agent-visual-button');visual.type='button';visual.setAttribute('aria-label',`${agent.name} ${agent.role} 호출`);visual.append(charNode(id));visual.onclick=()=>launchAgent(id);
      const name=element('h3','',agent.name);name.append(element('span','',agent.role));const action=element('button','button agent-call',`${agent.action} ↗`);action.onclick=()=>launchAgent(id);
      card.append(top,visual,name,element('p','agent-description',agent.intro),action);grid.append(card);
    }
    $$('[data-character]').forEach(node=>node.append(charNode(node.dataset.character)));
  }
  function setChatAgent(id,reset){
    if(!['analysis','report'].includes(id))id='analysis';
    if(state.busy)return;
    if(reset){state.messages=[];state.conversationId=null;renderMessages();$('#saved-indicator').textContent='대화는 답변 후 자동 저장돼요';}
    state.agentId=id;$('#chat-agent-avatar').replaceChildren(charNode(id));$('#chat-welcome-character').replaceChildren(charNode(id));$('#chat-agent-name').textContent=`${agents[id].name} · ${agents[id].role}`;
    $$('[data-chat-agent]').forEach(button=>{const selected=button.dataset.chatAgent===id;button.classList.toggle('selected',selected);button.setAttribute('aria-pressed',String(selected));});
  }
  async function loadCalendar(){
    const sequence=++calendarSequence;const response=await api('/api/data/calendar?year='+$('#calendar-year').value);if(sequence!==calendarSequence)return;
    calendarData=response;$('#calendar-year-total').textContent=`실적 ${number(response.hours)}시간 · ${number(response.record_count)}개 기록`;
    const picker=$('#calendar-year');const selected=picker.value;picker.replaceChildren();for(const year of response.available_years){const option=element('option','',`${year}년`);option.value=year;picker.append(option);}if(!response.available_years.includes(response.year)){const option=element('option','',`${response.year}년`);option.value=response.year;picker.append(option);}picker.value=selected;
    const same=selectedMonth?.startsWith(String(response.year))&&response.months.some(m=>m.month===selectedMonth);if(!same)selectedMonth=[...response.months].reverse().find(m=>m.has_records||m.planning?.count)?.month || response.months[0].month;
    renderMonthGrid();renderMonthDetail();
  }
  function renderMonthGrid(){
    const grid=$('#month-grid');grid.replaceChildren();
    for(const month of calendarData.months){const button=element('button','month-block');button.type='button';button.dataset.month=month.month;button.classList.toggle('selected',month.month===selectedMonth);button.setAttribute('aria-pressed',String(month.month===selectedMonth));button.setAttribute('aria-label',`${Number(month.month.slice(5))}월 ${month.has_records?number(month.hours)+'시간, '+month.day_count+'일':'보유 기록 없음'}`);
      const top=element('div','month-block-top');top.append(element('strong','',`${Number(month.month.slice(5))}월`),element('span','',month.has_records?'↗':'·'));
      const value=element('div','month-block-value',month.has_records?number(month.hours):'—');value.append(element('span','',month.has_records?'시간':''));
      button.append(top,value,element('p','',month.has_records?`실적 ${month.day_count}일 · ${month.record_count}건`:month.planning?.count?'교육결과 기록 미등록':'보유 기록 없음'));
      if(month.planning?.count){const plans=element('span','month-plan-count',`계획 ${month.planning.count}건${month.planning.by_status.held?' · 보류 '+month.planning.by_status.held+'건':''}`);button.append(plans);button.setAttribute('aria-label',button.getAttribute('aria-label')+`, 계획 ${month.planning.count}건, 보류 ${month.planning.by_status.held}건`);}
      button.onclick=()=>{selectedMonth=month.month;renderMonthGrid();renderMonthDetail();(month.planning?.count?$('#plan-detail'):$('#month-detail')).scrollIntoView({behavior:'smooth',block:'start'});};grid.append(button);}
  }
  function renderMonthDetail(){
    renderPlans();
    const month=calendarData.months.find(m=>m.month===selectedMonth);$('#selected-month-title').textContent=`${calendarData.year}년 ${Number(month.month.slice(5))}월 수업 기록`;$('#selected-month-total').textContent=month.has_records?`총 ${number(month.hours)}시간 · ${month.day_count}일`:'';
    const list=$('#day-blocks');list.replaceChildren();if(!month.has_records){list.append(empty('이 달에 보유한 교육 기록이 없습니다','교육 미실시를 뜻하지 않습니다.'));return;}
    for(const day of month.days){
      const block=element('article','day-block');const header=element('div','day-block-heading');const weekday=new Date(day.date+'T12:00:00').toLocaleDateString('ko-KR',{weekday:'short'});header.append(element('h3','',`${Number(day.date.slice(8))}일 ${weekday}요일`),element('span','',`${number(day.hours)}시간 · 교육일별 ${day.record_count}건`));block.append(header);
      const units=[];for(const record of day.records){if(record.schedule_units.length){for(const unit of record.schedule_units)units.push({record,time:`${unit.start_time}–${unit.end_time}`,sort:unit.start_time,hours:unit.hours,topic:unit.topic});}else units.push({record,time:'시간대 미입력',sort:'99:99',hours:record.hours,topic:record.memo});}
      units.sort((a,b)=>a.sort.localeCompare(b.sort)||a.record.id.localeCompare(b.record.id));
      for(const unit of units){const row=element('div','time-block');const time=element('div','time-label');time.append(element('strong','',unit.time),element('small','',`${number(unit.hours)}시간${unit.record.edited?' · 원본 시간표':''}`));const content=element('div','time-content');content.append(element('h4','',unit.record.title),element('p','',unit.topic));const meta=element('div','time-meta');const tag=element('span','mode-tag',unit.record.mode);tag.dataset.mode=unit.record.mode;meta.append(tag);if(unit.record.venue)meta.append(element('span','',unit.record.venue));if(unit.record.edited)meta.append(element('span','edited-note','수정 기록 · 합계는 수정된 교육시간 기준'));content.append(meta);row.append(time,content);block.append(row);}
      list.append(block);
    }
  }
  function renderPlans(){
    const month=calendarData.months.find(m=>m.month===selectedMonth),summary=month.planning;
    $('#plan-detail').hidden=!summary?.count;if(!summary?.count)return;
    $('#plan-month-title').textContent=`${calendarData.year}년 ${Number(month.month.slice(5))}월 교육계획·진행상태`;
    const counts=summary.by_status;$('#plan-counts').textContent=[counts.scheduled?`등록 계획 ${counts.scheduled}건 · ${number(summary.scheduled_hours)}시간`:'',counts.held?`보류 ${counts.held}건 · ${number(summary.held_hours)}시간`:'',counts.completed?`실시·승인 확인 ${counts.completed}건`:''].filter(Boolean).join(' / ');
    const policy=['전산에 등록된 교육계획입니다. 실시·승인 및 보류 상태는 별도로 확인한 내용에 따라 표시합니다.'];
    if(summary.review_after.length)policy.push(`교육 방향 재확인 기준일: ${summary.review_after.map(day=>new Date(day+'T12:00:00').toLocaleDateString('ko-KR')).join(', ')} 이후.`);
    if(summary.conditional_zoom_count)policy.push('조건부 온라인 대체 계획이 있습니다. 각 수업의 대체 조건을 확인해 주세요. 확정 전에는 기존 일정을 유지합니다.');
    $('#plan-policy').textContent=policy.join(' ');
    const filter=$('#plan-status-filter').value,items=month.plans.filter(plan=>!filter||plan.status===filter),list=$('#plan-list');list.replaceChildren();
    if(!items.length){list.append(empty('이 상태에 해당하는 계획이 없습니다'));return;}
    const labels={scheduled:'등록 계획',held:'보류',completed:'실시·승인 완료',cancelled:'폐강 확정'};
    for(const plan of items){const card=element('article','plan-card');card.dataset.planStatus=plan.status;const time=element('div','plan-date');const day=new Date(plan.date+'T12:00:00').toLocaleDateString('ko-KR',{month:'long',day:'numeric',weekday:'short'});time.append(element('strong','',day),element('span','',`${plan.start_time}–${plan.end_time}`),element('small','',`계획 ${number(plan.planned_hours)}시간`));const content=element('div','plan-content');const top=element('div','plan-card-top');const badge=element('span','plan-status',labels[plan.status]||plan.status);top.append(badge,element('span','plan-institution',`${plan.region} · ${plan.institution.replace(/\n/g,' ')}`));content.append(top,element('h3','',plan.title),element('p','plan-audience',`계획 대상: ${plan.audience_raw} · ${plan.delivery_mode}`));if(plan.status!=='scheduled')content.append(element('p','plan-status-note',plan.status_note));if(plan.replacement_condition)content.append(element('p','plan-replacement',plan.replacement_condition));const detail=element('details','plan-source');detail.append(element('summary','','교육 내용·출처 보기'),element('p','',plan.content),element('small','',`원본: ${plan.source_file} · 표 ${plan.source_table+1}, ${plan.source_row+1}행`));content.append(detail);card.append(time,content);list.append(card);}
  }
  async function loadSubjects(){const response=await api('/api/materials/subjects');subjectGroups=response.items;const options=$('#subject-options');options.replaceChildren();for(const group of subjectGroups){const option=element('option');option.value=group.subject;options.append(option);}renderSubjects();}
  function safeLink(value){try{const url=new URL(value);return url.protocol==='https:'&&!url.username&&!url.password?url.href:null;}catch{return null;}}
  function externalLink(url,label,className='button secondary'){const node=element('a',className,label);node.href=safeLink(url)||'#';node.target='_blank';node.rel='noopener noreferrer';return node;}
  function renderSubjects(){
    const query=$('#subject-search').value.trim().toLowerCase();const connected=$('#connected-only').checked;const groups=subjectGroups.filter(group=>(!connected||group.materials.length)&&(!query||`${group.subject} ${group.materials.map(m=>m.title).join(' ')}`.toLowerCase().includes(query)));
    $('#library-count').textContent=`${groups.length}개 과목 · 교재 ${groups.reduce((n,g)=>n+g.materials.length,0)}개`;
    const grid=$('#subject-grid');grid.replaceChildren();if(!groups.length){grid.append(empty(connected?'아직 연결된 교재가 없습니다':'찾는 과목이 없습니다',connected?'‘연결된 교재만 보기’를 해제하면 수업 과목을 볼 수 있어요.':''));return;}
    for(const group of groups){const card=element('article','subject-card panel');const top=element('div','subject-card-top');top.append(element('span','subject-book','▤'),element('span','',group.course_count?`원본 과정 ${group.course_count}건`:'교재 분야'));card.append(top,element('h3','',group.subject));
      if(!group.materials.length)card.append(element('p','material-empty','교재 연결 전'));
      for(const material of group.materials){const row=element('div','material-row');const info=element('div');info.append(element('strong','',material.title),element('small','',`${material.source_platform || (material.source_type==='local_file'?'이 컴퓨터':material.kind==='canva'?'Canva':'원본 링크')}${material.page_count?' · '+material.page_count+'쪽':''}`));const button=element('button','material-open','슬라이드 보기 ↗');button.onclick=()=>openSlides(material);row.append(info,button);card.append(row);}
      const add=element('button','text-button','이 과목에 교재 연결 +');add.onclick=()=>openMaterialForm(group.subject);card.append(add);grid.append(card);
    }
  }
  function openMaterialForm(subject=''){$('#material-form').reset();$('#material-form').elements.subject.value=subject;$('#material-dialog').showModal();}
  $('#material-form').addEventListener('submit',async event=>{event.preventDefault();const button=$('#material-submit');button.disabled=true;try{const values=Object.fromEntries(new FormData(event.currentTarget));if(!safeLink(values.url))throw new Error('https://로 시작하는 교재 원본 주소를 입력해 주세요.');await api('/api/materials',{method:'POST',body:JSON.stringify(values)});$('#material-dialog').close();await runAgent('materials',loadSubjects);toast('과목에 교재 링크를 연결했습니다.');}catch(error){toast(error.message);}finally{button.disabled=false;}});
  async function openSlides(material){
    const sequence=++slideSequence;
    const note=$('#slide-note');note.textContent=material.note||'';note.hidden=!material.note;
    $('#slide-title').textContent=material.title;$('#slide-subject').textContent=material.subject;const stage=$('#slide-stage'),tools=$('#slide-tools');stage.replaceChildren(empty('교재를 준비하고 있어요'));tools.replaceChildren();$('#slide-dialog').showModal();setAgentState('materials','working','선택한 교재를 열고 있어요.');
    if(slideBlob){URL.revokeObjectURL(slideBlob);slideBlob=null;}
    try{
      if(material.source_type==='local_file'){
        const headers={};const token=sessionStorage.getItem('academy_access_key');if(token)headers.Authorization=`Bearer ${token}`;
        const response=await fetch(apiBase()+'/api/materials/'+encodeURIComponent(material.id)+'/file',{headers});if(!response.ok)throw new Error('교재 파일을 열 수 없습니다. 서비스 연결을 확인해 주세요.');
        const blob=await response.blob();if(sequence!==slideSequence)return;
        slideBlob=URL.createObjectURL(blob);stage.replaceChildren();
        if(material.kind==='pdf'){const frame=element('iframe','pdf-slide-frame');frame.src=slideBlob;frame.title=material.title+' PDF 슬라이드';stage.append(frame);}
        else stage.append(empty('PowerPoint 원본이 준비되었습니다','아래 버튼으로 내려받아 PowerPoint에서 열어보세요.'));
        const download=element('a','button primary','원본 파일 다운로드');download.href=slideBlob;download.download=material.file_name;tools.append(download);
      }else{
        const pages=(material.preview_pages||[]).filter(page=>!page.expires_at||page.expires_at*1000>Date.now());
        if(pages.length){let current=0;const image=element('img','canva-slide-preview');image.alt=material.title+' 슬라이드 미리보기';image.referrerPolicy='no-referrer';const counter=element('span','slide-counter');const previous=element('button','button secondary','← 이전');const next=element('button','button secondary','다음 →');const paint=()=>{image.src=pages[current].url;counter.textContent=`미리보기 ${current+1} / ${pages.length}${material.page_count?' · 원본 '+material.page_count+'쪽':''}`;previous.disabled=current===0;next.disabled=current===pages.length-1;};previous.onclick=()=>{current--;paint();};next.onclick=()=>{current++;paint();};image.onerror=()=>{stage.replaceChildren(empty('미리보기를 불러올 수 없습니다','원본 열기를 눌러 전체 슬라이드를 확인해 주세요.'));};stage.replaceChildren(image);tools.append(previous,counter,next);paint();}
        else if(material.kind==='pdf'&&safeLink(material.url)){const frame=element('iframe','pdf-slide-frame');frame.src=safeLink(material.url);frame.title=material.title+' PDF 슬라이드';frame.referrerPolicy='no-referrer';stage.replaceChildren(frame);}
        else stage.replaceChildren(empty(material.kind==='canva'?'Canva 원본 슬라이드가 연결되어 있어요':'교재 원본이 연결되어 있어요','아래 원본 열기로 전체 내용을 확인하세요. 원본의 로그인 조건이 적용됩니다.'));
        if(safeLink(material.url))tools.append(externalLink(material.url,material.kind==='canva'?'Canva에서 전체 슬라이드 열기 ↗':'교재 원본 열기 ↗','button primary'));
      }
      setAgentState('materials','success','교재를 열었어요. 원본의 로그인 조건은 유지됩니다.');
    }catch(error){if(sequence!==slideSequence)return;stage.replaceChildren(empty('교재를 열지 못했습니다',error.message));setAgentState('materials','error',error.message);}
  }
  $('#slide-dialog').addEventListener('close',()=>{slideSequence++;$('#slide-stage').replaceChildren();if(slideBlob){URL.revokeObjectURL(slideBlob);slideBlob=null;}});
  $('#calendar-year').onchange=()=>runAgent('calendar',loadCalendar).catch(error=>toast(error.message));
  $('#plan-status-filter').onchange=renderPlans;
  $('#subject-search').oninput=renderSubjects;$('#connected-only').onchange=renderSubjects;$('#add-material').onclick=()=>openMaterialForm();$('#close-activity').onclick=()=>{$('#agent-activity').hidden=true;};
  $$('[data-launch-agent]').forEach(button=>button.onclick=()=>launchAgent(button.dataset.launchAgent));
  $$('[data-chat-agent]').forEach(button=>button.onclick=()=>launchAgent(button.dataset.chatAgent));
  $('#report-question').onclick=()=>launchAgent('report');
  renderAgents();setChatAgent(state.agentId,false);
  window.AcademyWorkspace={
    onNavigate:async view=>{if(view==='calendar')await runAgent('calendar',loadCalendar);if(view==='materials')await runAgent('materials',loadSubjects);},
    summaryChanged:s=>{$('#hub-records').textContent=`교육일별 기록 ${number(s.count)}건`;$('#hub-hours').textContent=`교육시간 ${number(s.metrics.total)}시간`;},
    chatState:(status,message)=>setAgentState(state.agentId,status,message),setChatAgent,launchAgent
  };
  if(state.summary)window.AcademyWorkspace.summaryChanged(state.summary);
})();
