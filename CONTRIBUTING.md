# 开发与提交规范

本次新增的流程要求从本次更新开始使用，不代表早期提交已经遵循这些步骤。

1. 先建 Issue，描述真实问题、复现步骤和可验证的完成标准。
2. 从最新 main 创建功能分支，一条分支解决一个明确问题。
3. 按有意义的实现阶段提交。建议使用 feat、fix、test、docs、chore，说明改变的行为；不通过空提交或机械拆分凑次数。
4. 在项目根目录运行 `python scripts/verify.py`，需要 Python 依赖和 Node.js。保留实际输出，未运行检查明确写 NOT_RUN。
5. 创建 PR，关联 Issue、实现提交、测试结果及风险。个人自检与独立评审分别标注。
6. 核实结果后合并，并通过 PR 关闭对应 Issue；遗留问题保持开放。

## 提交前检查

- 不提交 .env、账号令牌、运行数据库、患者资料或无关本地修改。
- 测试通过不等于真实模型准确率或业务收益达标。
- 制度文本、规则配置和评测期望如有差异，说明差异并由业务负责人核实。
- 文档与代码关联到具体提交。补整理的历史索引明确标记为事后整理，不回填日期。

## 本仓库验证入口

`python scripts/verify.py` 依次执行语法、后端、前端和课程文件完整性检查，失败返回非零。输出位于 artifacts/verification/，默认不入库；需要提交证据时人工检查敏感信息后归档到 docs/validation/evidence/。

当前有本地一键验证，未建立本轮 GitHub Actions 自动运行记录；不能把本地 PASS 写成 CI 已通过。

详见 [验证总览](docs/validation/README.md) 与 [提交过程索引](docs/development-process.md)。

## 保留的工程约束

|目录|职责|
|---|---|
|app/core/|配置与常量|
|app/api/|路由与请求校验，业务规则放services|
|app/services/|业务逻辑和工具，不耦合HTTP|
|app/agents/|编排与提示词，数据访问交给repositories|
|app/rag/|检索与向量化|
|app/repositories/|数据访问|
|static/、templates/|前端资源|

修改工具必须运行回归测试；修改提示词须检查兜底逻辑。新增写工具加入 tools.WRITE_TOOLS，需人工确认的加入 harness.CONFIRM_REQUIRED，并携带幂等键。新增接口遵循统一 code 与中文message错误响应，不直接暴露500堆栈。涉及Agent行为时说明对30条评测计划的影响，未跑真实模型评测须写明。

## 开发环境

Python安装依赖后可用 `uvicorn app.main:app --reload --port 8000` 启动；本地免费模型配置见README。已有Linux初始化方式仍可用：`bash scripts/init.sh`、激活.venv、`make dev`。跨平台完整验证统一使用 `python scripts/verify.py`。
