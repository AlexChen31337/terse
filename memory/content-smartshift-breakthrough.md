# SmartShift Breakthrough — Content Drafts

## English Version (dev.to / Substack / LinkedIn)

### Title: I Reverse-Engineered My Solar Inverter's API to Export 5kW to the Grid — Here's What I Found

**TL;DR:** Solplanet/AISWEI hybrid inverters have a hidden "Custom mode" (mod_r=4) that enables force grid export. The documented TOU mode (mod_r=5) is broken on current firmware. This took 12 hours of debugging to discover, and the fix is 3 lines of code.

---

Last week I installed a 46kWh battery system with a Solplanet ASW12kH-T3 hybrid inverter. The goal was simple: charge from solar during the day, export to the grid during peak pricing windows on Amber Electric, and pocket the difference.

The hardware was ready. The Amber API was feeding real-time spot prices. The automation was running every 5 minutes. Everything looked perfect — except the battery refused to export a single watt to the grid.

#### The Problem

Solplanet exposes a local HTTP API on the inverter's WiFi dongle (an ESP32). You can read battery state, solar production, and grid power. You can also write settings — battery work mode, charge/discharge limits, and TOU schedules.

The documentation (what little exists) says:
- `mod_r=2` → Self-consumption mode
- `mod_r=5` → Time-of-use mode (with schedule)

Self-consumption worked fine — the battery would discharge to cover home load. But it would never push power *to* the grid. That's the difference between saving $1-2/day and earning $6-7/night.

TOU mode accepted every setting I threw at it. The API returned `{"dat": "ok"}` for both `setbattery` and `setdefine` (the schedule endpoint). The schedule was correctly readable via `getdefine.cgi`. But the battery sat at 0W, stubbornly refusing to discharge.

#### What I Tried (and Failed)

Over 12 hours, I:

1. **Decoded the TOU schedule encoding** — reverse-engineered the slot format: `(hour << 24) | (half_hour << 17) | (duration << 14) | discharge_bit`. Slots were being written correctly.

2. **Cycled through every mode byte** — tried mode values 0-5 in the schedule slots. None triggered discharge.

3. **Tested self-consumption** — confirmed it discharges to cover home load (1499W), but never exports surplus.

4. **Scanned Modbus registers** — the ESP32 has a `fdbg.cgi` endpoint for raw Modbus RTU frames. Device 4 (battery) returned "Illegal Function" on all holding and input registers. Dead end.

5. **Checked the Solplanet cloud API** — read-only. No write endpoints at all.

6. **Nearly crashed the ESP32** — hammered it with too many API calls and it stopped responding for 10 minutes. Lesson: the dongle has very limited concurrent connection capacity.

#### The Breakthrough

At 9:30 PM, frustrated and running out of ideas, I found a small GitHub repository: [amber-solplanet](https://github.com/ilikedata/amber-solplanet) — "Optimise battery charge/discharge for Solplanet on Amber Electric."

Someone had already solved this exact problem. The answer was hiding in plain sight:

```python
SELF_CONSUMPTION_MODE = 2
CUSTOM_MODE = 4  # ← THIS IS THE KEY
```

**Custom mode** (`mod_r=4`), not TOU mode (`mod_r=5`).

The working sequence:
1. Write a discharge schedule slot via `setdefine` (the same API that TOU uses)
2. Set `mod_r=4` via `setbattery`
3. Watch the battery ramp from 0W → 1939W → **5045W** in 30 seconds

The documentation never mentions `mod_r=4` for this purpose. The HA Solplanet integration lists it as "Custom mode" but doesn't explain what it does. The Solplanet app doesn't expose it. It's essentially an undocumented forced-dispatch mode.

#### The Safety Trick

The amber-solplanet project uses a clever pattern: **backdated schedule slots**.

Instead of writing a slot for the current time (which might miss the start window), you write a slot that started 30 minutes ago with a 1-hour duration. This means:
- The slot is always "active" when written
- It naturally expires in ~30 minutes if the automation fails
- Stale commands don't persist — the inverter falls back to self-consumption

This is critical for safety. If your automation crashes at 2 AM, you don't want the battery to keep exporting until it's flat.

#### The Numbers

| Metric | Self-consumption only | With Custom mode export |
|--------|----------------------|------------------------|
| Battery discharge | 400-800W (home load) | **5045W (full power)** |
| Grid export | 0 kWh | ~40 kWh/night |
| Daily revenue | $1-2 (savings) | **$6-7 (export earnings)** |
| Annual value | ~$500 | **~$2,000-2,500** |

#### What You Need

If you have a Solplanet/AISWEI hybrid inverter with battery and Amber Electric (or any spot-price retailer):

1. Find your inverter's local IP (check your router's DHCP table)
2. API endpoints: `getdevdata.cgi`, `getdev.cgi`, `setting.cgi`, `getdefine.cgi`
3. Use `mod_r=4` (Custom mode) for force discharge
4. Use `mod_r=2` (Self-consumption) as your safe fallback
5. Write short-lived schedule slots that auto-expire
6. **Do NOT use `mod_r=5`** (TOU mode) — it's broken on current firmware

