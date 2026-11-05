# Idea Triage

一个给 Codex 和 Claude Code 使用的技能。把想法推进到可以决定要投入多少的程度。它先澄清目标，再查现成方案和关键证据，给出推荐、投入量级和最小验证。复杂想法可以保存评估、用户决定与复审条件。

## 安装

下载或克隆本仓库。在你要评估想法的项目目录里，按客户端选择一条命令。将示例中的源路径换成下载位置。

```sh
# Codex
mkdir -p .agents/skills
cp -R "/path/to/download/idea-triage" .agents/skills/

# Claude Code
mkdir -p .claude/skills
cp -R "/path/to/download/idea-triage" .claude/skills/
```

也可以分别放进用户级 `~/.agents/skills/` 与 `~/.claude/skills/`。已有同名技能时先确认客户端要加载哪一份，再更新。开启项目对话后，在 Codex 输入 `$idea-triage`，在 Claude Code 输入 `/idea-triage`，也可以直接用自然语言描述任务。

基本对话随客户端运行。需要保存正式评估状态时，使用 Python 3.9+ 和标准库 SQLite。可在终端运行 `python3 -c "import sqlite3; print(sqlite3.sqlite_version)"` 核实。是否能联网查证由客户端和当前授权决定。

从旧版更新时，请整套更新 `idea-triage/`，让模板和脚本来自同一个版本。旧脚本会忽略新报告中的 `track-v1` 和成本字段，仍用原权重算分。更新后的脚本会按原口径读取未标版本的报告，已有报告和项目状态可以保留。

## 从一句话开始

- 「先记一下这个想法，今天只登记，等我下次回来再评估。」
- 「帮我评估是否值得做。先查能复用的方案，给我结论、一项最小验证和建议投入。」
- 「按更新后的需求复审。列出要重验的条件，再给我阶段建议。」

正式报告分列想法潜力、下一阶段投入价值和本步成本效益。按自用、商用、小众或研究选用[评分口径](idea-triage/references/dimensions.md)，说明证据、关键阻断和提档条件。复评记录分数变化的依据及推进建议是否改变。证据不足时给暂定建议。正式报告可以留档，项目决定在用户确认后生效。用户明确要求时，可以在当前可写范围做验证关键假设的小样。

## 试跑

```sh
python3 idea-triage/scripts/triage.py tier example-verdict.md
```

示例中的评估和日期是合成输入。项目内状态存于 `.idea-triage/state.sqlite3`，应加入实际使用项目的忽略规则。证据和报告保留为 Markdown。写入、复审及备份命令见[阶段复审](idea-triage/references/stage-gate-review.md)。

[Codex 技能文档](https://learn.chatgpt.com/docs/build-skills) · [Claude Code 技能文档](https://code.claude.com/docs/en/skills) · [来源](SOURCES.md) · [MIT](LICENSE)
