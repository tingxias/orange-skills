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
