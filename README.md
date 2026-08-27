# AI Product Architecture Reverse Analysis

一个面向各类 AI 产品的证据驱动架构拆解 Skill，不限定视频或多模态创作领域。

它帮助分析者从真实产品截图、聊天记录、工作区数据、任务状态、工具结果、最终产物、错误提示和官方公开资料出发，逐步还原用户旅程、Agent 契约、工具调用、全局上下文、产物流、模型路由、权限、计费、安全与底层产品架构。

适用领域包括通用 Agent、AI 编程、AI 搜索与研究、AI 数据分析、AI 办公与内容生产、AI 客服与业务流程，以及图片、视频、音频等多模态创作产品。

## 核心能力

- 用户旅程与正常、修改、失败、中断路径
- 实际出现的 Agent 清单与 I/O 契约
- 单 Agent 功能等价 System Prompt
- 用户流、Agent 流、工具流、数据流、领域产物流和外部副作用流
- 按产品领域选择上下文、工具、验证和风险模板
- As-Is、To-Be、架构风险和规则—证据追溯
- 一份包含全部分析的单文件 HTML 最终报告，而非只有架构可视化
- 可复制、可下载的 Mermaid 用户旅程、Agent 流、状态机、ER 图、时序图和全景架构图
- 证据筛选、证据深链接、全局搜索、关键表格 CSV 导出和打印/另存 PDF
- 最终 HTML 自动验收，防止空章节、占位符、缺失图源码或交互断链

## 证据原则

所有结论必须区分：

- **已确认**：页面、截图、公开聊天、可见资产、状态、工具结果或官方资料直接支持。
- **合理推断**：由多条事实共同支持，但后台实现不可见。
- **建议设计**：为稳定性、完整性或可运营性提出的改进。
- **未知**：当前证据不足。

Agent 声称“已完成”不等于任务真实完成。必须同时检查领域产物、任务状态、工作区、执行回执和全局上下文；发生冲突时保留冲突，不自行替产品选择事实。

## 安装

将本仓库克隆或复制到个人 Skills 目录：

```text
~/.agents/skills/ai-product-architecture-reverse-analysis
```

Skill 入口为 `SKILL.md`。

## 使用

在支持 Skills 的 Agent 环境中调用：

```text
使用 $ai-product-architecture-reverse-analysis，基于我提供的截图和操作记录完成证据驱动的 AI 产品架构拆解。
```

可以单独指定四种分析模式：

1. 用户旅程模式
2. Agent 契约模式
3. 单 Agent Prompt 模式
4. 完整产品架构模式

完整产品架构模式默认只交付一份可独立打开的 HTML 成品。证据、用户旅程、Agent 契约、工具、上下文、数据流、图表、As-Is、To-Be、风险和未知项全部在同一份报告中。

## 文件结构

```text
ai-product-architecture-reverse-analysis/
├── SKILL.md
├── assets/
│   └── report-template.html
├── agents/
│   └── openai.yaml
├── scripts/
│   └── validate_report.py
└── references/
    ├── evidence-protocol.md
    ├── analysis-workflow.md
    ├── domain-profiles.md
    ├── report-contract.md
    ├── interactive-report-spec.md
    └── deliverables.md
```

## 最终报告校验

完整报告交付前运行：

```text
python3 scripts/validate_report.py /absolute/path/to/product-architecture-analysis.html
```

校验器检查 18 个必备章节、证据等级、证据深链接、Mermaid 图源码与复制/下载按钮、CSV 导出、搜索、打印、CSP、空章节和未替换占位符。

## 安全边界

- 不还原或声称读取模型隐藏思维链。
- 不把第三方猜测当成真实架构证据。
- 不输出 Cookie、Token、密码、鉴权头或个人敏感信息。
- 默认只读查看产品页面，不触发生成、购买、充值、发布、删除或覆盖资产。
- 未公开的后端语言、数据库、消息队列、云服务和内部工具名不得写成已确认事实。

## License

[MIT](LICENSE)
