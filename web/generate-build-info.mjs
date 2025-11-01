#!/usr/bin/env node

/**
 * Generate build information for the web app.
 * Called during the build process to capture commit SHA, timestamp, etc.
 */

import { execSync } from 'child_process';
import { writeFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

function getGitCommitSha() {
  try {
    return execSync('git rev-parse HEAD').toString().trim();
  } catch {
    return 'unknown';
  }
}

function getGitCommitShort() {
  try {
    return execSync('git rev-parse --short HEAD').toString().trim();
  } catch {
    return 'unknown';
  }
}

function getGitBranch() {
  try {
    return execSync('git rev-parse --abbrev-ref HEAD').toString().trim();
  } catch {
    return 'unknown';
  }
}

function getGitCommitMessage() {
  try {
    return execSync('git log -1 --pretty=%B').toString().trim();
  } catch {
    return 'unknown';
  }
}

const buildInfo = {
  version: process.env.npm_package_version || '0.1.0',
  commitSha: getGitCommitSha(),
  commitShort: getGitCommitShort(),
  branch: getGitBranch(),
  commitMessage: getGitCommitMessage(),
  buildTime: new Date().toISOString(),
  nodeVersion: process.version,
  // GitHub Actions specific
  githubRun: process.env.GITHUB_RUN_ID || null,
  githubRunNumber: process.env.GITHUB_RUN_NUMBER || null,
  githubActor: process.env.GITHUB_ACTOR || null,
  githubWorkflow: process.env.GITHUB_WORKFLOW || null,
  githubRef: process.env.GITHUB_REF || null,
  environment: process.env.VITE_ENVIRONMENT || 'development',
};

const outputPath = join(__dirname, 'public', 'buildInfo.json');
writeFileSync(outputPath, JSON.stringify(buildInfo, null, 2));

console.log('✅ Build info generated:', outputPath);
console.log(JSON.stringify(buildInfo, null, 2));

