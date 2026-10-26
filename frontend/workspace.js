(() => {
  'use strict';
  const agents = {
    calendar:{name:'캔디온',role:'일정 안내',color:'mint',intro:'월별 기록을 펼쳐 날짜와 시간대별 수업을 정리해요.',action:'월별 수업 정리',tag:'SCHEDULE'},
    materials:{name:'캔디북',role:'교재 안내',color:'lilac',intro:'흩어진 슬라이드를 과목별로 연결하고 찾아드려요.',action:'교재 슬라이드 찾기',tag:'LIBRARY'},
    analysis:{name:'캔디빛',role:'교육 분석 비서',color:'peach',intro:'교육시간과 운영 기록에서 의미 있는 흐름을 찾아요.',action:'교육 기록 분석하기',tag:'INSIGHTS'},
    report:{name:'캔디봄',role:'보고서 도우미',color:'butter',intro:'차곡차곡 쌓인 수업을 활동 보고서로 풀어드려요.',action:'활동 보고서 준비',tag:'REPORT'}
  };
  let calendarData=null,selectedMonth=null,subjectGroups=[],slideBlob=null,calendarSequence=0,slideSequence=0,materialLinkHandled=false,pdfViewerCleanup=null;
  const statusLabels={idle:'기다리고 있어요',ready:'함께 시작해요',working:'도와드리는 중',success:'정리가 끝났어요',error:'연결을 확인해요'};
  const characterAssets={calendar:'candy-on-3d.png',materials:'candy-book-3d.png',analysis:'candy-bit-3d.png',report:'candy-bom-3d.png'};
  function character(id){
    const agent=agents[id];
    return `<img class="character-image" src="assets/characters/${characterAssets[id]}" width="1024" height="1536" alt="${agent.name}, ${agent.role} · 3D 미래형 전신 캐릭터" decoding="async" draggable="false">`;
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
      if(month.planning?.count){const plans=element('span','month-plan-count',`계획 ${month.planning.count}건${month.planning.by_status.held?' · 보류 '+month.planning.by_status.held+'건':''}${month.planning.by_status.cancelled?' · 폐강 '+month.planning.by_status.cancelled+'건':''}${month.planning.confirmed_zoom_count?' · Zoom 전환 '+month.planning.confirmed_zoom_count+'건':''}${month.planning.confirmed_online_count?' · 온라인 '+month.planning.confirmed_online_count+'회 '+number(month.planning.confirmed_online_hours)+'시간':''}`);button.append(plans);button.setAttribute('aria-label',button.getAttribute('aria-label')+`, 계획 ${month.planning.count}건, 보류 ${month.planning.by_status.held}건, 대면 폐강 ${month.planning.by_status.cancelled}건, Zoom 대체 확정 ${month.planning.confirmed_zoom_count||0}건, 온라인 확정 일정 ${month.planning.confirmed_online_count||0}회 ${number(month.planning.confirmed_online_hours||0)}시간`);}
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
    const counts=summary.by_status;
    $('#plan-counts').textContent=[counts.scheduled?`진행 예정 ${counts.scheduled}건 · ${number(summary.scheduled_hours)}시간`:'',counts.held?`보류 ${counts.held}건 · ${number(summary.held_hours)}시간`:'',counts.completed?`실시·승인 확인 ${counts.completed}건`:'',counts.cancelled?`대면 폐강 ${counts.cancelled}건`:'',summary.confirmed_zoom_count?`폐강 수업 Zoom 전환 ${summary.confirmed_zoom_count}건`:'',summary.confirmed_online_count?`온라인 일정 ${summary.confirmed_online_count}회 · ${number(summary.confirmed_online_hours)}시간`:''].filter(Boolean).join(' / ');
    const policy=['원본 교육계획과 사용자가 확인한 온라인 시간표를 함께 표시합니다. 예정 시간은 실제 실적에 더하지 않으며, 시간표만으로 전산 등록·실시·승인을 확정하지 않습니다.'];
    if(summary.review_after.length)policy.push(`교육 방향 재확인 기준일: ${summary.review_after.map(day=>new Date(day+'T12:00:00').toLocaleDateString('ko-KR')).join(', ')} 이후.`);
    if(summary.conditional_zoom_count)policy.push('조건부 온라인 대체 계획이 있습니다. 아직 확정되지 않은 대체 수업의 조건을 확인해 주세요.');
    if(summary.confirmed_zoom_count)policy.push(`폐강 원본 수업 ${summary.confirmed_zoom_count}건의 온라인 Zoom 전환이 확정되었습니다.${summary.zoom_schedule_pending_count?` 이 중 ${summary.zoom_schedule_pending_count}건은 대체 날짜·시간 확인 중입니다. 폐강된 원래 일정을 Zoom 확정 일정으로 보지 마세요.`:''}`);
    if(summary.confirmed_online_count)policy.push(`날짜·시간이 확인된 온라인 Zoom 일정은 ${summary.confirmed_online_count}회 · ${number(summary.confirmed_online_hours)}시간입니다. 과목명·인원·접속 정보는 별도로 확인합니다.`);
    if(summary.zoom_group_schedule_confirmed_count)policy.push('폐강 수업의 대체 전체 시간표가 연결되었습니다. 과목별 회차는 임의로 배정하지 않습니다.');
    const pendingOverlaps=summary.schedule_conflict_pending_count??summary.schedule_conflict_count;
    if(pendingOverlaps)policy.push(`시간이 겹쳐 확인이 필요한 일정 ${pendingOverlaps}쌍이 있습니다. 해당 카드의 확인 표시를 살펴보세요.`);
    if(summary.confirmed_distinct_overlap_count)policy.push(`같은 시간의 별개 수업 ${summary.confirmed_distinct_overlap_count}쌍은 사용자 확인에 따라 각각 유지합니다.`);
    $('#plan-policy').textContent=policy.join(' ');
    const filter=$('#plan-status-filter').value,items=month.plans.filter(plan=>!filter||(filter==='online'?plan.schedule_status==='confirmed'&&plan.delivery_mode==='온라인 Zoom':plan.status===filter)),list=$('#plan-list');list.replaceChildren();
    if(!items.length){list.append(empty('이 상태에 해당하는 계획이 없습니다'));return;}
    const labels={scheduled:'등록 계획',held:'보류',completed:'실시·승인 완료',cancelled:'대면 폐강 확정'};
    for(const plan of items){
      const card=element('article','plan-card');card.dataset.planStatus=plan.status;const online=plan.schedule_status==='confirmed'&&plan.delivery_mode==='온라인 Zoom';card.dataset.online=String(online);
      const time=element('div','plan-date');
      if(online)time.append(element('small','online-schedule-label','온라인 확정 일정'));
      if(plan.status==='cancelled')time.append(element('small','original-plan-label','폐강된 원래 일정'));
      const day=new Date(plan.date+'T12:00:00').toLocaleDateString('ko-KR',{month:'long',day:'numeric',weekday:'short'});
      time.append(element('strong','',day),element('span','',`${plan.start_time}–${plan.end_time}`),element('small','',`${online?'예정':'원본 계획'} ${number(plan.planned_hours)}시간`));
      const content=element('div','plan-content'),top=element('div','plan-card-top');
      top.append(element('span','plan-status',online?'온라인 일정 확정':labels[plan.status]||plan.status),element('span','plan-institution',`${plan.region} · ${plan.institution.replace(/\n/g,' ')}`));
      content.append(top,element('h3','',plan.title),element('p','plan-audience',`${online?'교육 대상':'원본 계획 대상'}: ${plan.audience_raw} · ${plan.delivery_mode}`));
      if(plan.status!=='scheduled'||online)content.append(element('p','plan-status-note',plan.status_note||''));
      for(const confirmed of [true,false]){
        const overlaps=(plan.schedule_conflicts||[]).filter(other=>Boolean(other.distinct_session_confirmed)===confirmed);
        if(overlaps.length)content.append(element('p',`plan-conflict${confirmed?' confirmed-separate':''}`,`${confirmed?'동시간대 별도 수업 · 사용자 확인 완료':'시간 중복 확인 필요'}: ${overlaps.map(other=>`${other.start_time}–${other.end_time} · ${other.institution||other.title}`).join(' / ')}. ${confirmed?'서로 다른 수업으로 각각 보존합니다.':'진행시간 또는 담당 강사를 확인해 주세요.'}`));
      }
      if(plan.replacement_status==='confirmed'){
        const replacement=element('div','plan-replacement confirmed-replacement');replacement.append(element('strong','',`${plan.replacement_mode||'온라인'} 대체 확정`));
        const scheduled=plan.replacement_schedule_status==='confirmed'&&plan.replacement_date&&plan.replacement_start_time&&plan.replacement_end_time;
        const grouped=plan.replacement_schedule_status==='group_confirmed'&&plan.replacement_schedule_group_id;
        replacement.append(element('p','',grouped?'온라인 대체 전체 시간표 연결 완료 · 과목별 회차 확인 중':scheduled?`대체 수업: ${plan.replacement_date} ${plan.replacement_start_time}–${plan.replacement_end_time}`:'대체 날짜·시간: 확인 중'));
        if(plan.replacement_note)replacement.append(element('p','',plan.replacement_note));
        if(grouped){const firstMonth=calendarData.months.find(m=>m.plans.some(p=>p.schedule_group_id===plan.replacement_schedule_group_id&&p.schedule_status==='confirmed'));if(firstMonth){const open=element('button','button secondary','온라인 대체 시간표 보기 ↗');open.type='button';open.onclick=()=>{selectedMonth=firstMonth.month;$('#plan-status-filter').value='online';renderMonthGrid();renderMonthDetail();$('#plan-detail').scrollIntoView({behavior:'smooth',block:'start'});};replacement.append(open);}}
        content.append(replacement);
      }else if(plan.replacement_condition)content.append(element('p','plan-replacement',plan.replacement_condition));
      const detail=element('details','plan-source');detail.append(element('summary','','교육 내용·출처 보기'),element('p','',plan.content),element('small','',`원본: ${plan.source_file}${Number.isInteger(plan.source_table)?` · 표 ${plan.source_table+1}`:''}${Number.isInteger(plan.source_row)?` · ${plan.source_row+1}행`:''}`));
      content.append(detail);card.append(time,content);list.append(card);
    }
  }
  async function loadSubjects(){
    const response=await api('/api/materials/subjects');subjectGroups=response.items;
    for(const group of subjectGroups)if(group.subject==='미드저니 입문→숙련')group.materials.sort((a,b)=>a.title.localeCompare(b.title,'ko',{numeric:true}));
    const options=$('#subject-options');options.replaceChildren();for(const group of subjectGroups){const option=element('option');option.value=group.subject;options.append(option);}
    const linked=new URLSearchParams(location.search);
    if(!materialLinkHandled&&linked.get('subject'))$('#subject-search').value=linked.get('subject').slice(0,200);
    renderSubjects();
    if(!materialLinkHandled){
      materialLinkHandled=true;
      const part=linked.get('part');
      if(linked.get('subject')==='미드저니 입문→숙련'&&/^[1-4]$/.test(part||'')){
        const material=subjectGroups.find(group=>group.subject===linked.get('subject'))?.materials.find(item=>item.title.startsWith(`미드저니 교재 PART ${part} ·`));
        if(material)await openSlides(material);else toast('선택한 교재를 찾지 못했습니다. 자료실에서 교재 목록을 확인해 주세요.');
      }
    }
  }
  function safeLink(value){try{const url=new URL(value);return url.protocol==='https:'&&!url.username&&!url.password?url.href:null;}catch{return null;}}
  function externalLink(url,label,className='button secondary'){const node=element('a',className,label);node.href=safeLink(url)||'#';node.target='_blank';node.rel='noopener noreferrer';return node;}
  function renderSubjects(){
    const query=$('#subject-search').value.trim().toLowerCase();const connected=$('#connected-only').checked;const groups=subjectGroups.filter(group=>(!connected||group.materials.length)&&(!query||`${group.subject} ${group.materials.map(m=>m.title).join(' ')}`.toLowerCase().includes(query)));
    $('#library-count').textContent=`${groups.length}개 과목 · 교재 ${groups.reduce((n,g)=>n+g.materials.length,0)}개`;
    const grid=$('#subject-grid');grid.replaceChildren();if(!groups.length){grid.append(empty(connected?'아직 연결된 교재가 없습니다':'찾는 과목이 없습니다',connected?'‘연결된 교재만 보기’를 해제하면 수업 과목을 볼 수 있어요.':''));return;}
    for(const group of groups){const card=element('article','subject-card panel');const top=element('div','subject-card-top');top.append(element('span','subject-book','▤'),element('span','',group.course_count?`원본 과정 ${group.course_count}건`:'교재 분야'));card.append(top,element('h3','',group.subject));
      if(!group.materials.length)card.append(element('p','material-empty','교재 연결 전'));
      for(const material of group.materials){const row=element('div','material-row');const info=element('div');info.append(element('strong','',material.title),element('small','',`${material.source_platform || (material.source_type==='firestore_file'?'비공개 PDF':material.source_type==='local_file'?'이 컴퓨터':material.kind==='canva'?'Canva':'원본 링크')}${material.page_count?' · '+material.page_count+'쪽':''}`));const button=element('button','material-open',material.kind==='pdf'?'PDF 보기 ↗':'슬라이드 보기 ↗');button.onclick=()=>openSlides(material);row.append(info,button);card.append(row);}
      const add=element('button','text-button','이 과목에 교재 연결 +');add.onclick=()=>openMaterialForm(group.subject);card.append(add);grid.append(card);
    }
  }
  let retryMaterialAfterConnection=false;
  const materialError=element('div','form-error');materialError.id='material-error';materialError.hidden=true;
  const materialErrorText=element('p');materialErrorText.setAttribute('role','alert');
  const connectMaterial=element('button','button secondary','접속 키 연결');connectMaterial.type='button';connectMaterial.hidden=true;connectMaterial.onclick=()=>openConnectionSettings();
  materialError.append(materialErrorText,connectMaterial);$('#material-form .dialog-actions').before(materialError);
  function openMaterialForm(subject=''){retryMaterialAfterConnection=false;materialError.hidden=true;$('#material-form').reset();$('#material-form').elements.subject.value=subject;$('#material-dialog').showModal();}
  $('#material-dialog').addEventListener('close',()=>{retryMaterialAfterConnection=false;});
  window.addEventListener('academy:connected',()=>{if(retryMaterialAfterConnection&&$('#material-dialog').open){retryMaterialAfterConnection=false;$('#material-form').requestSubmit();}});
  $('#material-form').addEventListener('submit',async event=>{
    event.preventDefault();const button=$('#material-submit');button.disabled=true;button.textContent='저장 중…';materialError.hidden=true;
    let saved=false;
    try{
      const values=Object.fromEntries(new FormData(event.currentTarget));if(!safeLink(values.url))throw new Error('https://로 시작하는 교재 원본 주소를 입력해 주세요.');
      await api('/api/materials',{method:'POST',body:JSON.stringify(values)});saved=true;retryMaterialAfterConnection=false;$('#material-dialog').close();
      $('#subject-search').value=values.subject;await runAgent('materials',loadSubjects);toast('과목에 교재 링크를 연결했습니다.');
    }catch(error){
      if(saved){toast('교재는 저장했습니다. 목록 갱신을 위해 새로고침해 주세요.');return;}
      const needsConnection=error.status===401;retryMaterialAfterConnection=needsConnection;
      materialErrorText.textContent=needsConnection?'개인 접속 키 연결이 필요합니다. 입력 내용은 유지되며, 연결이 확인되면 저장을 이어갑니다.':error.message;
      connectMaterial.hidden=!needsConnection;materialError.hidden=false;materialError.scrollIntoView({block:'nearest'});
    }finally{button.disabled=false;button.textContent='교재 연결하기';}
  });
  async function openSlides(material){
    const sequence=++slideSequence;
    if(pdfViewerCleanup){pdfViewerCleanup();pdfViewerCleanup=null;}
    const note=$('#slide-note');note.textContent=material.note||'';note.hidden=!material.note;
    $('#slide-title').textContent=material.title;$('#slide-subject').textContent=material.subject;const stage=$('#slide-stage'),tools=$('#slide-tools');stage.replaceChildren(empty('교재를 준비하고 있어요'));tools.replaceChildren();$('#slide-dialog').showModal();setAgentState('materials','working','선택한 교재를 열고 있어요.');
    if(slideBlob){URL.revokeObjectURL(slideBlob);slideBlob=null;}
    try{
      if(['local_file','firestore_file'].includes(material.source_type)){
        const headers={};const token=sessionStorage.getItem('academy_access_key');if(token)headers.Authorization=`Bearer ${token}`;
        const response=await fetch(apiBase()+'/api/materials/'+encodeURIComponent(material.id)+'/file',{headers});if(!response.ok){let message='교재 파일을 열 수 없습니다. 서비스 연결을 확인해 주세요.';try{message=(await response.json()).detail||message;}catch{}throw new Error(message);}
        const blob=await response.blob();if(sequence!==slideSequence)return;
        slideBlob=URL.createObjectURL(blob);stage.replaceChildren();
        const download=element('a','button primary',material.kind==='pdf'?'PDF 다운로드':'원본 파일 다운로드');download.href=slideBlob;download.download=material.file_name;tools.append(download);
        if(material.kind==='pdf'){
          const {mountPdf}=await import('./pdf-viewer.js');
          const cleanup=await mountPdf(blob,stage,material.title,()=>sequence===slideSequence);
          if(sequence!==slideSequence){cleanup();return;}
          pdfViewerCleanup=cleanup;
        }else stage.append(empty('PowerPoint 원본이 준비되었습니다','아래 버튼으로 내려받아 PowerPoint에서 열어보세요.'));
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
  $('#slide-dialog').addEventListener('close',()=>{slideSequence++;if(pdfViewerCleanup){pdfViewerCleanup();pdfViewerCleanup=null;}$('#slide-stage').replaceChildren();if(slideBlob){URL.revokeObjectURL(slideBlob);slideBlob=null;}});
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
