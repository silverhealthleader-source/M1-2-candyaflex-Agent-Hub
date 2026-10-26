import {next, ipAddress} from '@vercel/functions';
import {createSiteGate} from './gate.mjs';

export default createSiteGate({next, getIp: ipAddress});
