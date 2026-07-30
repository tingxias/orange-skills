# 日报默认凭据与项目范围实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 已保存的角色 Key 自动使用，生成周报默认读取本周全部可见项目，非汇总命令不再询问项目目录。

**Architecture:** 保持现有服务、客户端和配置文件契约不变，只收紧 Skill 的交互规则。用静态行为测试锁定凭据自动读取、默认全项目以及领取和回执不询问项目范围。

**Tech Stack:** Markdown Skill、Python `unittest`、Skill validator、Git

## Global Constraints

- 首次使用或对应角色 Key 未配置时才询问完整 Key。
- 已保存的当前角色 Key 自动读取，禁止输出 Key、租约令牌和公司系统凭据。
- 本周工作总结默认读取当前工具可见的全部项目并使用 `scope.mode=all`。
- 只有用户主动指定项目时使用 `scope.mode=whitelist`。
- `fetch`、`complete`、`fail`、`get`、`list`、`append` 和 `modify` 不询问项目目录。
- 不修改 Rust 服务、HTTP 契约、Python 客户端配置格式或租约状态机。

---

### Task 1: 简化凭据与项目范围交互

**Files:**
- Modify: `scripts/test_skill_locale.py:20-48`
- Modify: `SKILL.md:10-71`
- Modify: `SKILL.md:93-170`

**Interfaces:**
- Consumes: `~/.config/daily-report/config.json` 或对应环境变量中的现有角色 Key。
- Produces: 未来 Skill 调用遵循默认凭据和默认项目范围规则；服务及客户端接口不变。

- [ ] **Step 1: 写入失败的静态行为测试**

将旧的逐次授权和范围询问断言替换为以下约束：

```python
self.assertIn("首次使用或对应角色 Key 未配置时", skill)
self.assertIn("直接读取并使用", skill)
self.assertIn("不再要求逐次授权", skill)
self.assertNotIn("使用默认范围（本周全部项目），还是指定项目？", skill)
self.assertIn("默认读取当前工具可见的全部项目", skill)
self.assertIn("不询问目录范围", skill)
self.assertIn("执行这些命令时不得询问同步目录或项目范围", skill)
```

- [ ] **Step 2: 运行测试并确认旧 Skill 失败**

Run: `python3 -m unittest test_skill_locale.SkillLocaleTests.test_skill_guidance_and_ui_metadata_are_chinese -v`

Working directory: `scripts`

Expected: FAIL，因为旧 Skill 仍要求后续使用逐次授权并询问默认或指定项目。

- [ ] **Step 3: 更新 Skill 交互规则**

在 `SKILL.md` 中明确：

```markdown
首次使用或当前命令所需角色 Key 未配置时，才要求用户输入完整 Key。配置文件或环境变量已有对应角色 Key 时，直接读取并使用，不再要求逐次授权。
```

项目汇总规则改为：

```markdown
默认读取当前工具可见的全部项目及其本周任务，不询问目录范围。只有用户在当前请求中主动指定项目名称或路径时，才限制为对应项目。
```

获取与其他非汇总命令增加：

```markdown
`fetch`、`complete`、`fail`、`get`、`list`、`append` 和 `modify` 不读取项目任务；执行这些命令时不得询问同步目录或项目范围。
```

发送、查询、修改、获取和认证错误说明统一改为“使用已配置 Key；缺失或失效时再请求更新”，同时保留密钥不输出、不记录、不入 Git 的限制。

- [ ] **Step 4: 运行目标测试与完整测试**

Run: `python3 -m unittest test_skill_locale.SkillLocaleTests.test_skill_guidance_and_ui_metadata_are_chinese -v`

Working directory: `scripts`

Expected: PASS

Run: `python3 -m unittest discover -s scripts -p 'test_*.py' -v`

Expected: 16 tests PASS。

- [ ] **Step 5: 校验 Skill 和差异**

Run: `python3 /Users/a1234/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/a1234/.codex/skills/daily-report`

Expected: `Skill is valid!`。如果系统 Python 缺少 PyYAML，只在临时目录安装并通过 `PYTHONPATH` 运行，不修改全局环境。

Run: `git diff --check`

Expected: exit 0。

- [ ] **Step 6: 提交并推送**

```bash
git add SKILL.md scripts/test_skill_locale.py docs/superpowers/plans/2026-07-30-default-credential-and-project-scope.md
git commit -m "简化日报凭据与项目范围确认"
git push origin master
```

最后确认 `git rev-parse HEAD` 与 `git ls-remote origin refs/heads/master` 相同。
