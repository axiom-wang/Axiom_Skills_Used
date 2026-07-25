# Phase 3: 验证产出

## 目标

确认生成的 SKILL 目录完整、一致、可被下游 AI 正确使用。

## 检查清单

### 3.1 文件完整性

确认以下文件全部存在：

```
□ SKILL.md（带 name + description frontmatter）
□ tasks/01-generate-code.md
□ tasks/02-verify.md
□ reference/CONTEXT.md
□ reference/ 中至少有 1 个参考文件
□ rules/architecture.md
□ rules/design-system.md
□ prompt-template.md（带变量说明 + 提示词 + 使用说明）
□ prompts/ 中有 3 个即用型提示词文件（变量已填充，风格有差异）
```

### 3.2 内部引用一致性

- SKILL.md 中提到的所有文件路径在目录中实际存在
- tasks/ 中的"下一步"指引正确
- rules/architecture.md 中的组件列表与 reference/ 中的文件对应
- CONTEXT.md 中的数据类型与 rules/architecture.md 一致

### 3.3 Reference 大小检查

```bash
# 统计 reference/ 总行数
find <output_path>/reference -name "*.md" -o -name "*.tsx" -o -name "*.ts" -o -name "*.css" | xargs wc -l
```

- 总行数 ≤ 2000 行：通过
- 总行数 > 2000 行：需要按大小管理策略裁剪

### 3.4 SKILL 可用性检查

模拟下游 AI 的视角，验证：

1. **能否从 SKILL.md 理解要做什么？**
   - 概述是否清晰
   - 执行流程是否明确
   - 参数表是否完整

2. **能否从 tasks/01-generate-code.md 知道怎么做？**
   - 是否包含布局合约代码块（精确 JSX + Tailwind 类名）
   - 是否有 per-page block spec（每个页面的内容块排列）
   - 是否有页面完整性声明（所有页面文件名列表 + "缺一不可"约束）
   - 对首页/Dashboard 类页面，是否明确了每个区块"直接渲染"而非跳转
   - 对含子导航的页面（Settings 等），是否描述了其内部 tab 切换结构
   - 生成顺序是否合理
   - 自检清单是否包含：布局验证 + 页面完整性 + 首页内容验证

3. **能否从 reference/ 学到模式？**
   - CONTEXT.md 是否涵盖了功能、风格、数据结构
   - 参考代码是否展示了足够的模式（不需要全量，但需要覆盖各类文件类型）
   - 被裁剪的文件是否有补偿（tasks/01 中增加了对应的内容块规格，或 CONTEXT.md 中有详细描述）

4. **能否从 rules/ 知道边界？**
   - architecture.md 是否包含布局骨架代码块（不是文字描述，是实际 JSX）
   - 组件职责表中的描述是否精确到渲染形式（无模糊词）
   - 什么能改、什么不能改是否清晰
   - 设计推断规则是否有逻辑依据

### 3.5 Prompt Template 检查

验证 prompt-template.md：
- 变量表中的变量名与 SKILL.md 参数表一致
- 提示词中的 `{{变量}}` 都在变量表中有对应说明
- 系统指令是否涵盖了架构骨架声明、生成范围、关键约束
- 使用说明是否面向非技术用户（无需理解 SKILL 概念）
- 变体提示是否提供了有意义的调整方向（不是泛泛的"你可以改"）
- 提示词整体长度合理（不超过 500 字，太长用户不愿读；关键信息不能遗漏）

### 3.6 Description 触发检查

验证 SKILL.md 的 frontmatter description：
- 是否涵盖了用户可能的触发短语
- 是否说明了做什么和什么时候用
- 是否足够"推送"以确保被正确触发

### 3.7 结构保真度检查

验证产出的 SKILL 是否能防止三类常见质量回归：

**布局偏移防护**：
- tasks/01 中是否包含一段可复制粘贴的 App.tsx JSX 结构代码？
- 该代码是否带有精确的 Tailwind 类名（而非文字描述如"固定宽度侧边栏"）？
- 是否有明确的"禁止"清单（如"不允许将 Sidebar 改为顶部导航"）？

**页面遗漏防护**：
- tasks/01 中是否有一个完整的页面文件名清单？
- 非核心页面（如 Settings）是否有内部结构描述，足以防止被跳过？
- 路由结构表和页面清单是否数量一致？

**内容降级防护**：
- 首页/Dashboard 的每个区块是否明确标注了"直接渲染内容"？
- 是否有语句明确禁止"用链接/按钮替代实际图表"？
- 组件职责表中的渲染形式描述是否具体（折线图、柱状图、桑基图 vs "分析图表"）？

## 常见问题修复

| 问题 | 修复方式 |
|------|---------|
| reference/ 太大 | 删除重复模式的文件，保留代表性的 |
| architecture.md 约束太紧 | 检查是否把应该自由的部分也锁住了 |
| design-system.md 推断规则太少 | 至少覆盖 5 种配色 + 3 种排版组合 |

## 完成

SKILL 生成完毕，目录已就绪。告知用户输出路径和使用方式。
