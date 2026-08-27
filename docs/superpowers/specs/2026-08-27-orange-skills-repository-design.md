# orange-skills 多 Skill 仓库设计

## 背景

当前 `daily-report` 仓库的根目录本身就是一个 Skill，只适合承载单个 Skill。后续还会开发新的 Skill，因此需要将仓库调整为可被 CC Switch 按子目录发现的多 Skill 仓库，并把仓库与独立本地源码目录统一命名为 `orange-skills`。

现有 GitHub 与 Gitea 仓库的 `master` 分支均指向提交 `95545e6`。本机 `/Users/a1234/.cc-switch/skills/daily-report` 是 CC Switch 管理的安装副本，`/Users/a1234/.codex/skills/daily-report` 是指向该副本的符号链接，两者都不作为源码工作区。

## 目标

1. 将 GitHub 和 Gitea 仓库都从 `daily-report` 改名为 `orange-skills`，保留完整 Git 历史。
2. 使用 `/Users/a1234/Documents/personal/project/github/orange-skills` 作为唯一的本地源码工作区。
3. 将现有 `daily-report` Skill 移入 `skills/daily-report/`。
4. 为后续新增 Skill 建立统一、可发现、可独立校验的目录约定。
5. 保持 `daily-report` Skill 的行为、中文内容和测试结果不变。

## 非目标

- 不修改 CC Switch 的仓库配置、数据库或安装副本；这些操作由用户自行完成。
- 不修改 `/Users/a1234/.codex/skills/daily-report` 符号链接。
- 不恢复旧 Producer/Consumer、中间服务、Rust 服务或数据库逻辑。
- 不在本次迁移中创建新的业务 Skill。
- 不改动旧 Rust 项目 `/Users/a1234/Documents/personal/project/gitea/daily_report`。

## 目录结构

迁移完成后的结构为：

```text
orange-skills/
├── README.md
├── docs/
│   └── superpowers/
│       ├── plans/
│       └── specs/
└── skills/
    └── daily-report/
        ├── SKILL.md
        ├── agents/
        │   └── openai.yaml
        ├── references/
        │   └── workflow-config.md
        └── scripts/
            ├── test_siyuan_workflow.py
            └── test_skill_locale.py
```

后续每个 Skill 使用独立目录 `skills/<skill-name>/`，其名称必须与 `SKILL.md` 的 `name` 一致。Skill 私有的脚本、引用和资源只放在自己的目录内，不在不同 Skill 之间建立隐式相对路径依赖。

## 仓库与远端

迁移后使用以下远端：

- GitHub：`https://github.com/tingxias/orange-skills`
- Gitea：`ssh://git@gitea.lehuicheng.top:19109/yonyou/orange-skills.git`
- 默认分支：`master`

本地 Git 远端命名约定：

- `origin` 指向 GitHub。
- `gitea` 指向 Gitea。

两个远端必须推送同一个 `master` 提交。远端改名完成后，更新本地 URL，并通过 `git ls-remote` 与提交哈希核对两端一致。

## README 内容

根目录 `README.md` 说明：

- 仓库用途和目录约定。
- 当前包含的 Skill 列表。
- 新增 Skill 时的最小文件要求和校验方式。
- CC Switch 手动配置参考值：Owner `tingxias`、Name `orange-skills`、Branch `master`、Subdirectory `skills`。

README 只提供说明，不自动修改 CC Switch。

## 迁移方法

迁移使用 Git 感知的移动操作，将根目录下的 Skill 文件整体移入 `skills/daily-report/`。保留现有文件内容，随后只调整因目录层级改变而失效的测试路径或仓库级说明。

设计文档和后续实施计划保留在仓库根目录的 `docs/superpowers/` 下，不放进具体 Skill，以免被 CC Switch 当成 Skill 内容安装。

## 验证

迁移必须完成以下验证：

1. 对 `skills/daily-report/` 运行官方 `quick_validate.py`。
2. 从 `skills/daily-report/scripts/` 运行现有单元测试，确认全部通过。
3. 检查 `skills/` 下一层仅有合法 Skill 目录，且每个目录都含 `SKILL.md`。
4. 检查仓库中不存在旧 Producer/Consumer Key、中间服务或真实凭据。
5. 检查 GitHub 与 Gitea 的 `master` 指向相同提交。
6. 检查旧 Rust 工作区、CC Switch 安装副本和 Codex 符号链接均未被修改。

CC Switch 的实际刷新和发现验证由用户在手动修改配置后执行，不作为本次自动实施的完成条件。

## 异常处理与回退

- 任一远端改名失败时，停止更新本地远端 URL，不删除旧仓库，也不创建内容分叉的新仓库。
- 目录迁移或测试失败时，不推送迁移提交；在本地修复并重新完成全部验证。
- 一个远端推送成功而另一个失败时，保留已推送提交，修复连接后将同一提交补推到另一端，不生成不同历史。
- CC Switch 因尚未手动改配置而继续使用旧安装副本属于预期状态，不回写其配置。

## 完成标准

- 本地源码位于 `/Users/a1234/Documents/personal/project/github/orange-skills`。
- 仓库根目录不再直接充当 Skill，`daily-report` 位于 `skills/daily-report/`。
- GitHub 与 Gitea 仓库均命名为 `orange-skills`，且 `master` 提交一致。
- Skill 校验和现有测试全部通过。
- 仓库未包含凭据，旧 Rust 项目和 CC Switch 管理目录未被修改。
