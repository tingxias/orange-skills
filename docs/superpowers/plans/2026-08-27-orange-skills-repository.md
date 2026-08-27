# orange-skills Repository Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有单 Skill 仓库迁移为名为 `orange-skills` 的多 Skill 仓库，并让 GitHub 与 Gitea 的 `master` 保持同一提交。

**Architecture:** 仓库根目录只承载说明、测试和设计资料，所有可安装 Skill 放在 `skills/<skill-name>/`。现有 `daily-report` 原样迁入 `skills/daily-report/`，用仓库结构测试和现有行为测试共同守护迁移；远端改名在本地验证完成后执行。

**Tech Stack:** Markdown、Python 3 `unittest`、Git、GitHub CLI、Gitea Web UI

**Spec:** `docs/superpowers/specs/2026-08-27-orange-skills-repository-design.md`

## Global Constraints

- 唯一本地源码工作区是 `/Users/a1234/Documents/personal/project/github/orange-skills`。
- 默认分支保持 `master`。
- GitHub 最终地址是 `https://github.com/tingxias/orange-skills`。
- Gitea 最终地址是 `ssh://git@gitea.lehuicheng.top:19109/yonyou/orange-skills.git`。
- 不修改 `/Users/a1234/.cc-switch/` 下的配置、数据库、Skill 安装副本或备份。
- 不修改 `/Users/a1234/.codex/skills/daily-report` 符号链接。
- 不修改旧 Rust 项目 `/Users/a1234/Documents/personal/project/gitea/daily_report`。
- 不恢复 Producer/Consumer、中间服务、Rust 服务或数据库链路。
- 不输出、写入或提交任何令牌、密码、数据库连接串或 MCP 凭据。

---

### Task 1: 建立多 Skill 仓库结构

**Files:**
- Create: `tests/test_repository_layout.py`
- Create: `README.md`
- Move: `SKILL.md` → `skills/daily-report/SKILL.md`
- Move: `agents/openai.yaml` → `skills/daily-report/agents/openai.yaml`
- Move: `references/workflow-config.md` → `skills/daily-report/references/workflow-config.md`
- Move: `scripts/test_siyuan_workflow.py` → `skills/daily-report/scripts/test_siyuan_workflow.py`
- Move: `scripts/test_skill_locale.py` → `skills/daily-report/scripts/test_skill_locale.py`
- Preserve: `.gitignore`

**Interfaces:**
- Consumes: 当前根目录单 Skill 结构，以及 `SKILL.md` 的 YAML `name: daily-report`。
- Produces: `skills/<skill-name>/SKILL.md` 仓库约定；每个 Skill 目录名必须与 frontmatter `name` 一致。

- [ ] **Step 1: 写入失败的仓库结构测试**

创建 `tests/test_repository_layout.py`：

```python
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"


class RepositoryLayoutTests(unittest.TestCase):
    def test_repository_root_is_not_an_installable_skill(self):
        self.assertFalse((ROOT / "SKILL.md").exists())
        self.assertTrue((ROOT / "README.md").is_file())

    def test_each_skill_has_matching_directory_and_frontmatter_name(self):
        skill_dirs = sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir())
        self.assertEqual([path.name for path in skill_dirs], ["daily-report"])

        for skill_dir in skill_dirs:
            skill_file = skill_dir / "SKILL.md"
            self.assertTrue(skill_file.is_file(), skill_file)
            text = skill_file.read_text(encoding="utf-8")
            match = re.search(r"(?m)^name:\s*([a-z0-9-]+)\s*$", text)
            self.assertIsNotNone(match, skill_file)
            self.assertEqual(match.group(1), skill_dir.name)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试并确认它因旧结构失败**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Expected: FAIL；至少包含根目录仍存在 `SKILL.md`，或 `skills/` 不存在导致的失败。

- [ ] **Step 3: 使用 Git 移动现有 Skill 文件**

Run:

```bash
mkdir -p skills/daily-report
git mv SKILL.md agents references scripts skills/daily-report/
```

Expected: `git status --short` 将原文件显示为移动到 `skills/daily-report/`；根目录 `.gitignore` 保持不动。

- [ ] **Step 4: 创建根目录 README**

创建 `README.md`，内容如下：

````markdown
# orange-skills

个人 Codex Skills 集合。仓库根目录不直接作为 Skill 安装，所有 Skill 位于 `skills/` 下。

## Skills

- `daily-report`：按明确日期通过思源 MCP 推送、查询、获取、追加或修改个人日报；仅在用户明确要求时进入公司系统写入或提交阶段。

## 目录约定

每个 Skill 使用独立目录：

```text
skills/<skill-name>/
├── SKILL.md
├── agents/
├── references/
└── scripts/
```

目录名必须与 `SKILL.md` frontmatter 中的 `name` 一致。只创建该 Skill 实际需要的子目录，不在 Skill 之间使用隐式相对路径依赖。

## 校验

```bash
python3 /Users/a1234/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/daily-report
python3 -m unittest discover -s skills/daily-report/scripts -p 'test_*.py' -v
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## CC Switch

