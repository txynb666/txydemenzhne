# 参考项目学习与本项目改进

用户提供的参考项目是展会服务流程项目，与门诊领域不同。本次借鉴可审计的工程组织方式，没有复制其业务代码、测试结果或满分结论。

参考读取版本：`3851255974fb0f7f232302f919e10591e39836d4`。

|参考做法|参考来源|本项目落地|
|---|---|---|
|需求对应实现、测试、工具证据、业务结论和剩余风险|[需求追溯](https://github.com/ZHISISANG/Engineering_Technology_and_InnovativePractice/blob/3851255974fb0f7f232302f919e10591e39836d4/docs/requirements-traceability.md)|本目录需求追溯矩阵，明确PASS/PARTIAL/NOT_RUN/NOT_IMPLEMENTED|
|单一入口执行检查并保留原始输出|[验证脚本](https://github.com/ZHISISANG/Engineering_Technology_and_InnovativePractice/blob/3851255974fb0f7f232302f919e10591e39836d4/scripts/verify.sh)|跨平台Python `scripts/verify.py`，失败退出非零，保存JUnit、日志、源码摘要|
|跨模块执行后检查产物及审计|[端到端测试](https://github.com/ZHISISANG/Engineering_Technology_and_InnovativePractice/blob/3851255974fb0f7f232302f919e10591e39836d4/tests/test_end_to_end.py)|真实HTTP确认路由、服务工具、临时SQLite和审计断言；仅外部模型回复使用替身|

## 为什么优先做这些

原项目已有可运行页面、工具及说明文档，但 README 仍写9项测试、泛化“任何写操作先确认”，以及缺少一次运行即可复现的验收入口。只看截图无法核实并发、重复提交或确认后的数据归属。

本次用实际修复支撑代码实现，用自动生成证据支撑文档验证，减少“功能描述大于实现范围”的问题。新增四项代码修复和十二项后端测试（34对比原22），前端原6项仍通过。具体修改见验证总览。

没有老师的详细评分标准，无法推断每项扣分原因或保证满分。若评分要求覆盖实验室主流程，下一阶段优先补齐“签到—候诊队列—异常转交—人工接手—到诊事件”闭环及回放数据，而非继续增加报销功能或页面数量。
