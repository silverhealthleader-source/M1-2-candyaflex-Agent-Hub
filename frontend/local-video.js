// Local File/Blob playback only. This module never uploads or persists video bytes.
export const LOCAL_VIDEOS = {
  'attirang-brand-film': {title:'카페 아띠랑 브랜드 필름', description:'이 PC에 보관한 브랜드 필름 MP4를 선택해 주세요.'},
  'attirang-10s-ad': {title:'카페 아띠랑 10초 광고', description:'이 PC에 보관한 10초 광고 MP4를 선택해 주세요.'},
  'attirang-logo-song': {title:'아띠랑 로고송', description:'이 PC에 보관한 로고송 MP4를 선택해 주세요.'}
};

export async function validateLocalMp4(file) {
  if (!file || !/\.mp4$/i.test(file.name || '') || !Number.isFinite(file.size) || file.size < 16) {
    throw new Error('PC에 보관한 MP4 영상 파일을 선택해 주세요.');
  }
  const header = new Uint8Array(await file.slice(0,12).arrayBuffer());
  const size = new DataView(header.buffer,header.byteOffset,header.byteLength).getUint32(0);
  if (String.fromCharCode(...header.slice(4,8)) !== 'ftyp' || size < 16 || size > Math.min(file.size,1024*1024)) {
    throw new Error('MP4 형식을 확인할 수 없습니다. 원본 영상 파일을 선택해 주세요.');
  }
  return file;
}

export function createLocalVideoLibrary(urls = URL) {
  const files = new Map();
  let activeUrl = null;
  const release = () => {if(activeUrl){urls.revokeObjectURL(activeUrl);activeUrl=null;}};
  return {
    async connect(id,file) {
      if(!Object.hasOwn(LOCAL_VIDEOS,id))throw new Error('등록된 영상 버튼을 선택해 주세요.');
      await validateLocalMp4(file);
      files.set(id,file);
    },
    has: id => files.has(id),
    source(id) {
      release();
      const file=files.get(id);
      if(!file)return null;
      activeUrl=urls.createObjectURL(file);
      return {file,url:activeUrl};
    },
    release
  };
}

function mountLocalVideoPlayer(doc) {
  const library=createLocalVideoLibrary();
  const node=(tag,className,text)=>{const el=doc.createElement(tag);if(className)el.className=className;if(text!==undefined)el.textContent=text;return el;};
  const dialog=node('dialog','local-video-dialog');
  dialog.id='local-video-dialog';
  dialog.setAttribute('aria-labelledby','local-video-title');
  const heading=node('div','local-video-heading');
  const title=node('h2');title.id='local-video-title';
  const close=node('button','local-video-close','×');close.type='button';close.setAttribute('aria-label','영상 닫기');
  heading.append(title,close);
  const privacy=node('p','local-video-privacy','영상은 이 PC에서만 재생됩니다. 선택한 파일은 서버로 전송되지 않습니다.');
  const guidance=node('p','local-video-guidance');
  const fileName=node('p','local-video-filename');
  const stage=node('div','local-video-stage');
  const video=node('video','local-video-element');video.controls=true;video.playsInline=true;video.preload='metadata';video.hidden=true;
  const empty=node('p','local-video-empty','아래 버튼으로 이 PC의 MP4 파일을 선택하세요.');
  stage.append(video,empty);
  const status=node('p','local-video-status');status.setAttribute('role','status');
  const input=node('input');input.type='file';input.accept='.mp4,video/mp4';input.hidden=true;
  const actions=node('div','local-video-actions');
  const choose=node('button','btn btn-primary','PC에서 영상 선택');choose.type='button';
  const done=node('button','btn btn-gold','닫기');done.type='button';
  actions.append(choose,done);
  const hint=node('p','local-video-hint','선택한 파일은 이 탭을 사용하는 동안 연결됩니다. 새로고침하거나 다른 기기에서 열면 다시 선택해 주세요.');
  dialog.append(heading,privacy,guidance,fileName,stage,status,actions,hint,input);
  doc.body.append(dialog);
  let activeId=null,sequence=0;
  function stop(){
    video.pause();video.onerror=null;video.removeAttribute('src');video.load();
    video.hidden=true;library.release();
  }
  async function show(id) {
    stop();
    const source=library.source(id);
    if(!source)return;
    empty.hidden=true;video.hidden=false;video.src=source.url;video.setAttribute('aria-label',LOCAL_VIDEOS[id].title);
    fileName.textContent=source.file.name;
    choose.textContent='다른 MP4 파일 선택';
    status.textContent='영상을 준비했습니다. 재생 버튼으로 감상하세요.';
    video.onerror=()=>{status.textContent='이 영상을 재생하지 못했습니다. 브라우저가 지원하는 MP4 파일인지 확인해 주세요.';};
    try{await video.play();}catch{/* Native controls remain available if the browser requires another gesture. */}
  }
  doc.addEventListener('click',event=>{
    const button=event.target.closest?.('[data-local-video]');
    if(!button)return;
    const id=button.dataset.localVideo;
    if(!Object.hasOwn(LOCAL_VIDEOS,id))return;
    sequence++;activeId=id;title.textContent=LOCAL_VIDEOS[id].title;guidance.textContent=LOCAL_VIDEOS[id].description;
    stop();fileName.textContent='';status.textContent='';empty.hidden=false;choose.textContent='PC에서 영상 선택';
    if(!dialog.open)dialog.showModal();
    if(library.has(id))show(id);
  });
  choose.onclick=()=>{input.value='';input.click();};
  input.onchange=async()=>{
    const file=input.files?.[0],id=activeId,current=sequence;
    if(!file||!id)return;
    status.textContent='선택한 파일을 확인하고 있어요.';
    try{
      await library.connect(id,file);
      if(current===sequence&&dialog.open)await show(id);
    }catch(error){if(current===sequence)status.textContent=error.message;}
  };
  close.onclick=done.onclick=()=>dialog.close();
  dialog.addEventListener('close',()=>{sequence++;stop();activeId=null;});
  window.addEventListener('pagehide',stop);
}

if (typeof document !== 'undefined') mountLocalVideoPlayer(document);

