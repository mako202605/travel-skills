# -*- coding: utf-8 -*-
"""
特色民宿推荐 - ClawHub技能脚本
数据源：飞猪旅行（SCF代理），零配置
2合1：结构化搜索 + AI语义推荐
"""
import json
import urllib.request
import urllib.error

# ============ 配置 ============
FLIGGY_PROXY = "https://1439498936-6sysdjjt99.ap-guangzhou.tencentscf.com"
PROXY_TOKEN = "tp_8k2mX9vQ4z"
TIMEOUT = 60


# ============ 代理调用 ============
def _call_fliggy(rtype, params):
    body = json.dumps({"type": rtype, "params": params}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(
        FLIGGY_PROXY, data=body,
        headers={"Content-Type": "application/json", "X-Proxy-Token": PROXY_TOKEN},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = ""
        try: err = e.read().decode("utf-8", errors="replace")[:200]
        except: pass
        return {"error": "proxy error " + str(e.code) + ": " + err}
    except Exception as e:
        return {"error": "request error: " + str(e)}


# ============ 格式化 ============
def _normalize_item(item):
    """统一item字段：兼容旧版平铺格式和fast_search的info嵌套格式"""
    info = item.get("info")
    if isinstance(info, dict):
        return {
            "name": info.get("title", ""), "price": info.get("price", ""),
            "priceInfo": "", "address": "", "star": info.get("star", ""),
            "score": info.get("scoreDesc", ""), "poi": "",
            "url": info.get("jumpUrl", ""), "pic": info.get("picUrl", ""),
            "tags": info.get("tags", ""),
        }
    return {
        "name": item.get("name", ""), "price": item.get("price", ""),
        "priceInfo": item.get("priceInfo", ""), "address": item.get("address", ""),
        "star": item.get("star", ""),
        "score": item.get("score", "") or item.get("rating", "") or item.get("commentScore", ""),
        "poi": item.get("interestsPoi", ""), "url": item.get("detailUrl", ""),
        "pic": item.get("mainPic", ""), "tags": item.get("tags", ""),
    }


def _format_homestay_list(data):
    """格式化结构化搜索结果为可读列表"""
    items = data.get("data", {}).get("itemList", []) if isinstance(data, dict) else []
    if not items: return ""

    filtered = []
    for item in items:
        norm = _normalize_item(item)
        if "公寓" in norm["name"]: continue
        filtered.append(norm)

    if not filtered: return ""

    lines = []
    for i, it in enumerate(filtered[:10], 1):
        name = it["name"] or "未知"
        line = str(i) + ". " + name
        details = []
        if it["star"] and str(it["star"]).strip(): details.append(str(it["star"]).strip())
        if it["score"] and str(it["score"]).strip(): details.append("⭐" + str(it["score"]).strip())
        price_display = ""
        if it["priceInfo"] and str(it["priceInfo"]).strip():
            price_display = str(it["priceInfo"]).strip()
        elif it["price"] and str(it["price"]).strip():
            price_display = "¥" + str(it["price"]).strip() + "起"
        if price_display: details.append(price_display)
        if details: line += "  " + " | ".join(details)
        lines.append(line)
        if it["address"]: lines.append("   📍 " + it["address"])
        if it["poi"]: lines.append("   🏞️ 附近：" + it["poi"])
        if it["url"]: lines.append("   🔗 " + it["url"])
    lines.append("")
    lines.append("数据来源：飞猪旅行 | 价格实时变动，以实际下单为准")
    return "\n".join(lines)


def _format_ai_text(data):
    """格式化AI搜索结果"""
    if isinstance(data, dict):
        if "error" in data: return "搜索失败：" + data["error"]
        if "raw_text" in data: return data["raw_text"]
        inner = data.get("data", data)
        if isinstance(inner, str): return inner
        if isinstance(inner, dict):
            formatted = _format_homestay_list(data)
            if formatted: return formatted
            return json.dumps(inner, ensure_ascii=False, indent=2)
    return str(data)


# ============ 工具函数 ============

def search_homestay(params):
    """特色民宿搜索：搜索特色民宿，返回民宿列表（名称、价格、评分、地址、预订链接）。"""
    dest_name = params.get("dest_name", "")
    if not dest_name: return "请提供目的地，如：大理、莫干山、三亚"

    key_words = params.get("key_words", "")
    poi_name = params.get("poi_name", "")
    check_in_date = params.get("check_in_date", "")
    check_out_date = params.get("check_out_date", "")
    max_price = params.get("max_price", 0)
    sort = params.get("sort", "")

    parts = [dest_name]
    if key_words: parts.append(key_words)
    elif poi_name: parts.append(poi_name + "附近")
    parts.append("民宿")

    if poi_name and key_words: parts.append("靠近" + poi_name)
    if check_in_date and check_out_date: parts.append("入住" + check_in_date + "退" + check_out_date)
    if max_price > 0: parts.append("价格" + str(max_price) + "元以内")
    if sort == "price_asc": parts.append("按价格从低到高")
    elif sort == "price_desc": parts.append("按价格从高到低")
    elif sort == "rate_desc": parts.append("按评分从高到低")

    query = " ".join(parts)

    # 优先走fliggy_fast_search，失败回退fliggy_ai_search
    result = _call_fliggy("fliggy_fast_search", {"query": query})
    formatted = _format_homestay_list(result)
    if formatted: return formatted

    result = _call_fliggy("fliggy_ai_search", {"query": query})
    return _format_ai_text(result)


def recommend_homestay(params):
    """AI语义推荐民宿：用自然语言描述需求，AI推荐特色民宿。"""
    query = params.get("query", "")
    if not query: return "请描述你的民宿需求，如：莫干山带院子能烧烤的亲子民宿"

    search_query = query
    if "民宿" not in query and "客栈" not in query and "住宿" not in query:
        search_query = query + " 民宿"
    result = _call_fliggy("fliggy_ai_search", {"query": search_query})
    return _format_ai_text(result)
