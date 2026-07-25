# atoms.dev 平台工作流

> 最后验证日期：2026-06-14。平台更新后需重新核实骨架文件列表和工具 API。

skill_generator_skill 生成的 SKILL 最终运行在 atoms.dev 平台上。本文件记录平台的工作模式，供生成 SKILL 时参考。

## 平台架构

```
/workspace/
├── .atoms/
│   ├── ATOMS.md          # 项目上下文（Overview + Constraints）
│   ├── PROGRESS.md       # 任务进度跟踪
│   └── skills/           # 已安装的 SKILL 目录
│       └── <skill-name>/
│           └── SKILL.md
└── app/
    └── frontend/         # use_template 初始化的前端项目
        ├── README.md     # 模版使用说明
        ├── package.json
        ├── vite.config.ts
        ├── tailwind.config.ts
        ├── tsconfig.json
        ├── index.html    # 不可修改（使用环境变量占位符）
        └── src/
            ├── main.tsx
            ├── App.tsx           # Router shell
            ├── index.css         # CSS 变量 + Tailwind 配置
            ├── components/ui/    # shadcn 组件（预装，不可修改）
            ├── lib/utils.ts      # cn() 工具函数
            └── pages/Index.tsx   # 默认首页占位（必须替换）
```

## 角色系统

atoms.dev 使用多角色协作：
- **Mike** (Team Leader)：分配任务、协调
- **Emma** (Product Manager)：需求分析、PRD
- **Bob** (Architect)：系统设计
- **Alex** (Engineer)：前端开发（SKILL 的主要执行者）
- **David** (Data Analyst)：数据相关
- **Sarah** (SEO Specialist)：SEO 内容

SKILL 的 frontmatter 中可以指定 `roles: [Alex]` 来限定谁读取。

## 平台工具

Alex（Engineer）可用的工具：

| 工具 | 用途 | 调用格式 |
|------|------|---------|
| `FrontendEngineer.draft_plan` | 提交开发计划给用户确认 | `<content>计划内容</content>` |
| `FrontendEngineer.use_template` | 初始化项目模版 | `<scene>frontend</scene>` |
| `Editor.write` | 创建新文件 | `<path>路径</path><content>内容</content>` |
| `Editor.edit_file_by_replace` | 编辑已有文件 | `<file_name>路径</file_name><to_replace>旧</to_replace><new_content>新</new_content>` |
| `Editor.read` | 读取文件 | `<path>路径</path>` |
| `Terminal.run` | 执行命令 | `<cmd>命令</cmd>` |
| `CheckUI.run` | UI 视觉验证 | `<instruction>验证描述</instruction>` |
| `ImageCreator.generate_images` | 生成图片资源 | `<images>[{description, filename, style?, size?}]</images>` |
| `RoleZero.reply_to_human` | 回复用户 | `<content>消息</content>` |

## 标准工作流程

```
1. 用户提需求
2. Alex 调用 FrontendEngineer.draft_plan → 用户 APPROVE/UPDATE
3. Alex 调用 FrontendEngineer.use_template(scene: frontend) → 骨架项目就绪
4. Alex 读 README.md 了解模版结构
5. Alex 读 /workspace/.atoms/skills/ 下的 SKILL（如果有的话）
6. Alex 更新 ATOMS.md（记录项目 Overview + Constraints）
7. Alex 更新 PROGRESS.md（记录任务分解和状态）
8. Alex 用 Editor.write 逐个创建业务文件
9. Alex 用 Terminal.run 跑 lint + build
10. Alex 用 CheckUI.run 验证 UI
11. 如果有错误，修复后重复 9-10
12. Alex 用 RoleZero.reply_to_human 告知用户完成
```

## 模版骨架（use_template 后自动存在的文件）

以下文件由 `FrontendEngineer.use_template(scene: frontend)` 自动生成，**AI 不需要创建**：

- `index.html` — 不可修改
- `vite.config.ts` — 构建配置
- `tailwind.config.ts` — Tailwind 配置
- `tsconfig.json` — TypeScript 配置
- `package.json` — 依赖和脚本（预装了 shadcn、react-router-dom、lucide-react 等）
- `src/main.tsx` — 入口
- `src/App.tsx` — Router shell（默认只有 `/` 指向 Index.tsx）
- `src/index.css` — 基础样式（含 Tailwind directives + shadcn CSS 变量）
- `src/components/ui/*` — 全套 shadcn 组件
- `src/lib/utils.ts` — `cn()` 函数
- `src/pages/Index.tsx` — 默认占位页面（**必须替换为真实首页**）

## SKILL 在 atoms.dev 中的位置

SKILL 文件放在 `/workspace/.atoms/skills/<skill-name>/SKILL.md`。

Alex 在开发前会读取相关的 SKILL 来获取指引。所以我们生成的 SKILL 要：
1. 告诉 Alex 使用 `frontend` 场景的模版（骨架已存在）
2. 列出需要创建的业务文件（不是骨架文件）
3. 给出创作指引（参考 reference/、遵守 rules/）
4. 不要在 SKILL 里写 `<Editor.write>` 之类的工具调用——SKILL 描述"做什么"，Alex 自己知道用什么工具

## 对 SKILL 生成的影响

理解了这个工作流后，skill_generator_skill 生成的 SKILL 应该：

1. **不包含 init 步骤** — `use_template` 已经处理了
2. **明确声明使用 `frontend` scene** — 让 Alex 知道调用 `use_template(scene: frontend)`
3. **骨架文件列为"已存在"** — 不要让 AI 去创建 vite.config/tailwind.config 等
4. **业务文件是创作目标** — pages/、components/（非ui）、data/、context/、index.css 变量部分
5. **App.tsx 需要修改** — 添加路由（骨架文件中唯一需要改的）
6. **验证步骤用 Terminal.run + CheckUI.run** — 但 SKILL 只说"lint + build + UI 检查"，不写工具名
7. **图片资源用 ImageCreator** — SKILL 可以指引 AI 生成什么图片，但不写工具调用语法
