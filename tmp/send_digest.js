const path = require('path');
require('dotenv').config({ path: path.resolve('/home/bowen/.openclaw/workspace/skills/imap-smtp-email/.env') });
const nodemailer = require('nodemailer');
const fs = require('fs');

async function main() {
  const transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST,
    port: parseInt(process.env.SMTP_PORT) || 587,
    secure: process.env.SMTP_SECURE === 'true',
    auth: { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS },
    tls: { rejectUnauthorized: process.env.SMTP_REJECT_UNAUTHORIZED !== 'false' }
  });

  await transporter.verify();
  console.log('SMTP connected');

  const htmlContent = fs.readFileSync('/tmp/daily_ideas_20260426.html', 'utf8');
  
  const info = await transporter.sendMail({
    from: process.env.SMTP_FROM || process.env.SMTP_USER,
    to: 'bowen31337@outlook.com',
    subject: 'Alex Daily Ideas - Sun Apr 26',
    html: htmlContent
  });

  console.log('Sent:', info.messageId);
  console.log('Response:', info.response);
}

main().catch(err => { console.error('Error:', err.message); process.exit(1); });