The full automation code is open source: [ha-smartshift](https://github.com/bowen31337/ha-smartshift)

#### Lessons Learned

1. **Documentation lies.** The API docs say TOU mode supports scheduled discharge. It doesn't — on this firmware, at least.
2. **Look for prior art.** Someone else had this exact problem and solved it months ago. A GitHub search saved me from the Modbus rabbit hole.
3. **ESP32 dongles are fragile.** One request every 5 seconds max. Don't scan Modbus registers in a tight loop or you'll brick the dongle for 10 minutes.
4. **Backdated slots are genius.** They solve the "stale command" problem elegantly — no cleanup needed, they just expire.
5. **Self-consumption mode is your friend** when you're debugging. It always works and never does anything dangerous.

---

*Tags: solar, battery, inverter, amber-electric, solplanet, aiswei, home-automation, python, api, reverse-engineering*

---

## Chinese Version (MbD / 面包多)

### 标题：我花了12小时逆向工程太阳能逆变器API，终于让电池以5kW向电网输出 —— 从亏钱到日赚50块的全过程

---

上周装了一套46度电的家用电池系统，配的是Solplanet ASW12kH-T3混合逆变器。目标很简单：白天用太阳能充电，晚上高峰时段把电卖回电网，赚差价。

听起来很美好对吧？硬件到位了，Amber Electric的实时电价API接好了，自动化脚本每5分钟跑一次。一切看起来完美——除了电池死活不往电网送电。

#### 问题出在哪

逆变器的WiFi模块（一个ESP32芯片）提供了本地HTTP API。你能读到电池状态、太阳能发电量、电网功率。也能写入设置——工作模式、充放电限制、分时调度。

文档里写的是：
- `mod_r=2` → 自用模式（Self-consumption）
- `mod_r=5` → 分时模式（TOU）

自用模式没问题——电池会放电来满足家里用电。但它**绝对不会**主动往电网送电。这就是每天省1-2块和每晚赚40-50块的区别。

分时模式呢？API返回成功，调度表写入正确，读回来也对。但电池就是0瓦，纹丝不动。

#### 12小时的折腾

我试了所有能试的：

1. **解码了调度表的编码格式** —— 位移、掩码、标志位，全手工逆向
2. **遍历了所有模式字节** —— 0到5全试了一遍
3. **扫描了Modbus寄存器** —— 通过ESP32的调试端口发送原始Modbus帧，结果电池控制器根本不响应
4. **查了云端API** —— 只读，没有写入接口
5. **差点把ESP32搞挂了** —— 请求太频繁，模块直接罢工10分钟

#### 转机

晚上9点半，我在GitHub上发现了一个小项目：[amber-solplanet](https://github.com/ilikedata/amber-solplanet)——有人已经解决了完全相同的问题。

答案藏在一个常量里：

```python
CUSTOM_MODE = 4  # ← 就是这个！
```

不是分时模式（mod_r=5），是**自定义模式**（mod_r=4）！

操作很简单：
1. 通过 `setdefine` 写入一个放电调度时间段
2. 把工作模式设成 `mod_r=4`
3. 看着电池30秒内从0瓦飙升到 **5045瓦**

文档里从没提到 mod_r=4 能这样用。App里也没有这个选项。这是一个**未公开的强制输出模式**。

#### 安全设计

这个方案有个巧妙的安全机制：**回溯调度时间段**。

写入的时间段起始时间是30分钟前，持续1小时。这意味着：
- 写入时一定在"活跃"窗口内
- 如果自动化程序崩了，时间段30分钟后自动过期
- 逆变器会安全回退到自用模式

不需要清理，不需要心跳检测，过期了就自动安全。

#### 实际收益

| 指标 | 仅自用模式 | 自定义模式强制输出 |
|------|-----------|-------------------|
| 电池放电功率 | 400-800W（仅供家用） | **5045W（全力输出电网）** |
| 每日电网输出 | 0度 | ~40度 |
| 每日收入 | 省8-15块 | **赚40-50块** |
| 年化收益 | ~3000块 | **~15000-18000块** |

（基于Amber Electric澳洲现货电价，高峰时段feed-in约14澳分/度）

#### 写在最后

1. **文档会骗人。** API说分时模式支持定时放电，但在当前固件上根本不工作。
2. **先搜GitHub。** 别人可能早就解决了你的问题，一个搜索能省你一天时间。
3. **ESP32很脆弱。** 请求间隔至少5秒，否则它会罢工。
4. **回溯时间段是天才设计。** 不需要清理机制，到期自动失效。

完整代码开源：[ha-smartshift](https://github.com/bowen31337/ha-smartshift)

---

*这是一篇纯技术实战文章。如果你也有Solplanet逆变器+储能电池，希望这能帮你少走弯路。*
