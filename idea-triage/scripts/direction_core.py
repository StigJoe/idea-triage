"""Portable scoring contract. Generated from the maintained direction scorer."""

import io
import re
from datetime import date

RUBRIC_PATH = "references/dimensions.md"
OUTLOOK_RUBRIC_PATH = "references/dimensions.md"

WEIGHTS = {"demand": 25, "supply_gap": 15, "competitor_traction": 20,
           "segment_crowding": 10, "feasibility": 15, "my_edge": 15}


VERDICTS = {"go", "conditional-go", "pivot", "kill"}


TOPKEYS = ("knowledge_cutoff", "networked", "reviewer", "date", "verdict", "idea_type")


CALIBRATION = "provisional"


CUTOFFS = ((75, "go"), (60, "conditional-go"), (40, "pivot"))


BAND_MARGIN = 5


IDEA_TYPES = ("market", "self_use", "niche", "research")


OUTLOOK_WEIGHTS = {"durability": 20, "compounding": 25, "ceiling": 15,
                   "moat_vs_general": 25, "alignment": 15}


OUTLOOK_CUTOFFS = (70, 40)


def parse(path):
    """解析 DIRECTION-VERDICT.md 头块（缩进式 key: value，stdlib 无 yaml 依赖）"""
    d = {"rubric": {}, "outlook": {}, "conditions": [], "steelman_kill": "", "self_doubt": "", "_errors": []}
    cur_block = None
    seen_keys = set()
    fence_seen = False
    for raw in io.open(path, encoding="utf-8").read().splitlines():
        if not raw.strip() or raw.lstrip().startswith("<!--"):
            continue
        line = raw.rstrip()
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())



        if stripped in ("---", "..."):
            if fence_seen or seen_keys:
                break
            fence_seen = True
            continue
        if indent == 0 and ":" in stripped:
            key = stripped.split(":", 1)[0].strip()
            if key in seen_keys:
                d["_errors"].append("重复字段: %s" % key)
            seen_keys.add(key)
        if indent == 0 and stripped.endswith(":") and stripped[:-1] in ("rubric", "outlook", "conditions"):
            cur_block = stripped[:-1]
            if cur_block == "outlook":
                d["_outlook_present"] = True
            continue
        if indent == 0 and (stripped.endswith("|") or stripped.endswith(">")):
            cur_block = stripped.split(":")[0].strip()
            if cur_block in ("rubric", "outlook", "conditions"):
                d["_errors"].append("%s 必须使用缩进结构，不能是文本块" % cur_block)
            d.setdefault(cur_block, "")
            continue
        if indent == 0 and ":" in stripped:
            k, v = stripped.split(":", 1)
            k = k.strip()
            if k in ("rubric", "outlook", "conditions"):
                d["_errors"].append("%s 必须使用缩进块，不能是行内值" % k)
            elif not k.startswith("_"):
                d[k] = v.strip().strip('"').strip("'")
            cur_block = None
            continue
        if cur_block in ("rubric", "outlook") and ":" in stripped:
            k, v = stripped.split(":", 1)
            if k.strip() in d[cur_block]:
                d["_errors"].append("重复维度: %s.%s" % (cur_block, k.strip()))
            m = re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)(?:\s+#.*)?\s*", v)
            if not m:
                d["_errors"].append("%s.%s 必须是数值（可附 # 注释）" % (cur_block, k.strip()))
            d[cur_block][k.strip()] = float(m.group(1)) if m else None
        elif cur_block == "conditions":





            if stripped.startswith("-"):
                d["conditions"].append(stripped.lstrip("-").strip())
            elif d["conditions"]:
                d["conditions"][-1] = (d["conditions"][-1] + " " + stripped).strip()
        elif cur_block in ("steelman_kill", "self_doubt"):
            d[cur_block] = (d.get(cur_block, "") + " " + stripped).strip()
    return d


def outlook_score(d):
    """第二轴总分 0-100。缺维 ⇒ (None, 缺的维名列表)；越界 ⇒ (None, 错误说明)。"""
    o = d.get("outlook") or {}
    missing = [k for k in OUTLOOK_WEIGHTS if k not in o]
    if missing:
        return None, ["缺前景维度: %s（口径见 %s）" % ("/".join(missing), OUTLOOK_RUBRIC_PATH)]
    bad = [k for k in OUTLOOK_WEIGHTS if not (isinstance(o[k], (int, float)) and 0 <= o[k] <= 10)]
    if bad:
        return None, ["前景维度取值须为 0-10 的数: %s" % "/".join(bad)]
    total = sum(o[k] / 10.0 * w for k, w in OUTLOOK_WEIGHTS.items())
    return round(total, 1), []


TIER_MATRIX = {
    ("go", "hi"): ("长期投入", "🟢 长期投入（核心资产）：给稳定时间预算，**允许建重资产**（数据库/基建/公开作品）"),
    ("go", "mid"): ("立项设收割点", "🔵 立项但设收割点：定一个「做到哪就停」的交付物，别无限延展"),
    ("go", "lo"): ("快做快收", "🟡 快做快收：短周期拿走结果，**不建重资产**（会被替代或一次性）"),
    ("conditional-go", "hi"): ("加投补条件", "🟢 加投把条件补齐：前景值得为它花代价（条件 + 到期日仍必填）"),
    ("conditional-go", "mid"): ("短期观察", "🟠 短期观察（随时可砍）：低成本探针，不排期、不建资产，到期未验即砍"),
    ("conditional-go", "lo"): ("砍掉", "🔴 砍掉：条件都满足了也不值得投"),
    ("pivot", "hi"): ("换方向", "🔁 换方向：核心洞察有价值但载体不对（须给 pivot_to，并对新对象**重跑两轴**）"),
    ("pivot", "mid"): ("换方向或降级", "🔁 换方向或降级为一条用法：优先「记成方法/用法」而不是做产品"),
    ("pivot", "lo"): ("砍掉", "🔴 砍掉"),
    ("kill", "hi"): ("归档待触发", "⏸️ 归档 + 记触发条件：现在不成立但前景分高 ⇒ 写明「什么前提变了就重估」，别彻底删"),
    ("kill", "mid"): ("砍掉", "🔴 砍掉"),
    ("kill", "lo"): ("砍掉", "🔴 砍掉"),
}


def _outlook_band(outlook):
    return "hi" if outlook >= OUTLOOK_CUTOFFS[0] else "mid" if outlook >= OUTLOOK_CUTOFFS[1] else "lo"


def investment_tier(band, outlook):
    """两轴合成 ⇒ (tier_id, advice)。band = 6 维那轴的档位。"""
    return TIER_MATRIX[(band, _outlook_band(outlook))]


OUTLOOK_REQUIRED_FIELDS = ("rank_note", "time_budget", "next_wall")


OUTLOOK_FIELD_HINT = {
    "rank_note": "一句话意见 + **在实际对比范围内排第几**（不许每条都说「值得」）",
    "time_budget": "时间预算量级（小时/天/周/月）——用户时间稀缺，不给量级等于没给建议",
    "next_wall": "撞墙点：继续做下去**下一个会撞的墙**是什么（缺数据/缺能力/缺钱/需求不存在/已被现成覆盖/会被通用能力吞掉）",
}


def outlook_errors(d):
    """前景轴的契约检查。没有 outlook 块 ⇒ 返回 []（向后兼容：旧格式仍可跑 6 维那轴）。"""
    o = d.get("outlook") or {}
    if not o and not d.get("_outlook_present"):
        return []
    errs = []
    _t, e = outlook_score(d)
    errs += e
    for k in OUTLOOK_REQUIRED_FIELDS:
        if not str(d.get(k, "")).strip():
            errs.append("有 outlook 块但缺 `%s`：%s" % (k, OUTLOOK_FIELD_HINT[k]))
    return errs


def implied_verdict(total):
    return "go" if total >= 75 else "conditional-go" if total >= 60 else "pivot" if total >= 40 else "kill"


def weighted_total(d):
    tot, miss = 0.0, []
    for k, w in WEIGHTS.items():
        v = d.get("rubric", {}).get(k)
        if v is None:
            miss.append(k)
        else:
            tot += max(0.0, min(10.0, float(v))) / 10 * w
    return round(tot, 1), miss


def validate(d):
    errs = list(d.get("_errors", []))
    for k in TOPKEYS:
        if not str(d.get(k, "")).strip():
            errs.append("缺 %s（时效/归属不可核 ⇒ 拒收）" % k)
    if d.get("verdict") and d["verdict"] not in VERDICTS:
        errs.append("verdict 非法: %s（须 ∈ %s）" % (d["verdict"], "/".join(sorted(VERDICTS))))
    it = str(d.get("idea_type", "")).strip()
    if it and it not in IDEA_TYPES:
        errs.append("idea_type 非法: %s（须 ∈ %s）——没有它就无法选六维口径" % (it, "/".join(IDEA_TYPES)))
    if d.get("date") and not valid_date(d["date"]):
        errs.append("date 必须为有效日期 YYYY-MM-DD")
    if "|" in str(d.get("reviewer", "")):
        errs.append("reviewer 不得含台账分隔符 |")
    _, miss = weighted_total(d)
    for k in miss:
        errs.append("rubric 缺维度 %s（权重 %d）" % (k, WEIGHTS[k]))
    for k, v in d.get("rubric", {}).items():
        if v is not None and not (0 <= v <= 10):
            errs.append("rubric.%s=%s 越界（0-10）" % (k, v))
    if len(d.get("steelman_kill", "")) < 40:
        errs.append("steelman_kill 缺失或过短(<40字)：没有最强反方论证=不可信")
    if len(d.get("self_doubt", "")) < 20:
        errs.append("self_doubt 缺失或过短(<20字)：未说明若错最可能错在哪")
    if d.get("verdict") == "conditional-go":
        cs = d.get("conditions", [])
        if not cs:
            errs.append("conditional-go 必须列 conditions（含到期日）")
    for c in d.get("conditions", []):
        due = re.search(r"\d{4}-\d{2}-\d{2}", c)
        if not due:
            errs.append("condition 缺到期日 YYYY-MM-DD: %s" % c[:40])
        elif not valid_date(due.group(0)):
            errs.append("condition 到期日无效: %s" % due.group(0))
    if d.get("verdict") == "pivot" and len(str(d.get("pivot_to", ""))) < 10:
        errs.append("pivot 必须给具体转向（pivot_to: …）")
    if not re.match(r"^yes(?:$|[\s(（])", str(d.get("networked", "")), re.I):
        errs.append("networked 必须为 yes：未确认联网核最新事实，拒收为正式 verdict")

    cut = str(d.get("knowledge_cutoff", "")).strip().lower()
    net = str(d.get("networked", ""))
    if cut and cut not in ("unknown", "未披露") and not valid_date(
            cut + "-01" if re.fullmatch(r"\d{4}-\d{2}", cut) else cut):
        errs.append("knowledge_cutoff 必须为有效 YYYY-MM / YYYY-MM-DD 或 unknown / 未披露")
    net_date = re.search(r"\d{4}-\d{2}-\d{2}", net)
    if net_date and not valid_date(net_date.group(0)):
        errs.append("networked 检索截至日无效")
    if cut in ("unknown", "未披露") and not net.lower().startswith("no"):
        if not re.search(r"\d{4}-\d{2}-\d{2}", net):
            errs.append("knowledge_cutoff=unknown 可接受的前提是 networked=yes 且**给了检索截至日**;"
                        "networked 字段里没找到日期 ⇒ 拒收")


    if not miss and d.get("verdict") in VERDICTS:
        total = weighted_total(d)[0]
        nb = near_band(total)
        if nb:
            implied = implied_verdict(total)
            sd = str(d.get("self_doubt", ""))

            named = [v for v in VERDICTS if v != implied
                     and re.search(r"(?<![\w-])" + re.escape(v) + r"(?![\w-])", sd)]
            if not named:
                errs.append("总分 %.1f 落在 %s ±5 内 ⇒ self_doubt 必须显式陈述口径取另一端会落哪档"
                            "（至少点名一个相邻档位: %s）" %
                            (total, nb, "/".join(v for v in sorted(VERDICTS) if v != implied)))
    return errs + outlook_errors(d)


def valid_date(value):
    try:
        return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)) and bool(date.fromisoformat(value))
    except (ValueError, TypeError):
        return False


def near_band(total):
    """纯函数:总分是否落在档位边界 ±BAND_MARGIN 内。返回该边界档位名或 None。"""
    for cut, name in CUTOFFS:
        if abs(total - cut) <= BAND_MARGIN:
            return "%s 边界(%d)" % (name, cut)
    return None
