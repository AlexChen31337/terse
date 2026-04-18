# Encrypted Backup Info

## Encryption Method
- Algorithm: AES-256-CBC with PBKDF2
- Tool: OpenSSL

## Encrypt command
```bash
openssl enc -aes-256-cbc -salt -pbkdf2 -in <file> -out <file>.enc -pass "pass:$(cat /home/bowen/clawd/memory/encrypted/.key)"
```

## Decrypt command
```bash
openssl enc -aes-256-cbc -d -salt -pbkdf2 -in <file>.enc -out <file> -pass "pass:$(cat /home/bowen/clawd/memory/encrypted/.key)"
```

## Sensitive files list
- hl-private-key.txt
- twitter-api-credentials.json
- moltbook-credentials.json
- discord-credentials.json
- gmail-credentials.json
- twitter-credentials.txt
- github-token.txt
- reddit-credentials.json
- twitter-bird-credentials.txt
- clawhub-token.txt
- github-config.json
- clawchain-bot-github.txt
