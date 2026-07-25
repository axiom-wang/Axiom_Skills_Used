# Phase 1: 分析模版

## 目标

读取模版源码（和可选的对话历史），产出五份内部文档：技术栈报告、产品定义、架构约束、逐文件定制化标注、可定制点清单。这五份文档是 Phase 2 生成 SKILL 文件的输入。

## 执行步骤

### 1.1 读取文件结构和技术栈

列出模版目录（排除 node_modules、.git、lock 文件、`__pycache__`）。

**基础技术栈（所有模版固定，无需识别）**：

- 前端：Vite + React + TypeScript + Tailwind CSS + shadcn/ui
- 后端（如有）：FastAPI + SQLAlchemy + Alembic + Pydantic

**需要识别的是业务额外依赖**：

从 `package.json` 的 dependencies 和 `requirements.txt` / `pyproject.toml` 中，找出基础栈之外的库。例如：

- 图表库（recharts、chart.js）
- 动画库（framer-motion、react-spring）
- 状态管理（zustand、jotai）
- 表单（react-hook-form、zod）
- 日期处理（date-fns、dayjs）
- 后端额外库（celery、redis、boto3）

产出：前后端除模版依赖外的业务额外依赖列表。

### 1.2 识别业务文件

目的：从模版源码中筛出**业务文件**——这些是需要提取到产出 SKILL 的 reference/ 中的文件。

**快速过滤规则——以下是骨架，直接跳过**：

- 构建配置：`vite.config.*`、`tsconfig.json`、`tailwind.config.*`、`package.json`
- 平台基础设施：`main.tsx`、`lib/config.ts`、`lib/api.ts`、`lib/utils.ts`
- UI 组件库：`components/ui/*`
- 平台页面：`pages/AuthCallback.tsx`、`pages/AuthError.tsx`、`pages/blog/`
- 后端骨架：`main.py`、`core/config.py`、`core/enums.py`、`tests/conftest.py`、`alembic/`

**业务文件（提取目标）**：

前端：

- `pages/*`（除 Auth\* 和 blog/） → 业务页面
- 非 `ui/` 下的 `components/*` → 业务组件
- `data/*` / `store/*` / `context/*` → 数据和状态
- `hooks/*` → 自定义 hooks
- `index.css` 中的 CSS 变量部分 → 主题定义
- `pages/Index.tsx` → 模版中的占位页，看它被替换成了什么

后端：

- `routers/*.py` → API 路由
- `models/*.py` → 数据库模型
- `schemas/*.py` → Pydantic 请求/响应模型
- `services/*.py` → 业务逻辑
- `middlewares/*.py` → 自定义中间件
- `dependencies/*.py` → 依赖注入

**需要了解但不提取的骨架机制**：

- App.tsx 中的 MODULE markers（`MODULE_IMPORTS_START/END`、`MODULE_ROUTES_START/END`、`MODULE_PROVIDERS_START/END`）——这是平台 AI 注入业务代码的位置，产出 SKILL 的 architecture.md 需要说明这个机制
- 后端 `routers/` 的自动发现注册——同上

#### 业务文件编码模式分组

对业务文件按"编码模式"分组标记，供 Phase 2 决定 reference/ 保留哪些代表：

| 模式类型      | 典型特征                                   |
| ------------- | ------------------------------------------ |
| 纯展示组件    | 只接收 props，无内部状态，纯 Tailwind 渲染 |
| 带状态组件    | 有 useState/useReducer，含交互逻辑         |
| Context/Store | 定义全局状态，提供 Provider                |
| 数据文件      | 纯数据数组/对象，含 type 定义              |
| 页面文件      | 组装多个组件，含路由级逻辑                 |
| 样式文件      | CSS 变量、全局样式                         |
| API 路由      | FastAPI router，含 CRUD 端点               |
| 数据模型      | SQLAlchemy model + Pydantic schema         |
| 服务层        | 业务逻辑函数，被 router 调用               |

同一模式类型内，标记复杂度最高的文件为"代表"。

产出三个清单：骨架文件列表 + 业务文件列表 + 业务文件模式分组表。

### 1.3 提炼产品定义

从对话历史 JSON 中提炼产品定义：

对话历史格式来自 atoms.dev（MGXEnv JSON）。

#### JSON 结构概览

```
{
  "success": true,
  "data": {
    "roles": {
      "Mike": { ... },       // Team Leader
      "Emma": { ... },       // Product Manager
      "Bob": { ... },        // Architect
      "Alex": { ... },       // Engineer ← 主要读这个
      "David": { ... },      // Data Analyst
      "Sarah": { ... }       // SEO Specialist
    },
    "history": {             // 用户视角的对话（精简版）
      "storage": [...]
    }
  }
}
```

#### 核心数据路径

- **Alex 的完整对话**：`data.roles.Alex.rc.memory.storage[]` — 包含所有开发细节
- **用户视角对话**：`data.history.storage[]` — 精简版，用于快速了解需求轮次

