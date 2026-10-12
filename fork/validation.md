# 初始维护基线验证

日期：2026-10-12。上游 commit：`0205278e715dd4a7454de683b9b9b76f0e13db85`，Telethon 1.45.0，Layer 230；检查环境为 Python 3.12.12，opentele 1.15.1，pytest 8.4.2，pytest-asyncio 0.23.8。

- 上游生成 TL 和错误类型后，与原项目安装的 160 个 Python 文件比较：没有差异、缺失或额外文件。
- 从已提交源码归档构建维护 wheel 成功；wheel 中版本和 Layer 与 manifest 一致。
- 安装 wheel 后 `fork/check_compat.py` 通过：opentele 与 Telethon 共用客户端和 session 类，类型与请求序列化往返通过，未连接 Telegram。
- `pytest tests/telethon`：32 通过，3 失败。失败均位于 `tests/telethon/client/test_messages.py`，涉及 send_message 向 send_file 转发参数：`update_stickersets_order` 未转发，以及旧测试预期未包含新参数。

3 个失败在单独导出的未经修改上游基线上同样复现。这是初始上游测试状态；本次维护提交没有修改消息发送、连接或注册逻辑。后续行为补丁必须与该基线比较并检查是否增加失败；不能以这些基线失败为理由跳过相关新增检查。

实际账号注册、网络互通、冻结概率和风控因果关系均未测试。
