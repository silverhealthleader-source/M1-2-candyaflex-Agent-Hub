import test from 'node:test';
import assert from 'node:assert/strict';
import {createSiteGate, safeReturnPath} from '../access/gate.mjs';
import {readFileSync} from 'node:fs';
import deployedGate from '../access/proxy.js';

test('Vercel accepts the entrypoint extension and the real server module blocks anonymous access',async()=>{
  const deployment=JSON.parse(readFileSync(new URL('../vercel.json',import.meta.url),'utf8'));
  assert.match(deployment.proxy.entrypoint,/\.(js|ts|py)$/);
  assert.equal(typeof deployedGate,'function');
  assert.equal((await deployedGate(new Request('https://site.example/app.js'))).status,401);
});

// Synthetic test secret only; production code comes solely from Vercel settings.
const synthetic = 'unit-test-only-passphrase';
function setup() {
  let clock = 1800000000000, code = synthetic;
  const gate = createSiteGate({getCode:()=>code, now:()=>clock, getIp:()=> 'test-client', next:()=>new Response('downstream',{headers:{'x-middleware-next':'1'}})});
  const request = (path, options={}) => new Request('https://site.example' + path, options);
  const login = (value=synthetic, returnTo='/education', extra={}) => gate(request('/_access/login',{
    method:'POST',headers:{Origin:'https://site.example','Content-Type':'application/x-www-form-urlencoded',...extra},
    body:new URLSearchParams({code:value,returnTo})}));
  return {gate,request,login,advance:milliseconds=>clock+=milliseconds,setCode:value=>code=value};
}

test('all entry routes and static assets require authentication, including spoofed middleware headers',async()=>{
  const {gate,request}=setup();
  for(const path of ['/','/education','/education.html','/assets/logo.png','/config.js','/app.js','/access/gate.mjs']) {
    const response=await gate(request(path,{headers:{'x-middleware-subrequest':'middleware:middleware:middleware'}}));
    assert.equal(response.status,path.split('/').pop().includes('.')?401:302);
    assert.equal(response.headers.get('Cache-Control'),'private, no-store, max-age=0');
    assert.ok(!(await response.text()).includes('downstream'));
  }
});
test('unset and short codes fail closed and are never included in the page',async()=>{
  const {gate,request,setCode,login}=setup();
  for(const code of ['', '123']) {
    setCode(code);assert.equal((await gate(request('/_access'))).status,503);
    assert.equal((await login()).status,503);assert.equal((await gate(request('/'))).status,302);
  }
});
test('correct code creates a signed HttpOnly secure host cookie and restores only local destinations',async()=>{
  const {gate,request,login}=setup();const response=await login();
  assert.equal(response.status,303);assert.equal(response.headers.get('Location'),'/education');
  const cookie=response.headers.get('Set-Cookie');
  for(const flag of ['__Host-candyaflex_site=','Path=/','HttpOnly','Secure','SameSite=Strict'])assert.ok(cookie.includes(flag));
  assert.ok(!cookie.includes(synthetic));assert.ok(!(await response.text()).includes(synthetic));
  const allowed=await gate(request('/app.js',{headers:{Cookie:cookie.split(';')[0]}}));
  assert.equal(allowed.headers.get('x-middleware-next'),'1');
  assert.equal(allowed.headers.get('Vary'),'Cookie');
});
test('incorrect codes, forged cookies, expiry, changed codes and cross-host replay are rejected',async()=>{
  const {gate,request,login,advance,setCode}=setup();assert.equal((await login('wrong-code')).status,401);
  const response=await login();const cookie=response.headers.get('Set-Cookie').split(';')[0];
  for(const value of ['__Host-candyaflex_site=true',cookie.slice(0,-1)+'!'])assert.equal((await gate(request('/',{headers:{Cookie:value}}))).status,302);
  const other=await gate(new Request('https://other.example/',{headers:{Cookie:cookie}}));assert.equal(other.status,302);
  advance(8*3600*1000);assert.equal((await gate(request('/',{headers:{Cookie:cookie}}))).status,302);
  advance(-8*3600*1000);setCode('another-unit-test-passphrase');assert.equal((await gate(request('/',{headers:{Cookie:cookie}}))).status,302);
});
test('login/logout reject cross-origin and non-POST requests; logout expires cookie',async()=>{
  const {gate,request,login}=setup();assert.equal((await login(synthetic,'/',{Origin:'https://elsewhere.example'})).status,403);
  assert.equal((await login(synthetic,'/',{Origin:'null'})).status,403);
  for(const path of ['/_access/login','/_access/logout'])assert.equal((await gate(request(path))).status,405);
  const response=await gate(request('/_access/logout',{method:'POST',headers:{Origin:'https://site.example'}}));
  assert.equal(response.status,303);assert.ok(response.headers.get('Set-Cookie').includes('Max-Age=0'));
});
test('login document preserves same-origin browser form Origin without exposing cross-site referrers',async()=>{
  const {gate,request}=setup();
  const response=await gate(request('/_access'));
  assert.equal(response.headers.get('Referrer-Policy'),'same-origin');
  assert.ok((await response.text()).includes('method="post" action="/_access/login"'));
});
test('redirects and HTML cannot be injected through returnTo',async()=>{
  const {gate,request,login}=setup();
  for(const path of ['https://evil.example','//evil.example','/\\evil.example','/_access/logout','/\r\nLocation: bad'])assert.equal(safeReturnPath(path),'/');
  assert.equal((await login(synthetic,'//evil.example')).headers.get('Location'),'/');
  const body=await (await gate(request('/_access?returnTo='+encodeURIComponent('/"><script>alert(1)</script>')))).text();
  assert.ok(!body.includes('<script>'));assert.ok(!body.includes(synthetic));
});
test('oversized bodies and unsupported content types are rejected',async()=>{
  const {gate,request}=setup();
  assert.equal((await gate(request('/_access/login',{method:'POST',headers:{Origin:'https://site.example','Content-Type':'application/json'},body:'{}'}))).status,400);
  assert.equal((await gate(request('/_access/login',{method:'POST',headers:{Origin:'https://site.example','Content-Type':'application/x-www-form-urlencoded'},body:'code='+ 'x'.repeat(5000)}))).status,413);
});
test('repeated failures are throttled within a process and recover after the window',async()=>{
  const {login,advance}=setup();for(let i=0;i<15;i++)assert.equal((await login('incorrect')).status,401);
  assert.equal((await login()).status,429);advance(10*60*1000+1);assert.equal((await login()).status,303);
});
