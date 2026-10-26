import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root = path.dirname(fileURLToPath(import.meta.url));
const out = path.join(root, 'dist');
fs.mkdirSync(out, {recursive: true});
// Also remove copies left in a reused output directory by an older build.
for (const name of ['presentation.html', 'presentation.css', 'presentation.js']) fs.rmSync(path.join(out, name), {force: true});
for (const name of ['index.html', 'education.html', 'styles.css', 'app.js', 'workspace.js', 'pdf-viewer.js', 'workspace.css', 'planning.css', 'branding.css', 'review.css', 'academy-design.css']) fs.copyFileSync(path.join(root, name), path.join(out, name));
fs.cpSync(path.join(root, 'assets'), path.join(out, 'assets'), {recursive:true});
const api = process.env.API_BASE_URL || '';
if (api && !/^https?:\/\//.test(api)) throw new Error('API_BASE_URL must start with http:// or https://');
fs.writeFileSync(path.join(out, 'config.js'), `window.ACADEMY_CONFIG = ${JSON.stringify({API_BASE_URL:api.replace(/\/$/, '')})};\n`);
console.log('Vanilla HTML/CSS/JS built in frontend/dist');
