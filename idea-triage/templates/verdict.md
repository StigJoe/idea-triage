<!-- DIRECTION-VERDICT v1 -->
<!-- ⚠️ 这个注释头 + 下面的键值块是**机器契约**,不是排版说明。
     它由 `<!--` 起、由第一条 `---` 止;评分工具只解析这一段。
     键名/缩进照抄,别改:改了 tier 就 rc=1。
     所有键**顶格**;rubric / outlook / conditions 三个块的子项**缩进 2 格**。 -->
knowledge_cutoff: <YYYY-MM;我的知识截止,不是今天>
networked: <yes/no（检索至 YYYY-MM-DD）—— no 会被拒收为正式 verdict>
reviewer: <谁做的判定:外部模型名 / 主会话 —— 执行者≠评审者>
date: <YYYY-MM-DD>
idea_type: <market / self_use / niche / research —— 必填,决定六维口径>
rubric:
  demand: <1-10>
  supply_gap: <1-10>
  competitor_traction: <1-10>
  segment_crowding: <1-10>
  feasibility: <1-10>
  my_edge: <1-10>
outlook:
  durability: <1-10>
  compounding: <1-10>
  ceiling: <1-10>
  moat_vs_general: <1-10>
  alignment: <1-10>
verdict: <go / conditional-go / pivot / kill>
pivot_to: <判定为 pivot 时写具体转向，其他判定可省略>
rank_note: 在档 <N> 条里排第 <K>；值不值得投入时间（不许每条都说「值得」）
time_budget: <小时 / 天 / 周 / 月>（量级；不给量级等于没给建议）
next_wall: <W1–W8 下一个会撞的墙 + 一句说明>
conditions:
  - id: C1
    deadline: "<YYYY-MM-DD>"
    requirement: "<要验的具体动作>"
steelman_kill: |
  最强反方:<把对手/怀疑者的最强论证写成一行,别写成稻草人>
self_doubt: |
  若我错,最可能错在:<一句>
---

# <想法> · 评估结论

- 结论：<方向和理由>
- 需求及证据：<当前版本、来源、能与不能验证>
- 投入：<时间或成本、比较范围、分层及理由>
- 推荐路线：<复用、最小试验、继续、转向或收手>
- 下一步及结束条件：<可验结果、条件、期限、缺口>
- 用户决定：<如已有明确决定则记录来源，评估本身仅给建议>

## 关键证据

- [一手资料] <会影响建议的主张> | [来源](<URL:直接网页链接或相对项目文件>) | <来源支持到哪一步、仍缺什么>
- 改判条件：<哪项发现或失败会改变建议，以及改成什么>

## 补充说明

按需补方案差异、反方证据、复查记录。头块供工具读取，正文供人读。
