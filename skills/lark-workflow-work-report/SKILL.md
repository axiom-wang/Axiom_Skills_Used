---
name: lark-workflow-work-report
version: 1.0.0
description: "工作日报/周报生成工作流：并行拉取飞书日程、待办、私信、群聊@我、发出消息五类数据，AI 汇总生成结构化日报，并保存为本地 Markdown。当用户说「生成日报」「今天日报」「写日报」「生成周报」时触发。"
metadata:
  requires:
    bins: ["lark-cli"]
---

# 工作日报 / 周报生成工作流

**CRITICAL — 开始前 MUST 先用 Read 工具读取 [`../lark-shared/SKILL.md`](../lark-shared/SKILL.md)，其中包含认证、权限处理。**

## 适用场景

- "帮我生成今天的日报" / "写今天的工作日报"
- "重新生成日报" / "更新今天的日报"
- "生成本周周报" / "这周工作汇总"

---

## 用户配置（王炎专属）

生成前先用 Read 工具读取记忆文件，获取用户 open_id 等配置（如文件存在）：

```
/Users/wangyan/.claude/projects/-Users-wangyan/memory/user_profile.md
```

关键配置速查：

| 项目 | 值 |
|------|-----|
| 用户 open_id | `ou_d3d3bc98a3ec2ae9b0e9d1d645a22393` |
| 日报本地目录 | `D:\obsidian\default\Career\deepwisdom\日报` |
| 周报本地目录 | `D:\obsidian\default\Career\deepwisdom\周报` |

**本地保存原则**：

- 日报和周报只保存到本地 Markdown 文件。
- 不创建飞书 Wiki 节点。
- 不追加或更新飞书云文档。
- 不写入飞书 Base 统计表。
- 如果用户另行指定本地 Obsidian/iCloud 目录，以用户指定目录为准。

---

## 日报生成流程

### Step 1：确定日期与周次

```bash
# 获取今天日期
date +%Y-%m-%d

# 计算当周起止日（周日~周六，美式周）
python3 -c "
from datetime import date, timedelta
today = date.today()
offset = (today.weekday() + 1) % 7
sun = today - timedelta(days=offset)
sat = sun + timedelta(days=6)
print(f'{sun.strftime(\"%m/%d\")}-{sat.strftime(\"%m/%d\")}')
"
```

星期中文映射：Mon=星期一, Tue=星期二, Wed=星期三, Thu=星期四, Fri=星期五, Sat=星期六, Sun=星期日

### Step 2：并行拉取五类数据

以下五条命令**并行执行**（在同一条消息中发出所有 Bash 工具调用）：

```bash
# ① 日程
lark-cli calendar +agenda \
  --as user \
  --start "YYYY-MM-DDT00:00:00+08:00" \
  --end   "YYYY-MM-DDT23:59:59+08:00"

# ② 未完成待办
lark-cli task +get-my-tasks --as user

# ③ 当日私信（收到 + 发出）
lark-cli im +messages-search \
  --as user \
  --chat-type p2p \
  --start "YYYY-MM-DDT00:00:00+08:00" \
  --end   "YYYY-MM-DDT23:59:59+08:00"

# ④ 群聊@我
lark-cli im +messages-search \
  --as user \
  --is-at-me --chat-type group \
  --start "YYYY-MM-DDT00:00:00+08:00" \
  --end   "YYYY-MM-DDT23:59:59+08:00"

# ⑤ 我发出的消息
lark-cli im +messages-search \
  --as user \
  --sender ou_d3d3bc98a3ec2ae9b0e9d1d645a22393 \
  --start "YYYY-MM-DDT00:00:00+08:00" \
  --end   "YYYY-MM-DDT23:59:59+08:00"
```

> **注意**：`search:message` scope 需单独授权。若遇到 `missing required scope: search:message`，在后台以 background 模式运行 `lark-cli auth login --scope "search:message"`，取出授权链接发给用户。

### Step 3：AI 汇总

将五类数据整合成结构化日报，格式如下：

```markdown
# YYYY-MM-DD（星期X）

## 日程安排

| 时间 | 事件 | 组织者 | 状态 |
|------|------|--------|------|
| HH:mm-HH:mm | 事件名 | 姓名 | 已参加/待确认/已拒绝 |

## 【今日完成事项】

- 事项名称（进展：xx%，链接：xxx）
- 事项名称（进展：已完成，链接：内部讨论，无链接）

（从「我发出的消息」、私信和群聊中提炼当日实际推进的工作。每条必须包含进展百分比和产出链接；链接优先填 MR/PR、文档、设计稿等，没有外部链接填"内部讨论，无链接"。无实质进展则写"无"。）

## 【风险】

（当前遇到的阻塞或潜在风险，从群聊通知、讨论中识别；没有则写"无"）

## 【今日计划】

- 计划事项（预期产出：xxx）
- 计划事项

（根据「待办事项」、群聊中提到的后续行动、MR review 进展等推断明日/下一步计划）

## 【思考】

（今天的反思、洞察或改进想法；从讨论、技术决策、流程问题中提炼；没有则写"无"）

## 群聊重要通知

| 时间 | 发送人 | 群组 | 内容摘要 |
|------|--------|------|---------|
| HH:mm | 姓名 | 群名 | 一句话摘要 |

（仅收录 @我 或 @all 的有实质内容的通知，过滤系统机器人的重复提醒）

## 待办事项

- [ ] 任务名（截止：日期 或 无截止日期）

## 小结

- **会议**：N 场
- **核心产出**：① ... ；② ... ；③ ...
```

