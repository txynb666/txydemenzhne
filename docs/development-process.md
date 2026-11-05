# 开发与提交过程索引

本页于 2026年11月5日事后整理已有 Git 历史，用于核查实际开发过程；不代表这些历史工作事先创建过 Issue 或经过独立评审。提交链接和时间以 GitHub 为准。本项目由个人在 AI 辅助下开发。

## 已有真实迭代

|阶段|实际提交|内容与证据|
|---|---|---|
|本地模型接入|[e476ecc](https://github.com/txynb666/txydemenzhne/commit/e476ecc0bb56bfb86f2ba2601c0a665f91d11951)|Ollama配置、模型诊断与错误提示；不声称当时已有PR|
|聊天界面改进|[6e81730](https://github.com/txynb666/txydemenzhne/commit/6e8173032e387c00d6943d6af38a8ddc43bdc99a)、[80d8e72](https://github.com/txynb666/txydemenzhne/commit/80d8e722fb86ccd4865098e9ee811b1c66aaf2e7)、[ec04c7a](https://github.com/txynb666/txydemenzhne/commit/ec04c7ad24144c5840b7437b52afd695d478cb77)|响应式布局、头部输入区、可读性逐次调整|
|课程资料整理|[496c109](https://github.com/txynb666/txydemenzhne/commit/496c10981e0cfb5610d32e2a7a2ef0dba7615133)|原始业务挖掘、流程图、设计和报价，见课程提交目录|
|代码修复与验证|[397db31](https://github.com/txynb666/txydemenzhne/commit/397db3196bd3763c00db7208a737f5dc81e81af6)|预约幂等、密钥、会话归属和输入校验；34项后端与6项前端测试，见验证目录|

以上按可识别的实际迭代归纳，不把提交数当作功能质量或评分结果。

## 本次完整流程

- 问题：[Issue #1](https://github.com/txynb666/txydemenzhne/issues/1)，从创建时开始跟踪流程改进。
- 分支：`chore/submission-process-evidence`。
- 实现：[997303e](https://github.com/txynb666/txydemenzhne/commit/997303e8bd0e54e635364f04de71b5b31ec624f4)，加入Issue模板、PR模板及贡献规范。
- 合并请求：[PR #2](https://github.com/txynb666/txydemenzhne/pull/2)，保留变更、验证、自检和合并状态。
- 本页所在后续提交补充真实历史索引、恢复保留原工程约束、增加文档入口。
- 评审性质：个人/AI自检；没有同学或教师的独立评审，不伪造Approve记录。

## 实际验证记录

2026年11月5日，本机 Windows、Python 3.12，执行：

```sh
python scripts/verify.py --output-dir artifacts/process-verification
```

实际结果：syntax PASS；backend 34 passed、0失败；frontend 6 passed、0失败；documents PASS（13份材料完整性、30条用例结构）。后端有1条Starlette/AnyIO弃用警告。本轮先受本机回环连接权限限制等待，开放权限后完整重跑通过。重跑的原始输出和环境记录见[过程验证记录](process-evidence/)。

对新模板人工核查了GitHub模板路径、Markdown结构、Issue和PR链接，并通过GitHub PR差异确认实际变更。未执行真实模型质量评测或院内验收；没有本轮GitHub Actions运行结果。课程原件的SHA256/容器验证不是内容正确性的证明。

## 自检与风险

本轮仅修改流程模板、贡献规范与索引文档，不修改运行逻辑、制度原件或数据库。自检发现初稿贡献规范替换了原目录约定与工具要求，随后在同一PR补回；该检查属于个人/AI自检。

风险是模板不会自动保证执行规范，后续开发仍需实际填写验收结果。需要撤销时可回退此PR的合并提交，不影响现有业务数据。是否完成合并、何时关闭Issue，以GitHub页面状态为准。

## 后续仍需真实推进

后续新增功能继续按Issue→分支→实现→测试→PR处理。异常队列、真实医院对接、院内试点等仍未完成，见[需求追溯矩阵](validation/requirements-traceability.md)。不得用创建Issue或增加提交次数代替功能实现。
