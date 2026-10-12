# 维护版 Telethon

保留原包名 `Telethon` 和导入路径 `telethon`；上游来自 Codeberg，本仓库的 `tgreg-maintained` 分支维护小补丁。`fork/manifest.json` 记录上游基线、版本、Layer 和 opentele 兼容版本。首次基线与原环境的 160 个 Python 文件一致；首个维护版本仅增加版本标识和构建维护流程。

## 构建和检查

以下命令在仓库根目录执行，使用 Python 3.12 或更高版本。构建器要求所有维护文件已经提交；从 `git archive HEAD` 的干净副本构建，因此不会打包本地 session、凭据或工作目录中的未提交文件。

```sh
python3.12 -m venv .fork-venv
.fork-venv/bin/python -m pip install -r fork/build-requirements.txt
.fork-venv/bin/python fork/build.py
.fork-venv/bin/python -m pip install 'opentele==1.15.1' dist/fork/telethon-1.45.0+tgreg.1-py3-none-any.whl
.fork-venv/bin/python fork/check_compat.py
```

构建目录同时保存 JSON 收据，包含完整维护 commit、上游 commit、源码归档和 wheel 的 SHA256、版本和 Layer。构建器拒绝覆盖同名发布文件。把上一次发布的 wheel 和收据一起保留，部署前校验 SHA256；项目依赖文件也应固定完整维护 commit，不能只引用分支名。

检查脚本创建内存 session，检查版本、Layer、opentele 继承关系和 TL 序列化，不连接 Telegram。运行上游单元测试前，在开发环境安装 pytest 和 pytest-asyncio，然后生成源码中的 TL 文件：

```sh
.fork-venv/bin/python setup.py gen
.fork-venv/bin/python -m pytest tests/telethon
```

离线检查证明包构建和兼容关系，不证明实际网络行为或账号风控结果。未来修改行为时，应增加能检出该行为回归的测试。

## 合并上游

保持 `upstream` 指向 `https://codeberg.org/Lonami/Telethon.git`，`origin` 指向本 GitHub fork。不要通过旧 GitHub 仓库的 Sync fork 更新。

```sh
git checkout tgreg-maintained
git status --short
git fetch upstream
git checkout -b upgrade/next-upstream
git merge --no-ff upstream/v1
```

开始前工作区必须干净。比较旧基线、新上游和本地维护提交；不要在冲突时把整个目录覆盖成上游版本。解决冲突时同步维护 `telethon/version.py` 的版本后缀、`pyproject.toml` 的 Source 地址和 `fork/manifest.json` 的上游 commit、版本、Layer；检查 opentele 是否兼容。提交、构建和验证通过后再合并回维护分支并推送。

```sh
git checkout tgreg-maintained
git merge --ff-only upgrade/next-upstream
git push origin tgreg-maintained
git rev-parse HEAD
```

用最后输出的完整 SHA 更新业务项目锁文件。保留上个 SHA 和 wheel 用于回退；不要 force push、删除维护历史或移动已发布标签。环境直接安装的依赖始终是这个 fork 的 `Telethon`，opentele 也使用它。
