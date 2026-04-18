#!/usr/bin/env node
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });
const nodemailer = require('nodemailer');
const fs = require('fs');

async function main() {
  const htmlPath = process.argv[2];
  const toEmail = process.argv[3] || 'bowen31337@outlook.com';
  const subject = process.argv[4] || 'Alex Daily Ideas';

  if (!htmlPath || !fs.existsSync(htmlPath)) {
    console.error('Usage: node send_daily.js <html-file> [to-email] [subject]');
    console.error('HTML file not found:', htmlPath);
    process.exit(1);
  }

  const transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST,
    port: parseInt(process.env.SMTP_PORT) || 587,
    secure: process.env.SMTP_SECURE === 'true',
    auth: { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS },
    tls: { rejectUnauthorized: process.env.SMTP_REJECT_UNAUTHORIZED !== 'false' },
  });

  await transporter.verify();
  console.log('SMTP verified');

  const html = fs.readFileSync(htmlPath, 'utf8');
  const info = await transporter.sendMail({
    from: process.env.SMTP_FROM || process.env.SMTP_USER,
    to: toEmail,
    subject: subject,
    html: html,
  });

  console.log('Sent! MessageId:', info.messageId);
  console.log('Response:', info.response);
}

main().catch(err => { console.error('FAILED:', err.message); process.exit(1); });
