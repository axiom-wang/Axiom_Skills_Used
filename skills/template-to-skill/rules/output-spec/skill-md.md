# 产出 SKILL 的 SKILL.md 规范

## Frontmatter（必须）

```yaml
---
name: <kebab-case 标识符>
description: <触发式描述，覆盖用户可能的问法，100-200 字>
---
```

**description 写法原则**：
- 先说做什么（"根据用户需求，参考 XX 模版架构从头生成定制化的 XX 应用"）
- 再说什么时候触发（覆盖用户可能的问法和场景描述）
- 稍微"推送"——宁可多触发不要漏触发

## 正文章节（按顺序）

1. **概述** — 一句话描述 + "定向修改，不是从头重写"声明
2. **参数表** — 根据模版业务类型设计（见下方"参数设计指引"）
3. **执行流程** — 三阶段流程图（Phase A 分析 → Phase B 修改 → Phase C 检查 + verify）
4. **骨架声明** — 模版内置的骨架文件列表（直接沿用，不需要初始化）
5. **reference/ 使用方式** — 4 步法（读背景 → 分析分层 → 输出定制清单 → 定向修改）
6. **目录结构** — 文件树
7. **注意事项** — 工作目录、核心原则、构建要求、禁令

## 参数设计指引

参数应从模版的业务本质推导，不要硬套固定模板。设计原则：

1. **必填参数**：让 AI 有足够信息做出差异化设计决策的最小集
2. **选填参数**：让用户可以精细控制但不必须的补充信息
3. **AI 自主推断**：参数以外的一切细节

不同领域的参数设计参考：

| 领域 | 必填参数 | 选填参数 |
|------|---------|---------|
| Store | brand_name, business_description | style_keywords, price_range, currency |
| Service | product_name, value_proposition | target_audience, cta_text, pricing_tiers |
| AI Tools | tool_name, core_function | input_type, output_type, tone |
| Marketplace | platform_name, category_focus | transaction_model, trust_signals |
| Game | game_name, game_genre | art_style, target_platform, monetization |
| Booking | business_name, service_type | booking_granularity, location |
| Pets | brand_name, pet_focus | service_types, tone, target_pet_owners |
| Portfolio | owner_name, profession | project_types, personal_brand_keywords |
| Jobs | platform_name, industry_focus | job_types, target_seniority |
| Course | platform_name, subject_area | learning_format, target_audience |
| Health | app_name, health_focus | tracking_metrics, motivation_style |
| Travel | site_name, travel_style | destinations, content_type |
| Food | brand_name, food_category | service_model, cuisine_style |
| Digital Goods | store_name, product_type | pricing_model, target_creator |
| Creator | creator_name, content_type | publication_frequency, monetization |
| Finance | app_name, finance_domain | risk_level, target_user_expertise |
| Lifestyle | brand_name, lifestyle_focus | aesthetic_keywords, target_demographic |

关键：参数数量控制在 2-4 个必填 + 2-3 个选填，不要让用户填一堆表单。
