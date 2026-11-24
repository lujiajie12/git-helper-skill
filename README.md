# Git规范协作助手

面向 Codex 开发智能体项目的 Git 协作 Skill，采用 feature 分支工作流，提供一个无第三方 Python 依赖的命令行辅助程序。

## 解决什么问题

协作开发中容易出现直接在主分支提交、提交说明混乱、误覆盖冲突代码和拉取时意外整合历史等问题。本项目通过分支与提交检查、仅允许快进拉取、冲突代码展示及原始版本快照，帮助开发者和 Codex 按一致的流程操作。

冲突处理分为两部分：程序负责展示与备份；Codex 按 Skill 中的流程解释候选方案，在用户选择后辅助修改。命令行程序本身不自动解决冲突。

## 主要功能

| 命令 | 实际行为 |
| --- | --- |
| `status` | 显示当前分支、工作区简要状态和远程地址 |
| `branch <名称>` | 在干净工作区创建并切换到符合配置的 feature 分支，以当前 HEAD 为起点 |
| `commit -m <说明>` | 仅提交已暂存内容，校验分支、提交标题、空暂存区、空白错误和疑似冲突标记 |
| `pull` | 工作区干净且 upstream 为同名远程分支时，执行仅快进拉取；历史分叉时停止 |
| `push` | 工作区干净时推送到同名远程 feature 分支，并设置 upstream；不使用强推 |
| `conflicts` | 检查未合并索引条目，展示冲突文件及 stage 版本，保存快照并列出人工处理选项 |

提交、拉取和推送默认仅允许 `feature/...` 分支，拒绝 `main`、`master`、`develop`。除状态和冲突查看外，程序遇到未解决冲突或正在进行的 merge/rebase 等操作会停止。

### 冲突保护与边界

- 文本冲突展示工作区内容和 stage 1/2/3（通常对应 base/ours/theirs）；某些冲突可能没有全部 stage。
- 每次检查创建唯一快照，保存 HEAD、状态、索引及可读取的冲突文件和 stage blob。普通仓库通常位于 `.git/git-helper-backups/<唯一编号>/`；worktree 等场景使用 Git 实际私有目录。
- 二进制或非 UTF-8 内容显示摘要；符号链接与子模块作特殊处理，不按普通文本写回。
- 程序只列出“保留当前侧、保留传入侧、人工组合、暂不处理”，没有交互式选项菜单或自动应用方案的命令。
- 用户选择后，Codex 按 [冲突处理流程](skills/git_helper/references/conflicts.md) 重新核对现场、展示和应用选定代码、检查差异并运行相关测试。这些步骤不是 CLI 自动完成的功能。
- 快照不是完整仓库备份，也没有一键恢复命令。快照可能包含敏感代码，不能上传。

## 安装方法

### 环境要求

- Python 3.10 或更高版本。
- Git，支持 `git switch`，且命令在 PATH 中可用。
- 提交时已配置 Git 用户名和邮箱；远程操作需要仓库地址、网络连接及相应权限。

本项目不需要 `pip install`，也不需要 GitHub CLI。取得项目文件后，在项目根目录检查环境并查看命令帮助：

```powershell
python --version
git --version
python skills/git_helper/scripts/git_helper.py --help
```

### 作为 Codex Skill 使用

直接向 Codex 引用 [SKILL.md](skills/git_helper/SKILL.md)，例如：

```text
请读取 skills/git_helper/SKILL.md，使用 Git规范协作助手检查本仓库状态。
```

如需安装为项目 Skill，将整个 `skills/git_helper` 目录复制到目标项目的 `.agents/skills/git-helper/`；用户级位置为 `~/.codex/skills/git-helper/`。保留目录内全部资源，安装后在新会话中检查是否可用；未被发现时直接引用 SKILL.md 的完整路径。机器标识为 `git-helper`，显示名为“Git规范协作助手”。

以下命令示例使用源码目录，复制安装后应相应调整脚本路径。

## 使用方法

### 1. 检查仓库

```powershell
python skills/git_helper/scripts/git_helper.py status
```

必须在 Git 仓库中运行，或通过 `--repo` 指定已有仓库。程序不会自动初始化仓库。全局参数写在子命令之前：

```powershell
python skills/git_helper/scripts/git_helper.py --repo "D:/projects/agent" status
```

对于尚未初始化的新项目，可先手动执行 `git init -b main`。若准备创建 feature 分支，工作区必须干净；新项目已有未跟踪文件时，应先明确首次提交方案，程序不会自动暂存文件。

### 2. 创建分支并提交

在干净的已有仓库中创建分支，再开始修改：

```powershell
python skills/git_helper/scripts/git_helper.py branch feature/add-agent
# 完成修改后，审阅差异并仅暂存选定文件
git diff
git add -- src/agent.py
git diff --cached
python skills/git_helper/scripts/git_helper.py commit -m "feat(agent): 添加任务执行入口"
```

