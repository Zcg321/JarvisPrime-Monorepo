#!/usr/bin/env node
import { chromium } from 'playwright';

async function readStdin() {
  return new Promise((resolve) => {
    let data = '';
    process.stdin.on('data', (chunk) => (data += chunk));
    process.stdin.on('end', () => resolve(data));
  });
}

async function main() {
  if (!process.env.FALLBACK_UI_BOT) {
    console.error('fallback disabled');
    process.exit(1);
  }
  const card = await readStdin();
  const browser = await chromium.launch();
  const page = await browser.newPage();
  // selectors must be provided via env for safety
  const url = process.env.UI_BOT_URL || 'https://example.com';
  await page.goto(url);
  const result = { summary: 'ui bot stub', files: [], commands: [], next_suggestion: '' };
  console.log(JSON.stringify(result));
  await browser.close();
}

main();
