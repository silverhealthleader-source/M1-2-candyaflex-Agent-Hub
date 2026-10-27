import test from 'node:test';
import assert from 'node:assert/strict';
import {LOCAL_VIDEOS,validateLocalMp4,createLocalVideoLibrary} from '../local-video.js';

function video(name='clip.mp4',tail='video'){
  const header=new Uint8Array(24);new DataView(header.buffer).setUint32(0,24);
  header.set(new TextEncoder().encode('ftypisom'),4);
  return new File([header,tail],name,{type:'video/mp4'});
}

test('local playback accepts real MP4 signatures and Korean or accented filenames',async()=>{
  for(const name of ['카페 아띠랑 10초 영상.mp4','Brand_film_for_Café_Attirant.mp4']){
    const file=video(name);assert.equal(await validateLocalMp4(file),file);
  }
});

test('local file validation rejects renamed documents, short files and invalid box sizes',async()=>{
  for(const file of [video('clip.html'),new File(['not a video at all'],'fake.mp4'),new File(['x'],'short.mp4')]){
    await assert.rejects(validateLocalMp4(file));
  }
  const invalid=video();const bytes=new Uint8Array(await invalid.arrayBuffer());new DataView(bytes.buffer).setUint32(0,2**32-1);
  await assert.rejects(validateLocalMp4(new File([bytes],'invalid.mp4')));
});

test('a large local logo song needs only its header for validation',async()=>{
  let reads=0;const sample=video();
  const large={name:'로고송.mp4',size:54*1024*1024,slice(start,end){reads++;assert.equal(start,0);assert.equal(end,12);return sample.slice(start,end);}};
  assert.equal(await validateLocalMp4(large),large);assert.equal(reads,1);
});

test('each video button retains its own local file and releases temporary URLs on switch or close',async()=>{
  const created=[],revoked=[];
  const library=createLocalVideoLibrary({createObjectURL(file){created.push(file);return 'blob:local-'+created.length;},revokeObjectURL(url){revoked.push(url);}});
  const first=video('brand.mp4','brand'),second=video('advertisement.mp4','ad');
  await library.connect('attirang-brand-film',first);await library.connect('attirang-10s-ad',second);
  assert.equal(library.source('attirang-brand-film').file,first);
  assert.equal(library.source('attirang-10s-ad').file,second);
  assert.deepEqual(revoked,['blob:local-1']);
  library.release();library.release();assert.deepEqual(revoked,['blob:local-1','blob:local-2']);
  assert.ok(library.has('attirang-brand-film'));
  assert.equal(library.source('attirang-brand-film').file,first);
  library.release();
});

test('only registered local video IDs can be connected',async()=>{
  const library=createLocalVideoLibrary();
  await assert.rejects(library.connect('unknown-video',video()));
  assert.equal(library.source('attirang-brand-film'),null);
  assert.equal(Object.keys(LOCAL_VIDEOS).length,3);
});

