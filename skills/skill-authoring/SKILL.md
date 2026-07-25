---
name: skill-authoring
description: Create or update Codex skills. Use when you need to scaffold a new skill, choose a skill name or registry location, write SKILL.md frontmatter/body, add optional scripts/references/assets, generate agents/openai.yaml, validate the skill folder, or install the skill via junctions.
---

# Skill Authoring

## 流程

1. 明确技能边界
   - 写清楚它要解决什么问题、触发词是什么、哪些情况不在范围内。
   - 保留 2-3 个真实示例，方便后续检查触发条件是否足够准确。

2. 选择名称和位置
   - 使用小写字母、数字和连字符。
   - 名称要短、明确、可触发，避免和现有 skill 重名。
   - 按 registry 分类存放：`codex/{agent,communication,writing,documentation}/` 或 `shared/{research,content,development,debugging,data-ml,agent-workflow,lark}/`.

3. 初始化 skill
   - 运行 `scripts/init_skill.py <skill-name> --path <registry-parent> [--resources scripts,references,assets]`
   - 只创建真正需要的资源目录，避免额外文件。

4. 编写 `SKILL.md`
   - frontmatter 只保留 `name` 和 `description`。
   - 把“什么时候用”写进 `description`，不要放到正文里。
   - 正文用祈使句，保持简短，优先写可执行步骤。
   - 长说明、表格、示例和参考资料放进 `references/`。

5. 补充元数据
   - 让 `agents/openai.yaml` 和 `SKILL.md` 保持一致。
   - 如有需要，再补 `scripts/`、`references/`、`assets/`。

6. 校验并安装
   - 运行 `scripts/quick_validate.py <skill-folder>` 检查 frontmatter 和命名规则。
   - 把 registry 里的 skill 通过 junction 挂到 `~/.codex/skills/` 或 `~/.claude/skills/`。

## 写作准则

- 只保留能帮助另一个 Codex 实际完成任务的信息。
- 避免 README、CHANGELOG、INSTALLATION_GUIDE 之类的附加文档。
- 说明要可执行、可验证、可复用。
