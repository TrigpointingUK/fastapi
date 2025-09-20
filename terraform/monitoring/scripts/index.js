exports.handler = async () => {
  const targetUrl = process.env.TARGET_URL;
  const expectedEnv = process.env.EXPECTED_ENVIRONMENT;
  const ua = process.env.USER_AGENT || "Trigpointing-canary/1.0 (+https://trigpointing.uk)";

  const res = await fetch(targetUrl, { headers: { "User-Agent": ua } });
  const body = await res.json();

  if (res.status !== 200) {
    throw new Error(`HTTP ${res.status} fetching ${targetUrl}`);
  }
  if (!body || body.status !== "healthy") {
    throw new Error(`Health not healthy: ${JSON.stringify(body)}`);
  }
  const env = body.tracing && body.tracing.environment;
  if (env !== expectedEnv) {
    throw new Error(`Environment mismatch: got ${env}, expected ${expectedEnv}`);
  }
  return { ok: true };
};

"use strict";

const synthetics = require('Synthetics');
const log = require('SyntheticsLogger');

exports.handler = async () => {
  const targetUrl = process.env.TARGET_URL;
  const expected = process.env.EXPECTED_SUBSTRING;
  const resp = await synthetics.executeHttpStep('fetch', targetUrl, {
    method: 'GET',
    headers: { 'accept': 'application/json,text/html' },
    timeout: 30000
  });
  const body = resp.body.toString();
  log.info(`Status: ${resp.statusCode}`);
  if (resp.statusCode < 200 || resp.statusCode >= 400) {
    throw new Error(`Bad status ${resp.statusCode}`);
  }
  if (!body.includes(expected)) {
    throw new Error('Expected substring not found');
  }
};
