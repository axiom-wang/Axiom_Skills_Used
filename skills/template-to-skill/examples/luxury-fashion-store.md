# 案例：奢侈品时装电商

一个中等复杂度的真实案例，展示如何将 shadcn/ui + React + Vite + Tailwind 模版转化为 SKILL。

## 输入

- **模版**：shadcn/ui 基础模版（React 18 + Vite 5 + TypeScript + Tailwind CSS 3）
- **对话历史**：有（MGXEnv 格式，约 20 轮对话）
- **模版规模**：中型（约 15 个业务文件）

## Phase 1 分析结果

### 技术栈

```yaml
framework: react 18
build_tool: vite 5
language: typescript
css: tailwind 3
ui_library: shadcn-ui
package_manager: pnpm
```

### 骨架 vs 业务分类

**骨架**：vite.config.ts, tsconfig.json, tailwind.config.ts, components/ui/*, lib/utils.ts, main.tsx

**业务**：
- pages/Index.tsx, ProductDetail.tsx, Bag.tsx
- components/ProductCard.tsx, CartContext.tsx, AddToBag.tsx, CartIcon.tsx, Wishlist.tsx, ColorSwatch.tsx, SizeSelector.tsx, CategoryFilter.tsx
- data/products.ts
- index.css（CSS 变量部分）

### 产品定义摘要

- **功能**：产品网格展示、两级分类筛选、产品详情页、购物袋、收藏
- **风格**：极简奢华（轻字重、宽字间距、小字号、大留白）

### 架构约束

- 路由：`/` + `/product/:id` + `/bag`
- 状态：CartContext（addItem/removeItem/updateQuantity/clearCart/itemCount/total）
- 类型：Product（id/brand/name/price/image/colors/sizes/category/gender）
- Provider：QueryClientProvider > CartProvider > TooltipProvider > BrowserRouter

## Phase 2 产出结构

```
luxury_fashion_store_skill/
├── SKILL.md                     # 110 行
├── tasks/
│   ├── 01-generate-code.md      # 80 行（最重要）
│   └── 02-verify.md             # 40 行
├── reference/
│   ├── CONTEXT.md               # 60 行
│   ├── pages/                   # 3 个文件，~400 行
│   ├── components/              # 7 个文件，~500 行
│   ├── data/products.ts         # ~80 行
│   └── styles/index.css         # ~40 行
├── prompt-template.md          # 提示词模版
├── prompts/                    # 3 个即用型提示词
│   ├── prompt-1.md
│   ├── prompt-2.md
│   └── prompt-3.md
└── rules/
    ├── architecture.md          # 骨架约束
    └── design-system.md         # 推断规则 + 编码规范
```

**reference/ 总行数**：约 1080 行（中型模版，全量复制）

## 关键决策说明

### 为什么 reference/ 选择全量复制

这个模版有 15 个业务文件，总行数约 1080，低于 2000 行阈值。每个文件都展示了不同的模式（组件 props 设计、Context 实现、数据格式），值得保留。

### 为什么 rules/ 合并为 2 个文件

原本考虑 3 个（architecture + coding-standards + design-system），但 coding-standards 与 design-system 高度相关（都是"怎么写代码"），合并后减少 AI 跳转次数。


### SKILL.md 的 description 怎么写的

```
根据用户的品牌定位和需求，参考奢侈品时装电商架构从头生成定制化电商网站。
当用户说"帮我做个时装网站"、"生成一个电商"、"做个品牌官网"、
"我想要一个卖XX的网站"时使用此技能。
```

## 产物质量指标

- SKILL.md：110 行，清晰的两步流程
- 最核心的 01-generate-code.md：80 行，包含生成顺序 + 自检清单 + 陷阱防御
- reference/ 总计 1080 行，覆盖所有文件类型
- 2 个 examples 展示了推断规则的两个极端
