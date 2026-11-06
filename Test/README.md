# 测试交付索引
量化测试方案.md及docx定义五类场景；正常、边界、对抗、权限、故障各有独立MD及DOCX，DOCX内嵌来自实际测试JSON的步骤可视化，非伪造浏览器截图。
可执行代码在tests/test_submission_scenarios.py，原有回归在tests目录；原始JSON、JUnit及完整日志在docs/提交补充/测试证据。39项后端与6项前端通过，5条弃用警告；真实模型及公网验证未执行。
