# 需求—实现—测试—验收追溯矩阵

2026年11月6日更新：下表保留原回归范围；本轮已新增后台预约审核与服务端拒绝AI伪造确认人，证据见 `tests/test_submission_scenarios.py` 的正常、对抗和权限场景，以及 `docs/提交补充/测试证据`。R02原先的“不能保证模型不伪填确认人”缺口已在工具入口修复；真实医护角色与临床签核仍未建立。

事实来自[实验室业务挖掘说明](../课程提交/01_业务挖掘说明与范围映射.md)。事实 ID 为教学合成案例证据，并非现场访谈。PASS 只表示列出的自动化断言通过；不等于对应业务需求全面验收。

|需求与来源|实现位置|可执行验证|工具侧结论|业务侧结论及缺口|
|---|---|---|---|---|
|R01 预约号源核实，f21/f32|`app/services/tools.py` 的 `check_slot_availability`、`create_appointment`|`test_retry_when_slot_full`、`test_concurrent_bookings_never_exceed_capacity`、`test_idempotency_key_cannot_reveal_other_users_booking`|PASS：满额重试返回同一单；12次请求、容量3、实际成功3；跨用户键冲突拒绝|NOT_RUN：演示SQLite，未接真实排班；不等于万人并发验证|
|R02 专业分诊由医护确认，f05/f52|`create_appointment`，AI未传确认人时写 `pending_triage`|`test_ai_appointment_requires_human_confirm`|PASS：演示工具的待分诊状态|PARTIAL：真实身份与医护签核工作台未实现；不能保证模型永不伪填确认人|
|R03 每次处理可追溯，f45|`app/repositories/agent_trace.py`、`app/main.py` 的 `chat_confirm`|`test_confirm_response_saved_to_original_conversation`、`test_http_confirmation_creates_exactly_one_draft_and_audit`|PASS：确认回复回原会话；一份草稿、一条工具审计，重复确认拒绝|PARTIAL：未完整关联真实资料版本、接手人、专业签核人|
|R04 系统不可用时明确提示，f44|`app/core/model_provider.py`、`app/main.py` SSE error|`test_chat_sse_returns_actionable_model_error`、`test_retrieval_failure_has_nonzero_error_code`、`tests/test_stream.cjs`|PASS：模型余额/向量错误提示，前端不把失败当正常回复|PARTIAL：提示可用，人工分派闭环与接手时间未实现|
|R05 报销先校验再确认（本项目扩展）|`check_reimbursement_eligibility`、`consume_token`、`harness.resume`|`test_valid_flow_creates_draft`、`test_token_replay_rejected`、`test_tampered_amount_rejected`、`test_http_reject_prevents_later_execution`、`test_expired_and_wrong_user_confirmation_cannot_execute`|PASS：一次性凭证、确认/取消/过期及重放；真实数据库断言|NOT_RUN：未接OA审批或财务付款；不把扩展报销等同原始候诊问题已解决|
|R06 输入与密钥配置可靠（工程约束）|`ConfirmRequest`、`tools._sign`、金额校验|`test_invalid_confirmation_action_rejected`、`test_signing_uses_configured_secret`、`test_invalid_amount_never_issues_eligibility_token`|PASS：非法action返回422；使用注入密钥；非法金额不签发凭证|NOT_RUN：未完成生产安全审计；员工端仍使用demo_user|
|R07 资料提交可核验（课程约束）|`scripts/verify_docs.py`、课程目录SHA256清单|一键验证的 documents 步骤|PASS：清单逐文件核验、DOCX ZIP/XML入口检查、30条案例字段检查|NOT_RUN：真实模型30例人工评测、业务人员文档签字验收|
|R08 等待改善与异常队列，f02/f10/f11/f25/f53|当前只有范围说明，未完成队列协同模块|无实际端到端测试|NOT_IMPLEMENTED|NOT_RUN：无到院/签到/叫号真实数据，不能宣称68→40分钟或下降20%|

## 本次回归的输入与预期

|复现场景|输入|验收断言|
|---|---|---|
|预约网络重试|容量1、同一用户同一幂等键连发2次|同预约ID，booked不增加第二次|
|争抢最后名额|容量3、8个线程发12个唯一请求|成功数=3，booked=3|
|确认前预览|已通过报销资格校验、创建待确认动作|确认之前草稿数量=0|
|确认与再次确认|同一token提交2次|第一次done，第二次error；仅1草稿和1审计|
|取消后再确认|reject后confirm|取消成功、后续error、草稿数量=0|
|跨会话确认|原会话存在待办，再创建新会话|回复只写原会话|

实现证据在 `tests/test_acceptance.py`；全部原始结果在[证据目录](evidence/)。这些断言验证应用行为，未执行医疗准确率、可用性或高并发性能评估。
