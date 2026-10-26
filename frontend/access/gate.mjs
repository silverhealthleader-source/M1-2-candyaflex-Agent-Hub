import {createHash, createHmac, randomBytes, timingSafeEqual} from 'node:crypto';

const HOURS = 8;
const MAX_FAILURES = 15;
const WINDOW_MS = 10 * 60 * 1000;
const digest = value => createHash('sha256').update(value).digest();
const escape = value => String(value).replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));

export function safeReturnPath(value) {
  if (typeof value !== 'string' || value.length > 2048 || !value.startsWith('/') || value.startsWith('//') || /[\\\r\n\u0000-\u001f]/.test(value)) return '/';
  try {
    const parsed = new URL(value, 'https://local.invalid');
    if (parsed.origin !== 'https://local.invalid' || parsed.pathname.startsWith('/_access')) return '/';
    return parsed.pathname + parsed.search + parsed.hash;
  } catch { return '/'; }
}

function page(message, returnTo, configured, authenticated = false) {
  return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>접속 인증 · 캔디A플렉스</title><style>
*{box-sizing:border-box}body{margin:0;min-height:100svh;display:grid;place-items:center;padding:24px;background:radial-gradient(ellipse at top left,#d9f0ec,transparent 65%),linear-gradient(140deg,#f4f7fb,#e6eff4);color:#173d50;font-family:system-ui,"Malgun Gothic",sans-serif}main{width:min(100%,490px);background:#fff;border:1px solid #cbdce3;border-top:6px solid #3a8a8a;border-radius:24px;padding:38px 32px;box-shadow:0 20px 60px #173d5014}.brand{font-size:14px;font-weight:750;letter-spacing:.04em;color:#2b7883}h1{font-size:30px;line-height:1.35;margin:20px 0 14px}p{font-size:17px;line-height:1.7;margin:12px 0 26px;color:#526b7b}label{display:block;font-size:17px;font-weight:700;margin-bottom:10px}input{width:100%;font:inherit;font-size:20px;padding:15px;border:1px solid #8faeba;border-radius:12px;min-height:56px}input:focus{outline:3px solid #a9d6d8;outline-offset:2px}button{width:100%;border:0;border-radius:12px;background:#235a6c;color:#fff;font-size:19px;font-weight:700;min-height:56px;padding:15px;margin-top:20px;box-shadow:0 5px 0 #c5ac71;cursor:pointer}button:disabled{opacity:.5;cursor:not-allowed}.message{padding:14px;border-radius:10px;background:#fff4dc;color:#6b4d19;font-size:16px;line-height:1.6}.foot{font-size:14px;margin:25px 0 0;color:#667c86}.secondary{background:#eef3f5;color:#235a6c;box-shadow:none}a{color:#235a6c} @media(max-width:480px){main{padding:30px 23px}h1{font-size:27px}}
</style></head><body><main><div class="brand">CANDYAFLEX · PRIVATE ACCESS</div><h1>캔디A플렉스<br>접속 인증</h1><p>에듀 융합에이전트를 이용하려면<br>운영자가 알려드린 인증번호를 입력해 주세요.</p>${message ? `<div class="message" role="alert">${escape(message)}</div>` : ''}<form method="post" action="/_access/login"><input type="hidden" name="returnTo" value="${escape(returnTo)}"><label for="access-code">접속 인증번호</label><input id="access-code" name="code" type="password" autocomplete="current-password" minlength="8" maxlength="128" required ${configured ? '' : 'disabled'} aria-describedby="session-help"><button type="submit" ${configured ? '' : 'disabled'}>인증하고 입장하기</button></form>${authenticated ? `<form method="post" action="/_access/logout"><button class="secondary">접속 종료</button></form><p class="foot"><a href="${escape(returnTo)}">사이트로 돌아가기</a></p>` : ''}<p id="session-help" class="foot">이 브라우저에서 최대 ${HOURS}시간 동안 이용할 수 있습니다. 인증번호는 운영자에게 문의해 주세요.</p></main></body></html>`;
}

export function createSiteGate({next, getCode = () => process.env.SITE_ACCESS_CODE || '', getIp = () => 'unknown', now = Date.now} = {}) {
  // Best-effort per-instance throttle; not a distributed rate limiter.
  const failures = new Map();
  // no-referrer turns Origin into "null" for browser form POSTs. Keep Origin
  // for same-site form navigation while withholding referrers from other sites.
  const headers = {'Cache-Control':'private, no-store, max-age=0','CDN-Cache-Control':'no-store','Vercel-CDN-Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'same-origin','X-Frame-Options':'DENY','Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"};
  function html(message, path, configured, status = 200, authenticated = false) {
    return new Response(page(message, path, configured, authenticated), {status, headers:{...headers,'Content-Type':'text/html; charset=utf-8'}});
  }
  function redirect(location, status = 303, cookie) {
    return new Response(null,{status,headers:{...headers,Location:location,...(cookie ? {'Set-Cookie':cookie} : {})}});
  }
  function signature(code, payload) { return createHmac('sha256', digest(code)).update('candyaflex-site-v1.' + payload).digest('base64url'); }
  function validSession(cookie, code, origin) {
    const match = /^v1\.([A-Za-z0-9_-]{1,512})\.([A-Za-z0-9_-]{43})$/.exec(cookie || '');
    if (!match || !timingSafeEqual(digest(match[2]), digest(signature(code, match[1])))) return false;
    try {
      const data = JSON.parse(Buffer.from(match[1], 'base64url').toString('utf8'));
      const seconds = Math.floor(now() / 1000);
      return data.aud === origin && Number.isInteger(data.exp) && data.exp > seconds && data.exp <= seconds + HOURS * 3600;
    } catch { return false; }
  }
  return async function gate(request) {
    const url = new URL(request.url);
    const secure = url.protocol === 'https:';
    const cookieName = secure ? '__Host-candyaflex_site' : 'candyaflex_site_local';
    const code = getCode().trim();
    const configured = code.length >= 8 && code.length <= 128;
    const cookies = request.headers.get('cookie') || '';
    const cookie = cookies.split(';').map(part => part.trim()).find(part => part.startsWith(cookieName + '='))?.slice(cookieName.length + 1);
    const authenticated = configured && validSession(cookie, code, url.origin);
    const returnTo = safeReturnPath(url.searchParams.get('returnTo') || '/');
    if (url.pathname === '/_access' && ['GET','HEAD'].includes(request.method)) {
      return html(configured ? '' : '운영자의 인증번호 설정이 필요합니다. 잠시 후 다시 접속해 주세요.', returnTo, configured, configured ? 200 : 503, authenticated);
    }
    if (url.pathname === '/_access/logout' || url.pathname === '/_access/login') {
      if (request.method !== 'POST') return new Response('허용하지 않는 요청입니다.',{status:405,headers:{...headers,Allow:'POST'}});
      if (request.headers.get('origin') !== url.origin) return new Response('요청 출처를 확인해 주세요.',{status:403,headers});
      if (url.pathname.endsWith('/logout')) return redirect('/_access',303,`${cookieName}=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0${secure ? '; Secure' : ''}`);
      if (!configured) return html('운영자의 인증번호 설정이 필요합니다.', '/', false, 503);
      if (!(request.headers.get('content-type') || '').startsWith('application/x-www-form-urlencoded') || Number(request.headers.get('content-length') || 0) > 4096) return new Response('요청 형식을 확인해 주세요.',{status:400,headers});
      const body = await request.text();
      if (Buffer.byteLength(body) > 4096) return new Response('입력 길이를 확인해 주세요.',{status:413,headers});
      const form = new URLSearchParams(body);
      const target = safeReturnPath(form.get('returnTo') || '/');
      const clientKey = digest(getIp(request) || 'unknown').toString('hex');
      const current = failures.get(clientKey);
      if (current && now() - current.start < WINDOW_MS && current.count >= MAX_FAILURES) {
        const response = html('입력 시도가 많습니다. 10분 후 다시 시도해 주세요.',target,true,429);
        response.headers.set('Retry-After','600'); return response;
      }
      const supplied = (form.get('code') || '').trim();
      if (supplied.length > 128 || !timingSafeEqual(digest(supplied), digest(code))) {
        if (failures.size >= 1000) {
          for (const [key, value] of failures) if (now() - value.start >= WINDOW_MS) failures.delete(key);
          if (failures.size >= 1000) failures.delete(failures.keys().next().value);
        }
        failures.set(clientKey, current && now() - current.start < WINDOW_MS ? {...current,count:current.count + 1} : {start:now(),count:1});
        return html('인증번호가 맞지 않습니다. 다시 확인해 주세요.',target,true,401);
      }
      failures.delete(clientKey);
      const payload = Buffer.from(JSON.stringify({exp:Math.floor(now() / 1000) + HOURS * 3600,aud:url.origin,n:randomBytes(16).toString('base64url')})).toString('base64url');
      return redirect(target,303,`${cookieName}=v1.${payload}.${signature(code,payload)}; Path=/; HttpOnly; SameSite=Strict${secure ? '; Secure' : ''}`);
    }
    if (!authenticated) {
      const destination = '/_access?returnTo=' + encodeURIComponent(safeReturnPath(url.pathname + url.search));
      if (!url.pathname.split('/').pop().includes('.') || (request.headers.get('accept') || '').includes('text/html')) return redirect(destination,302);
      return new Response('접속 인증이 필요합니다.',{status:401,headers});
    }
    const response = next();
    for (const [key,value] of Object.entries(headers)) if (key !== 'Content-Security-Policy' && key !== 'X-Frame-Options') response.headers.set(key,value);
    response.headers.append('Vary','Cookie');
    return response;
  };
}
