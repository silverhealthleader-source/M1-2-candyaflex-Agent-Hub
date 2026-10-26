// Mozilla PDF.js renders one page at a time, including browsers without a PDF plug-in.
const pdfjsPromise=import('./assets/vendor/pdfjs/pdf.min.mjs');

export async function mountPdf(blob,stage,title,isCurrent){
  const pdfjs=await pdfjsPromise;
  pdfjs.GlobalWorkerOptions.workerSrc=new URL('./assets/vendor/pdfjs/pdf.worker.min.mjs',import.meta.url).href;
  if(!isCurrent())return ()=>{};
  const reader=document.createElement('div');reader.className='pdf-reader';
  const toolbar=document.createElement('div');toolbar.className='pdf-reader-toolbar';toolbar.setAttribute('aria-label','PDF 페이지 이동');
  const previous=document.createElement('button');previous.type='button';previous.className='button secondary';previous.textContent='← 이전';
  const next=document.createElement('button');next.type='button';next.className='button secondary';next.textContent='다음 →';
  const label=document.createElement('label');label.textContent='쪽 ';
  const pageInput=document.createElement('input');pageInput.type='number';pageInput.min='1';pageInput.value='1';pageInput.setAttribute('aria-label','PDF 페이지 번호');
  const count=document.createElement('span');count.textContent=' / …';label.append(pageInput,count);
  const go=document.createElement('button');go.type='button';go.className='button secondary';go.textContent='이동';
  const status=document.createElement('span');status.className='pdf-reader-status';status.setAttribute('role','status');status.textContent='PDF를 준비하고 있어요.';
  const canvas=document.createElement('canvas');canvas.className='pdf-reader-canvas';canvas.setAttribute('role','img');
  toolbar.append(previous,label,go,next);reader.append(toolbar,status,canvas);stage.replaceChildren(reader);
  previous.disabled=next.disabled=pageInput.disabled=go.disabled=true;
  const task=pdfjs.getDocument({data:new Uint8Array(await blob.arrayBuffer()),isEvalSupported:false});
  let pdf,renderTask,disposed=false,current=1;
  const cleanup=()=>{disposed=true;renderTask?.cancel();task.destroy().catch(()=>{});};
  async function showPage(number){
    if(disposed||!isCurrent())return;
    previous.disabled=next.disabled=pageInput.disabled=go.disabled=true;status.textContent='페이지를 불러오고 있어요.';
    try{
      const page=await pdf.getPage(number);
      if(disposed||!isCurrent())return;
      const base=page.getViewport({scale:1});
      const viewport=page.getViewport({scale:Math.min(2,1600/base.width)});
      canvas.width=Math.ceil(viewport.width);canvas.height=Math.ceil(viewport.height);
      renderTask=page.render({canvasContext:canvas.getContext('2d'),viewport});
      await renderTask.promise;
      if(disposed||!isCurrent())return;
      current=number;pageInput.value=String(number);
      canvas.setAttribute('aria-label',`${title} · ${number} / ${pdf.numPages}쪽`);
      status.textContent=`${number} / ${pdf.numPages}쪽`;
    }catch(error){if(!disposed&&isCurrent())status.textContent='페이지를 표시하지 못했습니다. PDF 다운로드로 열어 주세요.';}
    finally{if(!disposed&&isCurrent()){previous.disabled=current===1;next.disabled=current===pdf.numPages;pageInput.disabled=go.disabled=false;}}
  }
  try{
    pdf=await task.promise;
    if(!isCurrent()){cleanup();return ()=>{};}
    pageInput.max=String(pdf.numPages);count.textContent=` / ${pdf.numPages}`;
    previous.onclick=()=>showPage(current-1);next.onclick=()=>showPage(current+1);
    go.onclick=()=>{const n=Number(pageInput.value);if(Number.isInteger(n)&&n>=1&&n<=pdf.numPages)showPage(n);else pageInput.value=String(current);};
    pageInput.onkeydown=event=>{if(event.key==='Enter'){event.preventDefault();go.click();}};
    await showPage(1);
    return cleanup;
  }catch(error){cleanup();throw error;}
}