添加此仓库时手动使用以下配置：

- Owner：`tingxias`
- Name：`orange-skills`
- Branch：`master`
- Subdirectory：`skills`

CC Switch 配置及本地安装副本不由本仓库自动修改。
````

- [ ] **Step 5: 运行仓库结构测试并确认通过**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Expected: 2 tests，全部 PASS。

- [ ] **Step 6: 运行 Skill 官方校验与现有行为测试**

Run:

```bash
python3 /Users/a1234/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/daily-report
python3 -m unittest discover -s skills/daily-report/scripts -p 'test_*.py' -v
```

Expected: `Skill is valid!`；现有 12 项测试全部 PASS。

- [ ] **Step 7: 检查迁移范围和敏感信息**

Run:

```bash
git diff --check
git status --short
find skills -mindepth 1 -maxdepth 1 -type d -print
rg -n --hidden -g '!.git/**' 'postgres(ql)?://[^[:space:]]+:[^@[:space:]]+@|Authorization:[[:space:]]*Bearer[[:space:]]+[A-Za-z0-9._-]{12,}|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY|admin1234' .
```

Expected:

- `git diff --check` 无输出。
- `find` 只输出 `skills/daily-report`。
- 敏感信息扫描无输出；如果命中，停止提交并移除真实凭据后重新运行。
- `git status --short` 只包含本任务的 README、测试和文件移动。

- [ ] **Step 8: 提交目录迁移**

Run:

```bash
git add README.md tests skills .gitignore
git commit -m "refactor: 调整为多 Skill 仓库结构"
```

Expected: 新提交包含 README、仓库结构测试和 `daily-report` 文件移动，不包含 CC Switch 或旧 Rust 项目文件。

---

### Task 2: 重命名 GitHub 与 Gitea 仓库

**Files:**
- Modify external state: GitHub repository `tingxias/daily-report`
- Modify external state: Gitea repository `yonyou/daily-report`
- Modify local-only Git config: `.git/config`

**Interfaces:**
- Consumes: Task 1 已验证但尚未推送的本地 `master`。
- Produces: GitHub `tingxias/orange-skills`、Gitea `yonyou/orange-skills`，以及本地 `origin`/`gitea` 远端配置。

- [ ] **Step 1: 记录改名前的远端基线**

Run:

```bash
git status --short --branch
git rev-parse HEAD
git ls-remote https://github.com/tingxias/daily-report.git refs/heads/master
git ls-remote ssh://git@gitea.lehuicheng.top:19109/yonyou/daily-report.git refs/heads/master
```

Expected:

- 工作区干净，本地 `master` 领先旧远端。
- 两个旧远端改名前的 `master` 都是 `95545e6f39b84f872f1f26324dbceb7ec767686f`。

- [ ] **Step 2: 重命名 GitHub 仓库**

Run:

```bash
gh repo rename orange-skills --repo tingxias/daily-report --yes
git remote set-url origin https://github.com/tingxias/orange-skills.git
git ls-remote origin refs/heads/master
```

Expected: `origin` 可访问，`refs/heads/master` 仍指向改名前的远端提交；GitHub 仓库显示为 `tingxias/orange-skills`。

- [ ] **Step 3: 通过 Gitea 已登录页面重命名仓库**

