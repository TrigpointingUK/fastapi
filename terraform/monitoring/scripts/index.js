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
