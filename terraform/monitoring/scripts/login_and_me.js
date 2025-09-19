"use strict";

const synthetics = require('Synthetics');
const https = require('https');

async function httpPostForm(url, form) {
  const body = new URLSearchParams(form).toString();
  const { hostname, pathname, protocol } = new URL(url);
  return new Promise((resolve, reject) => {
    const ua = process.env.USER_AGENT || 'Trigpointing-canary/1.0 (+https://trigpointing.uk)';
    const req = https.request({
      hostname,
      path: pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'accept': 'application/json',
        'Content-Length': Buffer.byteLength(body),
        'User-Agent': ua
      },
      timeout: 30000
    }, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve({ statusCode: res.statusCode, body: data }));
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

async function httpGet(url, headers) {
  const { hostname, pathname } = new URL(url);
  return new Promise((resolve, reject) => {
    const ua = process.env.USER_AGENT || 'Trigpointing-canary/1.0 (+https://trigpointing.uk)';
    const req = https.request({ hostname, path: pathname, method: 'GET', headers: { ...headers, 'User-Agent': ua }, timeout: 30000 }, res => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => resolve({ statusCode: res.statusCode, body: data }));
    });
    req.on('error', reject);
    req.end();
  });
}

exports.handler = async () => {
  const username = process.env.USERNAME;
  const password = process.env.PASSWORD;
  const legacyUserId = process.env.LEGACY_USER_ID;
  const loginUrl = process.env.LOGIN_URL;
  const meUrl = process.env.ME_URL;

  const loginResp = await httpPostForm(loginUrl, {
    grant_type: 'password', username, password
  });
  if (loginResp.statusCode < 200 || loginResp.statusCode >= 400) {
    console.log(`login status=${loginResp.statusCode}`);
    console.log(`login body=${(loginResp.body || '').substring(0, 500)}`);
    throw new Error(`Login failed ${loginResp.statusCode}`);
  }
  const token = JSON.parse(loginResp.body).access_token;
  if (!token) throw new Error('No access_token');

  const meResp = await httpGet(meUrl, { 'Authorization': `Bearer ${token}`, 'accept': 'application/json' });
  if (meResp.statusCode < 200 || meResp.statusCode >= 400) {
    console.log(`me status=${meResp.statusCode}`);
    console.log(`me body=${(meResp.body || '').substring(0, 500)}`);
    throw new Error(`Me failed ${meResp.statusCode}`);
  }
  const raw = meResp.body || '';
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (e) {
    console.log(`me invalid JSON, body=${raw.substring(0, 500)}`);
    throw new Error('Invalid JSON from /user/me');
  }
  const expectedId = String(legacyUserId).trim();
  const gotId = parsed && parsed.id !== undefined ? String(parsed.id) : '';
  if (gotId !== expectedId) {
    console.log(`expected id=${expectedId}, got id=${gotId}`);
    console.log(`me body=${raw.substring(0, 500)}`);
    throw new Error('legacy_userid mismatch in /user/me');
  }
};
