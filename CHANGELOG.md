# 更新日志

## v1.0.5

- 生成的图片文件名包含提示词（清洗后），方便在服务器上查找和管理
- 修复 metadata.yaml 版本号被重置的问题

## v1.0.4

- 新增 CHANGELOG.md 更新日志文件
- AstrBot 插件更新时可查看变更记录

## v1.0.3

- 查询类结果（余额查询、预设列表）改用合并转发消息发送，不再刷屏
- 添加 `_forward_result` 辅助方法统一处理转发消息

## v1.0.2

- 添加 LLM 工具调用：查询余额（nai_get_balance）
- 添加 LLM 工具调用：预设管理（nai_list_presets、nai_save_preset、nai_delete_preset）
- 修复 LLM 工具调用结果不发送给用户的问题

## v1.0.1

- 修复 `/nai save` 指令参数丢失的问题（GreedyStr 默认值导致只截取第一个 token）
- 添加查看单个预设详情功能（`/nai presets <预设名>`）

## v1.0.0

- 初始版本
- `/nai` 指令文生图，支持尺寸、预设、质量前缀、负面提示词、随机种子
- LLM Tool 调用生图（nai_generate）
- 5 个内置预设 + 自定义预设保存/删除
- 支持普通/2K/4K 分辨率
- 图片本地缓存，自动清理
- 配套人格提示词（生图助手）
