/**
 * Reddit Post Script
 * Posts to Reddit using authenticated browser session
 */

import { chromium } from 'playwright';
import * as fs from 'fs';
import * as path from 'path';

interface PostConfig {
  subreddit: string;
  title: string;
  content: string;
  isLink?: boolean;
  url?: string;
}

async function postToReddit(config: PostConfig) {
  // Load credentials
  const credPath = path.join(process.env.HOME!, 'clawd/memory/reddit-credentials.json');
  const creds = JSON.parse(fs.readFileSync(credPath, 'utf8'));
  
  const browser = await chromium.launch({ 
    headless: false,
    args: ['--start-maximized']
  });
  
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  
  // Inject session cookie
  await context.addCookies([
    {
      name: 'reddit_session',
      value: creds.reddit_session,
      domain: '.reddit.com',
      path: '/',
      httpOnly: true,
      secure: true,
      sameSite: 'None'
    }
  ]);
  
  const page = await context.newPage();
  
  console.log(`📝 Posting to r/${config.subreddit}...`);
  
  // Go to submit page
  const submitUrl = `https://www.reddit.com/r/${config.subreddit}/submit`;
  await page.goto(submitUrl);
  await page.waitForTimeout(3000);
  
  // Check if logged in
  const isLoggedIn = await page.locator('button:has-text("Create Post")').count() > 0 
                  || await page.locator('[placeholder="Title"]').count() > 0;
  
  if (!isLoggedIn) {
    console.error('❌ Not logged in! Cookie may have expired.');
    await page.waitForTimeout(60000); // Keep open for manual login
    await browser.close();
    return;
  }
  
  console.log('✅ Logged in as', creds.username);
  
  // Select post type
  if (config.isLink && config.url) {
    console.log('🔗 Creating link post...');
    await page.click('button:has-text("Link")').catch(() => {});
    await page.waitForTimeout(1000);
    
    if (await page.locator('[name="url"]').count() > 0) {
      await page.fill('[name="url"]', config.url);
    }
  } else {
    console.log('📄 Creating text post...');
    await page.click('button:has-text("Post")').catch(() => {});
    await page.waitForTimeout(1000);
  }
  
  // Fill title
  console.log('📝 Title:', config.title);
  await page.fill('[placeholder="Title"]', config.title);
  await page.waitForTimeout(500);
  
  // Fill content (for text posts)
  if (!config.isLink && config.content) {
    console.log('📝 Content:', config.content.substring(0, 100) + '...');
    const textArea = page.locator('[placeholder="Text (optional)"]').first();
    if (await textArea.count() > 0) {
      await textArea.fill(config.content);
    }
  }
  
  await page.waitForTimeout(1000);
  
  console.log('\n⏸️  Review the post and click "Post" when ready');
  console.log('   Or press Ctrl+C to cancel');
  
  // Keep browser open for review/posting
  await page.waitForTimeout(300000); // 5 minutes
  
  await browser.close();
  console.log('✅ Done!');
}

// CLI interface
const args = process.argv.slice(2);
if (args.length < 3) {
  console.log('Usage: npx tsx reddit-post.ts <subreddit> <title> <content> [--link <url>]');
  console.log('\nExample:');
  console.log('  npx tsx reddit-post.ts cryptocurrency "ClawChain: AI-Native Blockchain" "Full description here"');
  console.log('  npx tsx reddit-post.ts programming "My Project" "Check it out" --link https://github.com/user/repo');
  process.exit(1);
}

const subreddit = args[0];
const title = args[1];
const content = args[2];
const linkIndex = args.indexOf('--link');
const isLink = linkIndex !== -1;
const url = isLink ? args[linkIndex + 1] : undefined;

postToReddit({ subreddit, title, content, isLink, url }).catch(console.error);