#### 每条消息的结构

```json
{
  "role": "user" | "assistant",
  "cause_by": "metagpt.actions.add_requirement.UserRequirement" | "metagpt.actions.di.run_command.RunCommand",
  "content": "消息内容（含工具调用 XML）",
  "sent_from": "" | "Alex",
  "send_to": ["Alex", "<all>"]
}
```

#### 消息分类与提取价值

按 `role` + `cause_by` + `content` 关键词分类，提取不同信息：

| 筛选条件                                                        | 消息类型   | 提取什么                       |
| --------------------------------------------------------------- | ---------- | ------------------------------ |
| `role=user` + `cause_by=UserRequirement`                        | 用户需求   | 功能清单、用户画像、设计偏好   |
| `role=assistant` + content 含 `<FrontendEngineer.draft_plan>`   | 功能规划   | 任务分解、实现思路             |
| `role=assistant` + content 含 `<FrontendEngineer.use_template>` | 模版初始化 | scene 参数 → 确认模版类型      |
| `role=assistant` + content 含 `<Editor.write>`                  | 代码创建   | 最终源码（但优先从文件系统读） |
| `role=assistant` + content 含 `<ImageCreator.generate_images>`  | 图片生成   | 图片描述清单（品类、风格）     |

#### 可忽略的消息（噪音）

- `role=user` + `cause_by=RunCommand` + content 以 `Command Editor.read executed:` 开头 → 只是读取结果
- `role=assistant` + content 只有 `<Editor.read>` → 只是读取命令
- `role=user` + content 以 `Command Terminal.run executed:` 开头且无错误 → 正常执行结果
- `role=assistant` + content 以 `Command ... executed: SUCCESS` 开头 → 任务完成确认

#### 提取流程

1. **定位 Alex 的 storage**：`data.roles.Alex.rc.memory.storage`
2. **筛选用户需求消息**（`role=user` + `cause_by=UserRequirement`）→ 按时间顺序理解功能演进
3. **筛选 draft_plan 消息** → 提取 AI 理解的功能规划
4. **筛选 use_template 消息** → 确认 scene 参数
5. **从用户消息风格归纳用户画像**（语言、需求颗粒度、技术水平）

**核心原则**：回答"这个网站最终做成了什么？"而不是"用户怎么一步步要求的？"

### 1.4 确定架构约束

从业务代码中提取**业务层面的骨架**——这些是下游 AI 生成不同风格产物时都必须保持的结构。平台机制（MODULE markers、自动路由注册等）不属于这里的范畴，它们永远不变，不需要当约束提。

**前端业务骨架**：

- **页面布局合约（最高优先级）**：
  - 从 App.tsx 提取精确的 flex/grid 嵌套结构和 Tailwind 类名
  - 用 ASCII 图表示布局拓扑（含具体 CSS 数值如 w-64、h-16）
  - 从 Sidebar/Navbar/Layout 组件中提取关键类名
  - 产出：一段可直接粘贴到产出 SKILL 的 architecture.md 中的布局骨架代码
- **各页面的内容块结构**：
  - 对每个页面，识别其内部内容块的排列方式（grid-cols-X、并排区域、堆叠区域）
  - 对首页/Dashboard 类页面，精确记录每个区块包含什么组件、什么数据、是直接渲染还是跳转链接
  - 对含子导航的页面（如 Settings），记录其 tab/菜单 + 面板切换结构
  - 产出：per-page block spec，供 Phase 2 写入 tasks/01
- **业务路由表**：当前有哪些业务路由、对应哪些页面
- **状态管理接口**：Context / Store 的公共方法签名——组件间的数据流约定
- **核心数据类型**：被多个组件共享的 interface/type
- **组件职责划分**：每个业务组件的名称 + 职责 + props 接口。注意：
  - 职责描述要精确到"渲染什么类型的内容"，而不是模糊的"展示分析"
  - 对于复合组件（包含多个子区块），要列出其内部组成
- **Provider 层级**：Provider 的嵌套顺序（决定哪些组件能访问哪些状态）

**后端业务骨架**（如果模版含后端业务代码）：

- **分层结构**：router → service → model 的调用关系和职责边界
- **数据模型**：SQLAlchemy model + Pydantic schema 的对应关系
- **共享约定**：认证方式、错误响应格式、分页协议等跨路由的统一模式

**自由创作空间**（不属于骨架，下游 AI 可以完全重新设计）：视觉设计（配色/字体/图片）、文案内容、产品数据、交互动效、API 业务逻辑。

### 1.5 逐文件定制化标注

**前提**：已完成 §1.3（产品定义）和 §1.4（架构约束）。

**目标**：对每个业务文件产出精确的"可定制标注"（内部文档，供 Phase 2 写入产出 SKILL）。标注为 🎨 的部分可以改，未标注的部分默认保留原样。