`src/agent.py` 是示例业务文件，需替换为实际修改路径。程序不会执行自动暂存、项目测试、敏感信息扫描或代码审查；这些工作应在提交前完成。

提交标题格式为 `type(scope): 说明`，scope 可省略，也支持 `feat(api)!: 变更说明`。默认允许 `feat`、`fix`、`docs`、`style`、`refactor`、`perf`、`test`、`build`、`ci`、`chore`、`revert`，标题最多 100 个字符。校验集中在标题格式，不验证正文、footer 或不兼容变更说明是否完整。可参考 [提交模板](skills/git_helper/assets/commit-message.txt)，填写后删除无关段落；程序不会自动安装 Git 提交模板。

### 3. 推送与拉取

先确认远程地址；若尚无 origin，可手动配置，替换示例中的所有者和仓库名：

```powershell
git remote add origin https://github.com/OWNER/REPOSITORY.git
python skills/git_helper/scripts/git_helper.py push
python skills/git_helper/scripts/git_helper.py pull
```

`push` 推送当前 HEAD 到 `origin` 的同名 feature 分支。首次推送成功后设置 upstream，随后才能按默认规则拉取。`pull` 只整合同名远程分支，不会自动更新主分支或把主分支合入 feature 分支。远程分叉、认证失败或网络错误时停止，由用户和 Codex决定后续操作。项目不提供 GitHub 仓库创建功能。

### 4. 查看已有冲突

```powershell
python skills/git_helper/scripts/git_helper.py conflicts
```

该命令查看已有的索引冲突，不主动执行 merge 或 rebase。向 Codex 说明选择的方案后，再按 [冲突处理流程](skills/git_helper/references/conflicts.md) 处理。普通 merge 与 rebase 中 ours/theirs 的含义可能不同，必须先确认上下文。

### 配置

默认读取 [config.json](skills/git_helper/config.json)：

```json
{
  "remote": "origin",
  "feature_pattern": "feature/[a-z0-9][a-z0-9._/-]*",
  "protected_branches": ["main", "master", "develop"],
  "commit_types": ["feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert"],
  "max_subject_length": 100
}
```

可复制并修改这份配置，再指定替代文件；程序不会自动合并配置，替代文件须包含全部字段：

```powershell
python skills/git_helper/scripts/git_helper.py --config "D:/config/git-helper.json" status
```

分支名除匹配正则外，还需通过 Git 自身的分支名称校验。保护规则只作用于本程序，不能阻止直接执行原生 Git 命令，也不会安装 hooks 或 GitHub 分支保护规则。

## 输入输出示例

以下为典型示例；提交哈希、路径、分支状态和 Git 提示会随环境变化。程序正常完成返回退出码 `0`，业务校验或 Git 操作失败返回 `1`；命令行参数错误通常由解析器返回 `2`。

### 查看状态

输入：

```powershell
python skills/git_helper/scripts/git_helper.py status
```

示例输出（尚未配置远程）：

```text
## feature/git-helper
```

### 拒绝不规范的提交说明

前提：当前处于 feature 分支，且没有进行中的合并操作。

```powershell
python skills/git_helper/scripts/git_helper.py commit -m "update code"
```

输出到标准错误，退出码为 `1`：

```text
停止：提交说明不符合 Conventional Commits 或标题过长
```

### 无冲突

```powershell
python skills/git_helper/scripts/git_helper.py conflicts
```

输出：

```text
没有未解决的索引冲突
```

### 已有文本冲突

输入同一个 `conflicts` 命令。对于内容分别为 `base`、`ours`、`theirs` 的普通合并冲突，输出结构如下（blob ID 和唯一编号为占位展示；冲突段额外缩进，避免文档触发提交时的冲突标记检查）：

```text
FILE 'a.txt'
WORKING:
    <<<<<<< HEAD
    ours
    =======
    theirs
    >>>>>>> main

STAGE 1 mode=100644 blob=<base-blob-id>
base

STAGE 2 mode=100644 blob=<ours-blob-id>
ours

STAGE 3 mode=100644 blob=<theirs-blob-id>
theirs

备份：<Git私有目录>/git-helper-backups/<唯一编号>
选项：保留当前侧 / 保留传入侧 / 人工组合 / 暂不处理。先展示候选代码并由用户选择。
```

此时工作区和索引保持原样。程序不会等待键盘选择，也不会自动修改文件或完成合并。

## 项目结构

```text
skills/git_helper/
├── SKILL.md                    # Codex 协作指令、入口和流程
├── agents/openai.yaml          # Skill 显示信息
├── config.json                 # 默认配置
├── scripts/git_helper.py       # 主程序，内含冲突展示与备份逻辑
├── references/conflicts.md     # 人工选择与安全处理流程
└── assets/commit-message.txt   # 提交说明模板
```