**数据处理规则：**

1. **时间转换**：Unix timestamp → `Asia/Shanghai` → `HH:mm`
2. **RSVP 映射**：`accept`→已参加，`decline`→已拒绝，`needs_action`→待确认，`tentative`→暂定
3. **消息去重**：`im +messages-search --sender` 和 `--chat-type p2p` 有重叠，合并展示私信对话
4. **待办过滤**：任务列表可能含大量历史条目，只展示近 30 天内创建或有截止日期的，其余折叠为"其他 N 项历史待办"
5. **通知过滤**：@all 且内容为操作提醒（canary 冻结、数据异常等）标注 ⚠️
6. **屏蔽群组**：以下群组的消息全部忽略，不纳入汇总：
   - 厦门办公网络问题反馈群
   - 自助添加MGX白名单
   - MGX用户反馈群
   - newapi 问题反馈群

### Step 4：本地保存日报

将 Step 3 的报告内容保存为本地 Markdown 文件。报告内容不要以 `---` 开头，避免后续复制到 CLI 参数时被误解析。

默认保存路径：

```text
D:\obsidian\default\Career\deepwisdom\日报\YYYY-MM-DD.md
```

PowerShell 示例：

```powershell
$reportDir = "D:\obsidian\default\Career\deepwisdom\日报"
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
Set-Content -Path (Join-Path $reportDir "YYYY-MM-DD.md") -Value $markdown -Encoding UTF8
```

---

## 周报生成流程

当用户要求「生成周报」时，从本地日报 Markdown 文件读取本周所有日报记录，生成汇总报告。

### Step 1：计算本周日期范围

周定义：**周日（第1天）→ 周六（第7天）**，与美式日历一致。

```bash
python3 -c "
from datetime import date, timedelta
today = date.today()
# weekday(): Mon=0 … Sun=6；Sun 对应偏移 0，Mon 对应偏移 1，…，Sat 对应偏移 6
offset = (today.weekday() + 1) % 7   # 距本周日的天数
sun = today - timedelta(days=offset)  # 本周日（第1天）
sat = sun + timedelta(days=6)         # 本周六（第7天）
print(f'{sun} to {sat}')
"
```

### Step 2：从本地读取本周日报记录

默认日报目录：

```text
D:\obsidian\default\Career\deepwisdom\日报
```

读取本周日期范围内存在的 `YYYY-MM-DD.md` 文件，按日期升序合并分析。缺失日期只在周报的数据源限制中注明，不从飞书 Base 或飞书云文档补取。

### Step 3：生成周报结构

```markdown
# YYYY-WXX 工作周报（MM/DD - MM/DD）

## 本周工作总结

（整合本周所有日报记录，按项目/功能线归类总结核心产出、关键进展、重要决策与通知、遗留风险或待办。优先写有结果、有影响、有链接的事项；没有链接时写"内部讨论，无链接"。）

- 项目/方向 A：...
- 项目/方向 B：...
- 其他重要事项：...

**本周小结**：N 场会议，N 项关键产出，N 项跨周待办。

## 下周计划

（根据当前进度、未完成待办、已知需求和讨论中的后续行动推断。按优先级列出可执行计划，并尽量说明预期产出。）

- 计划事项 1（预期产出：...）
- 计划事项 2（预期产出：...）
- 计划事项 3（预期产出：...）

## 上周的心得和思考 & 需要得到的资源或帮助 & 对团队和公司的建议

**心得和思考**：

（总结本周工作中的反思、洞察、流程改进想法或技术判断；没有则写"无"。）

**需要得到的资源或帮助**：

（列出推进下周计划所需的资源、权限、协作、评审或决策支持；没有则写"无"。）

**对团队和公司的建议**：

（提炼对团队协作、产品流程、工程效率、组织机制等方面的建议；没有则写"无"。）
```

### Step 4：本地保存周报

生成周报后，将完整 Markdown 内容保存到本地 Obsidian 周报目录：

默认保存路径：

```text
D:\obsidian\default\Career\deepwisdom\周报\YYYY-WXX 工作周报.md
```

文件命名规则：`YYYY-WXX 工作周报.md`，例如 `2026-W20 工作周报.md`。

---

## 权限速查

| 数据源 | 所需 scope |
|--------|-----------|
| 日程 | `calendar:calendar.event:read` |
| 待办 | `task:task:read` |
| 消息搜索 | `search:message` |
| 消息详情/资料解析 | `im:message.reactions:read`、`contact:user.basic_profile:readonly`（部分 `messages-search` 返回需要） |

---

## 参考

- [lark-shared](../lark-shared/SKILL.md) — 认证、权限（必读）
- [lark-workflow-standup-report](../lark-workflow-standup-report/SKILL.md) — 日程待办摘要（早报场景）