#### 步骤

**Step 1：理解每个文件的角色**

结合 §1.3 的功能清单，理解每个业务文件在整体中的角色：
- 这个文件实现什么功能？
- 属于哪个页面/模块？
- 跟哪些文件配合？

**Step 2：按文件类型应用分层标注策略**

| 文件类型 | 标注策略 | 原因 |
|---------|---------|------|
| **UI 文件**（pages/\*、components/\*） | 逐块标注可改点（颜色类、文案字符串、可整块替换的区块），未标注部分 = 不可动 | 布局偏移的主战场，需要最高精度 |
| **数据文件**（data/\*） | 整体标记"保持 interface 结构，内容按新领域重写" | 不同领域内容完全不同，没法逐行保留 |
| **逻辑文件**（context/\*、hooks/\*） | 分情况：通用逻辑标记"📋 照搬模式"；领域特定逻辑标记"🎨 可定制" | 有些逻辑跨领域通用（加减数量、筛选排序），有些不是 |

**Step 3：对每个业务文件，只标注「可定制的部分」**

标注粒度灵活——从原子（单个颜色类、一行文案）到区块（整个图表组件可替换）。

#### 产出格式与质量要求

见 `rules/output-spec/reference.md` 中 STRUCTURE_MAP.md 的格式规范、标注策略和质量要求。

### 1.6 识别可定制点

从 §1.5 的逐文件标注中汇总可定制点清单——决定生成的 SKILL 告诉下游 AI "哪些部分可以根据用户提示词替换/重新设计"。

**核心理解**：用户选这个模版是因为认可它的布局和结构，但希望内容、风格、数据能根据不同业务需求定制。可定制点 = 在保持布局骨架不变的前提下，可以自由替换的部分。

**从源码中识别可定制维度**：

| 代码位置 | 可定制内容 |
|---------|-----------|
| `:root` CSS 变量 | 配色方案（主色/背景色/强调色） |
| `data/*.ts` 数据文件 | 产品/内容数据结构和内容 |
| 组件内的硬编码文案 | 标题、描述、CTA、标签 |
| 分类/筛选数组 | 分类体系和维度 |
| 图片引用 | 视觉素材 |

**识别方法**：

1. 找 CSS 变量定义 → 提取可替换的视觉维度
2. 找数据文件（`data/*.ts`）→ 提取数据结构和可替换的内容维度
3. 找硬编码的文案/分类 → 标记为可定制
4. 找组件 props 中的内容型字段 → 这些是用户可以通过提示词影响的

**产出格式**：

```markdown
## 可定制点清单

| 可定制点 | 维度 | 当前值 | 定制方式 |
|---------|------|--------|---------|
| 配色方案 | 视觉 | <从 CSS 变量中提取> | 替换 :root CSS 变量 |
| 核心数据 | 内容 | <从数据文件中提取> | 按 interface 结构生成新数据 |
| 分类体系 | 内容 | <从分类数组中提取> | 修改 categories 数组 |
| 品牌文案 | 内容 | <从组件中提取> | 替换硬编码字符串 |
```

### 1.7 设计风格推断规则

根据模版的业务类型（参考 `references/domain-knowledge.md` 中的"设计推断侧重"），设计"用户描述 → 设计决策"的映射：

- **配色推断**：品牌定位关键词 → 配色基调（列 5-7 种典型映射）
- **排版推断**：定位 → 字号/字重/间距体系（列 3-4 种）
- **数据推断**：业务类型 → 价格范围/分类体系/品牌风格
- **辅助推断**：受众 → 分类维度、语言 → 货币

## 产出

内存中的五份文档：

1. 技术栈报告（技术栈 + 文件分类 + 构建命令）
2. 产品定义（功能清单 + 视觉风格 + 数据结构 + 用户画像）
3. 架构约束（固定骨架 + 自由空间 + 推断规则）
4. 逐文件定制化标注（每个业务文件的 🎨 可定制标注，将写入产出 SKILL 的 `reference/STRUCTURE_MAP.md`）
5. 可定制点清单（从标注中汇总的维度 + 当前值 + 定制方式）

## 用户确认（必须）

Phase 1 完成后，**必须**将分析结果展示给用户确认，再进入 Phase 2。

展示格式：

```markdown
## 模版分析结果

### 技术栈

- 框架/构建/语言/CSS/UI 库/包管理器

### 识别的领域

- 主领域 + 辅助领域（如有）

### 功能清单

- 逐条列出从源码/对话中提炼的功能

### 骨架 vs 业务文件

- 骨架文件数 / 业务文件数
- 关键业务文件列表

### 可定制点（Top 5）

- 最重要的 5 个可定制点及当前值

---

以上分析是否准确？有需要补充或修正的吗？确认后我将开始生成 SKILL 文件。
```

用户确认（或修正后确认）后，再执行 Phase 2。

## 下一步

→ `02-generate.md`
