---
name: git-helper
description: 在 Codex 开发项目中执行 feature 分支校验、Git 拉取、Conventional Commits 提交、推送及人工确认的冲突辅助解决。用于实际 Git 协作，不替代代码审查。
---

# Git规范协作助手

机器标识为 `git-helper`；按用户要求存放在 `skills/git_helper/`。

## 入口

Python 3.10+、Git，无第三方依赖。从项目根目录运行：

```powershell
python skills/git_helper/scripts/git_helper.py status
```

主程序读取 Skill 内的 `config.json`；全局参数 `--repo` 指定仓库，`--config` 指定替代配置。先检查分支、暂存区和 merge/rebase 状态。配置不能替代用户对提交和推送目标的授权。

## 工作流

- 新项目经授权后 `git init -b main`，用 `branch feature/<主题>` 创建开发分支。禁止在 main/master/develop 直接提交或推送；遵守仓库更严格的规则。
- `pull` 只支持干净工作区、同名 upstream 和 fast-forward。遇到分叉即停止，展示两侧提交并协商整合方式。禁止自动 stash、reset 或重试合并。
- 提交前审阅实际 diff、敏感信息和生成文件，运行项目有关检查；只暂存明确文件，不默认 `git add .`。按 [提交模板](assets/commit-message.txt) 填写并删除无关段落。
- `commit -m "feat(scope): 说明"` 仅提交暂存内容，检查 Conventional Commits、索引冲突、冲突标记及空白错误。通过这些检查不代表代码语义正确。
- `push` 展示远程和分支，推送至同名 feature 分支，不强推。失败即停止并说明原因。
- `conflicts` 展示工作区和 base/ours/theirs 原始内容，保存独立快照。读取 [冲突解析模块](references/conflicts.md)，向用户展示候选代码，由用户选择后才写入。
- 禁止自动选 ours/theirs、无脑拼接双方代码、自动暂存解决结果。二进制、重命名、删除、子模块和 rebase 冲突要单独解释语义。

## 加载与使用

当前对话直接引用本文件并要求“使用 Git规范协作助手”。需安装时可复制本目录到项目 `.agents/skills/git-helper/` 或用户 `~/.codex/skills/git-helper/`，不要未经要求修改用户环境。新会话未列出技能时可直接引用绝对路径。

```powershell
# 在干净工作区中，从当前 HEAD 创建并切换到功能分支
python skills/git_helper/scripts/git_helper.py branch feature/add-agent

# 查看当前分支、工作区修改和远程仓库地址
python skills/git_helper/scripts/git_helper.py status

# 完成修改并审阅后，仅暂存指定目录；实际使用时替换为本次相关路径
git add -- skills/git_helper

# 校验分支、提交标题及暂存内容，通过后创建提交（示例说明请按实际修改填写）
python skills/git_helper/scripts/git_helper.py commit -m "feat(skill): 添加 Git 规范协作助手"

# 工作区干净时，将当前功能分支推送到同名远程分支，并设置 upstream
python skills/git_helper/scripts/git_helper.py push

# 已有同名 upstream 且工作区干净时，仅快进拉取；分叉时停止
python skills/git_helper/scripts/git_helper.py pull

# 查看已有索引冲突，展示代码并保存快照；不自动修改文件或解决冲突
python skills/git_helper/scripts/git_helper.py conflicts
```

首次上传须明确 GitHub 仓库地址、权限及可公开内容，再设置 origin；不得猜测目标。初次发布默认分支须单独说明，不能偷偷绕过 feature 保护。
