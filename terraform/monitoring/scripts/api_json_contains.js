"use strict";

const synthetics = require('Synthetics');
const log = require('SyntheticsLogger');

exports.handler = async () => {
  const url = process.env.TARGET_URL;
  const expected = process.env.EXPECTED_SUBSTRING;

  const page = await synthetics.getPage();
  await page.setUserAgent('Trigpointing-canary/1.0 (+https://trigpointing.uk)');
  const response = await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
  if (!response) {
    await synthetics.takeScreenshot('no_response', 'No response from target');
    throw new Error('No response from target');
  }
  const status = response.status();
  const headers = response.headers();
  if (status < 200 || status >= 400) {
    const text = await response.text().catch(() => "");
    log.info(`status=${status}`);
    log.info(`headers=${JSON.stringify(headers, null, 2).substring(0, 1000)}`);
    log.info(`body=${text.substring(0, 500)}`);
    await synthetics.takeScreenshot('bad_status', `HTTP ${status}`);
    throw new Error(`Bad status ${status}`);
  }
  const body = await response.text();
  if (!body.includes(expected)) {
    log.info(body.substring(0, 500));
    await synthetics.takeScreenshot('missing_expected', 'Expected substring not found');
    throw new Error('Expected substring not found');
  }
};
