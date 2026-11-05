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

- 推荐：<适用路线，如自用、商用验证、打磨、转向或收手；当前具体下一步和理由>
- 下一步及停止条件：<可验结果、所需投入、期限、失败后动作>
- 证据可信度：<高／中／低、主要依据和局限>
- 关键阻断：<阻断哪项行动、怎样验证通过；无则说明核对过什么>
- 用户决定：<如已有明确决定则记录来源，评估本身仅给建议>

## 评分与提档

独立版正式报告在头块 `idea_type` 后加入 `score_profile: track-v1`、`cost_affordability: <0–10 或 unknown>`、`cost_payoff: <0–10 或 unknown>`，每个字段单独一行并填实际值。正文用 [评分口径](../references/dimensions.md) 和工具结果填写下表。

| 评分 | 分数与档位 | 影响最大的证据或未知 | 可验证的提档条件 |
|---|---|---|---|
| 想法潜力 | <outlook> | <做成后的价值和使用周期> | <什么结果会改变潜力判断> |
| 下一阶段投入价值 | <direction> | <当前证据、竞争和执行优势> | <什么结果支持扩大投入> |
| 本步成本效益 | <cost_effectiveness 或待验证> | <动作、对照基线、周期、成本及预期收益> | <可观察的收益或成本边界> |

按需加专项分或给有依据的情景区间。复评列上轮标识、同口径分差和新证据，并说明推荐是否变化。换了目标、赛道或待评步骤时，标出不可直接比较的项。

## 关键证据

- [一手资料] <会影响建议的主张> | [来源](<URL:直接网页链接或相对项目文件>) | <来源支持到哪一步、仍缺什么>
- 改判条件：<哪项发现或失败会改变建议，以及改成什么>

## 补充说明

按需补方案差异、反方证据、复查记录。头块供工具读取，正文供人读。

- 建议进入规格或建设时，附该范围的问题、证据、推荐方案与验收，列出交接仍需解决的事项。
- 暂定或有条件继续时，注明阻断项、补证入口和重新判断的条件。
