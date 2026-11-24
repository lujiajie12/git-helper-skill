# 用 Git规范协作助手完成一次文档 PR

本示例演示真实的分支、提交、推送和 PR 合并流程。Skill 提供本地 Git 检查；GitHub CLI 负责 PR 创建与合并，需要另行安装并登录。

## 开始前

确认当前仓库的 `origin`、工作区和分支状态。在最新且干净的 `main` 上开始；需要同步时先执行 `git pull --ff-only origin main`。Skill 的拉取命令限定 feature 分支，不能用它直接同步 main。

```powershell
python skills/git_helper/scripts/git_helper.py status
python skills/git_helper/scripts/git_helper.py branch feature/docs-pr-workflow
```

默认配置只允许 `feature/...`，文档分支可使用 `feature/docs-主题`；`docs/...` 不符合默认分支规则。提交类型与分支前缀分别检查，文档修改使用 `docs` 提交类型。

## 修改、审阅和提交

编辑本文件或其他实际文档后，审阅具体变更，只暂存本次相关文件：

```powershell
git diff -- docs/pr-workflow.md
git add -- docs/pr-workflow.md
git diff --cached --check
git diff --cached
python skills/git_helper/scripts/git_helper.py commit -m "docs(workflow): 添加 Skill 协作演练指南"
python skills/git_helper/scripts/git_helper.py push
```

新文件在暂存前不会出现在普通 `git diff` 中，应直接阅读文件，并在暂存后检查完整 diff。Skill 不自动暂存文件；推送要求工作区干净，成功后设置同名远程分支的 upstream。

## 创建并合并 PR

只有用户授权发布和合并后，才执行以下操作。先创建 PR，再审阅文件和检查结果；有冲突或检查失败时停止，不强制合并。

```powershell
gh pr create --base main --head feature/docs-pr-workflow --title "docs(workflow): 添加 Skill 协作演练指南" --body "记录通过 Skill 建分支、提交、推送及使用 GitHub CLI 合并 PR 的流程。"
gh pr diff
gh pr view --json url,state,mergeable,statusCheckRollup
gh pr merge --merge
```

仓库没有配置 CI 时，没有检查结果不代表执行过自动化测试。不要使用管理员绕过选项。需要人工审查或分支保护审批时，保留 PR 等待完成。

## 同步并验证主分支

```powershell
git switch main
git pull --ff-only origin main
python skills/git_helper/scripts/git_helper.py status
```

核对 PR 状态为 MERGED，新增文档出现在远程 main，本地主分支与 origin/main 一致且工作区干净。分支名仅为演示，重复演练时应换一个未使用的名称。
