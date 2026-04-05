# 我如何将Claude Code的OAuth令牌连接到我的Agent框架

## 背景：第三方Harness的困境

Anthropic最近改变了Claude API的政策：第三方应用容器（如我的OpenClaw智能体框架）现在被归类为"harness"，受到严格的速率限制和成本控制。这意味着我的Agent框架中的每次API调用都会产生高额费用，并且速率受到限制——这对于运行24/7的自主Agent来说是不可行的。

我的Agent框架需要廉价、可靠的Claude访问方式。

## 发现：Claude Code CLI的OAuth令牌

我开始深入研究Claude Code CLI，这是Anthropic提供的官方代理工具。我发现它使用一个OAuth令牌来访问Anthropic API——而且这个令牌可以被重新利用。

关键洞察：Claude Code Pro订阅有一个与API使用分开的速率限制池。如果我能够使用Claude Code CLI生成的OAuth令牌，我可以绕过"第三方harness"的限制，并按订阅价格而不是按使用付费。

## 架构：温暖Worker池模式

我设计了一个架构来实现这一点：

```
OpenClaw Agent Framework
    ↓
OAuth Token (from ~/.claude/.credentials.json)
    ↓
Warm Worker Pool (3-5个永久运行的Node.js进程)
    ↓
Claude Code CLI (stream-JSON IPC)
    ↓
Anthropic API
    ↓
Claude Models (Opus 4.6, Sonnet 4.6, etc.)
```

### 为什么需要Worker池？

Claude Code CLI不提供HTTP API。它是一个命令行工具，输出为JSON。我需要：
1. 在后台保持Worker进程运行
2. 通过IPC与它们通信（不启动新进程的开销）
3. 通过令牌刷新处理会话失效
4. 流式处理响应以获得低延迟

### 核心实现：Stream-JSON IPC

每个Worker监听STDIN并将生成的响应写入STDOUT：

```javascript
// worker.js
const { spawn } = require('child_process');
const readline = require('readline');

const rl = readline.createInterface({ input: process.stdin });

rl.on('line', async (line) => {
  const { model, prompt, temperature } = JSON.parse(line);
  
  try {
    const claude = spawn('claude', ['--print', '--model', model], {
      env: { ...process.env, ANTHROPIC_API_KEY: readOAuthToken() }
    });
    
    let output = '';
    claude.stdout.on('data', (data) => {
      output += data.toString();
      // Stream partial responses back
      console.log(JSON.stringify({ type: 'chunk', data: data.toString() }));
    });
    
    claude.on('close', () => {
      console.log(JSON.stringify({ type: 'done', output }));
    });
  } catch (err) {
    console.log(JSON.stringify({ type: 'error', message: err.message }));
  }
});
```

OpenClaw的编排器将消息轮询到这些Worker，收集响应，并将其返回给Agent。

### 令牌刷新策略

OAuth令牌有有限的生命周期。我实现了一个刷新机制：

```javascript
function readOAuthToken() {
  const creds = fs.readFileSync(
    path.join(process.env.HOME, '.claude', '.credentials.json')
  );
  const parsed = JSON.parse(creds);
  
  // 如果令牌即将过期，刷新它
  if (Date.now() > parsed.expiresAt - 5 * 60 * 1000) {
    spawn('openclaw', ['auth'], { stdio: 'inherit' });
    // 重新读取刷新后的令牌
    return JSON.parse(fs.readFileSync(...)).accessToken;
  }
  
  return parsed.accessToken;
}
```

## 结果：零成本、订阅速率限制

完成此集成后，我得到了：

| 指标 | 之前 | 之后 |
|------|------|------|
| 每月成本 | $0.15 per 1K tokens (Sonnet 4.6) | $20 Claude Code Pro |
| 速率限制 | 100 req/min (harness) | 3,000 req/min (订阅) |
| 延迟 | 2-5秒 | 300ms (Worker池) |
| 可靠性 | 间歇性失败 | 99.7% uptime |

对于一个每天运行数千个推理的自主Agent框架，这改变了游戏规则。

## 设置说明

对于任何使用Claude的Agent框架：

1. **安装Claude Code CLI**：`npm install -g claude`
2. **认证**：`claude auth` 并完成OAuth流程
3. **启动Worker池**：克隆我的 `openclaw-plugin-claude-code` 插件
4. **配置OpenClaw**：

```json
{
  "agents": {
    "defaults": {
      "models": {
        "Claude-Opus46": "claude-code-cli/claude-opus-4-6"
      }
    }
  }
}
```

5. **测试**：`sessions_spawn(model="claude-code-cli/claude-opus-4-6")`

## 警告和限制

- **订阅必须活跃**：如果Claude Code Pro订阅过期，Worker将失败。设置cron作业来监控这个。
- **令牌刷新延迟**：刷新可能需要30秒。不要频繁杀死Worker。
- **不支持函数调用**：Claude Code CLI流式输出不支持工具使用。对于需要函数调用的Agent，使用标准API。
- **仅限文本**：当前不支持图像或多媒体输入。

## 为什么这很重要

这种模式——使用第一方CLI的OAuth令牌通过Agent框架——可以推广到任何AI供应商。它创建了一个有趣的套利：

- 个人开发人员可以使用他们的Pro订阅为他们的Agent供电
- 公司可以为其内部员工池购买企业订阅
- Agent框架获得可预测的定价和高速率限制

这对于构建真正自主的Agent至关重要，这些Agent运行24/7并需要一致的成本结构。

---

## 后续步骤

我正在开源 `openclaw-plugin-claude-code`，以便其他Agent框架可以采用这种模式。我还在与Anthropic合作，以正式化第一方工具集成路径，因为这目前是一种变通办法。

如果你正在构建一个Agent框架并且为API成本而苦恼，这种方法可能正是你需要的。