使用浏览器打开：

```text
https://gitea.lehuicheng.top/yonyou/daily-report/settings
```

在仓库设置中把仓库名称从 `daily-report` 改为 `orange-skills`，保存后打开：

```text
https://gitea.lehuicheng.top/yonyou/orange-skills
```

Expected: 新地址显示原仓库和原提交历史。若浏览器未登录或当前账号无管理权限，停止此步骤并请用户完成登录/授权；不得使用服务器 root 密码、SSH Git 凭据或新建分叉仓库代替改名。

- [ ] **Step 4: 配置并验证 Gitea 远端**

Run:

```bash
if git remote get-url gitea >/dev/null 2>&1; then
  git remote set-url gitea ssh://git@gitea.lehuicheng.top:19109/yonyou/orange-skills.git
else
  git remote add gitea ssh://git@gitea.lehuicheng.top:19109/yonyou/orange-skills.git
fi
git remote -v
git ls-remote gitea refs/heads/master
```

Expected:

- `origin` 只指向 GitHub `orange-skills`。
- `gitea` 只指向 Gitea `orange-skills`。
- Gitea `master` 仍指向改名前的远端提交。

---

### Task 3: 推送并完成双远端一致性验证

**Files:**
- Verify: `README.md`
- Verify: `skills/daily-report/`
- Verify: `tests/test_repository_layout.py`
- Verify unchanged external paths: `/Users/a1234/.cc-switch/skills/daily-report`
- Verify unchanged external paths: `/Users/a1234/.codex/skills/daily-report`
- Verify unchanged external repository: `/Users/a1234/Documents/personal/project/gitea/daily_report`

**Interfaces:**
- Consumes: Task 1 的迁移提交和 Task 2 的两个新远端。
- Produces: GitHub 与 Gitea 的 `master` 均指向本地 `HEAD`，本地工作区干净。

- [ ] **Step 1: 推送前重新运行全部本地验证**

Run:

```bash
python3 /Users/a1234/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/daily-report
python3 -m unittest discover -s skills/daily-report/scripts -p 'test_*.py' -v
python3 -m unittest discover -s tests -p 'test_*.py' -v
git diff --check
git status --short --branch
```

Expected: Skill 校验通过，12 项 Skill 测试和 2 项仓库结构测试全部 PASS，无 diff 错误，工作区干净且本地 `master` 领先远端。

- [ ] **Step 2: 推送同一提交到两个远端**

Run:

```bash
git push origin master
git push gitea master
```

Expected: 两次推送均成功；不强推，不创建第二条历史。

- [ ] **Step 3: 核对本地、GitHub 与 Gitea 提交完全一致**

Run:

```bash
local_head=$(git rev-parse HEAD)
github_head=$(git ls-remote origin refs/heads/master | awk '{print $1}')
gitea_head=$(git ls-remote gitea refs/heads/master | awk '{print $1}')
printf 'local=%s\ngithub=%s\ngitea=%s\n' "$local_head" "$github_head" "$gitea_head"
test "$local_head" = "$github_head"
test "$local_head" = "$gitea_head"
```

Expected: 三行提交哈希完全相同，两个 `test` 命令都返回 0。

- [ ] **Step 4: 核对明确排除的本地对象未被修改**

Run:

```bash
test "$(readlink /Users/a1234/.codex/skills/daily-report)" = "/Users/a1234/.cc-switch/skills/daily-report"
git -C /Users/a1234/Documents/personal/project/gitea/daily_report status --short --branch
git status --short --branch
```

Expected:

- Codex Skill 链接仍指向 CC Switch 管理目录。
- 旧 Rust 仓库仍保留其原有状态；本次实施不新增或修改其中任何文件。
- `orange-skills` 工作区干净，并跟踪新的 GitHub `origin/master`。

- [ ] **Step 5: 报告完成结果**

最终报告必须包含：

- 本地源码绝对路径。
- 最终提交哈希。
- Skill 校验结果及测试数量。
- GitHub 与 Gitea 的新仓库地址。
- 两个远端 `master` 哈希一致的验证结果。
- 明确说明 CC Switch 未修改，需要用户按 README 手动配置并刷新。
