# 代码实现与文档验证

这份材料补充课程提交目录，说明“实现了什么、怎样验证、证据在哪、哪些仍未验证”。本次改进基于源码基线 `496c109`，没有修改教学业务挖掘原始报告。

## 复现方法

环境：Python 3.11 或 3.12、Node.js 20 或以上。在项目根目录执行：

```sh
python -m pip install -r requirements.txt
python scripts/verify.py
```

Windows 同样使用这两条命令，不要求安装 make。首次安装依赖需要联网。验证本身不需要购买模型 API，不调用真实医院或审批接口。测试通过临时 SQLite 数据库运行，保留用户运行数据库。

脚本依次运行 Python 语法编译、后端 pytest、前端 Node 测试、文档完整性检查。任一步失败，最终退出码为非零；缺少 Node 也报失败。结果默认写入 `artifacts/verification/`，包含 JSON、JUnit XML 以及各步骤原始输出。不要把“接口返回 HTTP 200”当作 SSE 对话成功，测试会检查流内的 error/done 事件。

## 本次实测证据

|检查|结果|原始证据|
|---|---|---|
|Python 语法|PASS|[syntax.txt](evidence/syntax.txt)|
|后端约束、模型错误映射及 HTTP 集成|34 项通过，0 失败|[backend.txt](evidence/backend.txt)、[JUnit](evidence/pytest.xml)|
|前端 SSE 分块、异常和终态|6 项通过，0 失败|[frontend.txt](evidence/frontend.txt)|
|课程文件完整性、DOCX容器、评测用例结构|结果见自动输出|[documents.txt](evidence/documents.txt)|
|运行环境、命令、源码 SHA256|自动记录|[verification.json](evidence/verification.json)|

执行日期和 Python 版本以 JSON 为准。测试时有一条 Starlette/AnyIO 弃用警告，未造成失败。本次使用 Windows Python 3.12，未声称 Python 3.11 或 Docker 已在本轮重跑。环境中首次 HTTP 测试因回环连接权限受限等待，开放本机测试网络后重新运行，表内结果来自重跑后的完整执行。

## 代码改进

1. 预约满额后用同一幂等键重试，返回原预约，不误报无号；不同用户或号源复用该键被拒绝。容量更新仍由事务内条件更新保护。
2. 报销凭证 HMAC 读取配置中的 `ELIGIBILITY_SECRET`，移除工具层硬编码密钥。切换密钥前签发的未使用凭证需要重新校验。
3. 报销确认回复跟随原待办的会话 ID 保存，避免写入“最近创建”的其他会话。
4. 确认接口只接受 confirm/reject；金额校验拒绝 NaN、无穷和非正数。
5. 新增离线 HTTP→真实确认处理→工具→SQLite→审计集成验证，外部模型仅使用固定回复替身；新增并发、取消、过期和归属测试。

## 如何给老师查看

先打开[需求追溯矩阵](requirements-traceability.md)，从一条需求定位代码和测试；再看 `evidence/backend.txt` 与对应测试断言；最后现场运行 `python scripts/verify.py`，查看退出状态和新生成的报告。业务材料从[课程提交清单](../课程提交/README.md)进入。

## 尚未验证与缺口

- 离线模型替身只验证应用处理逻辑，不证明真实大模型选工具、回答内容或医疗建议可靠。
- `tests/eval_cases.json` 的 30 条案例只验证结构，人工模型评测状态为 **NOT_RUN**。制度变更后须重审期望答案，不能直接沿用固定报销比例。
- 实验室案例的队列重排、迟到加号、排班实时同步、交接签核尚无完整实现；当前代码只覆盖预约助手、制度问答及报销扩展。
- 真实 HIS/OA/企业微信、员工 SSO、院内试点、等待时间下降 20%等均为 **NOT_RUN**，不得写成达标。
- 课程文档的 SHA256 与 DOCX容器检查只证明文件完整及基本结构，不证明内容正确或排版已由 Word 逐页复核。
- 当前报销规则为演示配置；制度文档与规则配置仍需业务负责人核对，不能作为真实财务结算依据。

这些材料让实现与验证更易核查，不能据此保证课程分数。
