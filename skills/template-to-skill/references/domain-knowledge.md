# 领域知识库

分析模版时，先识别其所属领域，再加载对应领域文件指导可定制点识别、参数设计和推断规则生成。

## 已知领域清单

| 领域 | 文件 | 典型场景 |
|------|------|---------|
| Store | `domains/store.md` | 品牌官网电商、独立站、DTC |
| Service | `domains/service.md` | SaaS 落地页、企业服务、工具介绍 |
| AI Tools | `domains/ai-tools.md` | AI 产品界面、对话式工具、生成器 |
| Marketplace | `domains/marketplace.md` | 多卖家平台、C2C、聚合交易 |
| Game | `domains/game.md` | 游戏官网、游戏内嵌 H5、排行榜 |
| Booking | `domains/booking.md` | 预约系统、酒店/机票/餐厅预订 |
| Pets | `domains/pets.md` | 宠物服务、宠物电商、宠物社区 |
| Portfolio | `domains/portfolio.md` | 个人作品集、设计师展示、简历站 |
| Jobs | `domains/jobs.md` | 招聘平台、求职工具、HR 系统 |
| Course | `domains/course.md` | 在线教育、课程平台、学习管理 |
| Health | `domains/health.md` | 健康管理、医疗预约、健身追踪 |
| Travel | `domains/travel.md` | 旅游攻略、行程规划、目的地展示 |
| Food | `domains/food.md` | 餐饮外卖、食谱平台、餐厅展示 |
| Digital Goods | `domains/digital-goods.md` | 数字产品销售、模版/素材/插件 |
| Creator | `domains/creator.md` | 内容创作者、博客、Newsletter、播客 |
| Finance | `domains/finance.md` | 理财工具、加密货币、支付、记账 |
| Lifestyle | `domains/lifestyle.md` | 生活方式品牌、时尚杂志、兴趣社区 |

## 领域识别信号

按以下顺序匹配（命中即停）：

| 信号来源 | 检查方式 | 优先级 |
|---------|---------|--------|
| 用户 prompt | 直接提及业务类型时以用户说的为准 | 最高 |
| 路由命名 | `/product`, `/cart` → Store；`/booking`, `/schedule` → Booking | 高 |
| 数据模型 | `Product/Cart/Order` → Store；`Course/Lesson` → Course | 高 |
| 组件命名 | `ProductCard/AddToCart` → Store；`ChatWindow/PromptInput` → AI Tools | 中 |
| 依赖包 | `stripe` → Store/Finance；`openai` → AI Tools；`mapbox` → Travel | 中 |
| 目录结构 | `lessons/` → Course；`portfolio/` → Portfolio | 低 |

## 混合领域处理

实际模版经常是多领域混合（如"Store + Pets"、"Service + AI Tools"）。处理规则：

1. **主领域**：占页面/功能 60% 以上的领域，决定核心骨架和主要可定制点
2. **辅助领域**：提供补充可定制点，但不改变主骨架
3. **可定制点合并**：取两个领域的并集，去重后按优先级排列
4. **加载顺序**：先加载主领域文件，再加载辅助领域文件

示例：
- Store + Pets → 主骨架是商品浏览+购物车，可定制点包含宠物品种筛选/宠物档案
- Service + AI Tools → 主骨架是产品介绍+定价，可定制点包含 AI demo/对话界面

## Fallback：未知领域处理

当模版不匹配任何已知领域时：

1. **分析归属**：从模版的路由、数据模型、组件、视觉风格中推断其业务本质
2. **命名领域**：给出一个简短的领域名称（如 "Music Streaming"、"Real Estate"）
3. **自主构建领域知识**：参考已知领域文件的结构，基于 AI 自身认知 + 网络搜索，为该领域填充：
   - 识别关键词
   - 核心骨架（典型页面结构）
   - 典型可定制点（5-8 个）
   - 设计推断侧重
4. **写入产出**：将构建的领域知识直接融入产出 SKILL 的 rules/ 和 reference/CONTEXT.md 中
5. **建议更新**：在执行结束时提示用户"该模版属于 [XX] 领域，建议将此领域知识补充到 `references/domains/` 中供后续复用"

## 使用方式

分析阶段按以下顺序使用本文件：

1. **识别领域**：用"领域识别信号"表匹配模版所属领域（可能是多个的混合）
2. **加载领域文件**：读取对应的 `domains/<领域>.md`
3. **提取可定制点**：取该领域的"典型可定制点"表，结合代码结构信号筛选出实际存在的
4. **补充推断规则**：用"设计推断侧重"指导 design-system.md 的生成方向
