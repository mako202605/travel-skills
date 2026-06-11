# -*- coding: utf-8 -*-
"""酒店比价 v3.0 - 适配hotel-proxy v3（代理端统一解析，返回纯JSON dict）
第一步：途牛MCP原生搜索（自动2页合并约16家）→ 代码层评分过滤 → 展示酒店列表 + 智能换条件提示
第二步：用户选定酒店 → 多旅游平台精确比价（飞猪+RG detail+途牛多策略+同程）→ 展示各平台价格
美团酒店为推荐式接口，不支持按酒店名精确搜索，比价环节不使用
"""
import argparse, json, re, urllib.request, urllib.error, concurrent.futures
from datetime import datetime, timedelta

PROXY_URL = "https://1439498936-4wdncmn2oj.ap-guangzhou.tencentscf.com"
def _token():
    """代理认证令牌（用于请求OTA平台的代理服务鉴权）"""
    return "tp_8k2mX9vQ4z"

PNAME = {"rg":"RollingGo","tuniu":"途牛","tongcheng":"同程","fliggy":"飞猪"}
PORDER = ["rg","fliggy","tuniu","tongcheng"]
COMMISSION_PRIORITY = {"rg": 0, "fliggy": 1, "tuniu": 2, "tongcheng": 3}

AREA_HINTS = {
    "上海": ["外滩","陆家嘴","南京路","人民广场","虹桥","徐家汇","迪士尼","静安寺","新天地"],
    "北京": ["三里屯","国贸","王府井","西单","望京","中关村","前门","天安门","鸟巢"],
    "杭州": ["西湖","武林广场","钱江新城","萧山","滨江","灵隐寺","千岛湖"],
    "成都": ["春熙路","天府广场","宽窄巷子","武侯祠","锦里","太古里"],
    "广州": ["天河","珠江新城","北京路","越秀","白云","番禺"],
    "深圳": ["福田","南山","罗湖","华侨城","蛇口","宝安"],
    "三亚": ["亚龙湾","海棠湾","大东海","三亚湾","天涯海角"],
    "南京": ["新街口","夫子庙","玄武湖","中山陵","河西","仙林"],
}

# ===== 代理调用 =====
def _proxy(source, params, timeout=30):
    body = json.dumps({"source": source, "params": params}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        PROXY_URL, data=body,
        headers={"Content-Type": "application/json", "X-Proxy-Token": _token()},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"code": 500, "error": str(e)}

def _get_data(resp):
    """v3代理：直接返回纯dict，无需MCP/SSE解析"""
    if resp.get("code") != 0:
        return {"error": resp.get("error", "代理请求失败")[:200]}
    if resp.get("error"):
        return {"error": str(resp["error"])[:200]}
    data = resp.get("data")
    if data is None:
        return {"error": "数据为空"}
    return data

def _clean(name):
    """清理酒店名：去英文括号内容，保留中文括号和·"""
    name = re.sub(r'\s*\([A-Za-z][^)]*\)', '', name).strip()
    while name and name[-1] in ')）':
        if (name.count('(') + name.count('（')) < (name.count(')') + name.count('）')):
            name = name[:-1].rstrip()
        else:
            break
    return name.strip()

# ===== 第一步：途牛浏览（自动2页） =====
def _tuniu_browse(city, ci, co, kw, max_price, poi_name, min_score):
    """途牛MCP原生酒店搜索，自动查2页合并，代码层过滤评分"""
    params = {"city": city, "check_in": ci, "check_out": co}
    if kw and kw != "None": params["keyword"] = kw
    if poi_name and poi_name != "None": params["poiName"] = poi_name
    if max_price and max_price > 0: params["prices"] = f"0-{max_price}"

    # 第1页
    resp1 = _proxy("tuniu", params)
    data1 = _get_data(resp1)
    if "error" in data1:
        return [], 0
    qid1 = data1.get("queryId", "")
    hl1 = data1.get("hotels") or data1.get("hotelList") or []
    if not isinstance(hl1, list):
        hl1 = []

    # 第2页
    hl2 = []
    if qid1 and len(hl1) >= 6:
        params2 = dict(params)
        params2["pageNum"] = "2"
        params2["queryId"] = qid1
        resp2 = _proxy("tuniu", params2)
        data2 = _get_data(resp2)
        if "hotels" in data2 or "hotelList" in data2:
            hl2 = data2.get("hotels") or data2.get("hotelList") or []
            if not isinstance(hl2, list):
                hl2 = []

    # 合并去重
    all_raw = hl1 + hl2
    seen_ids = set()
    hotels = []
    total_before_filter = 0
    for h in all_raw[:40]:
        hotel_id = str(h.get("hotelId", ""))
        if hotel_id and hotel_id in seen_ids:
            continue
        if hotel_id:
            seen_ids.add(hotel_id)
        name = _clean(h.get("hotelName") or h.get("name", ""))
        if not name:
            continue
        try:
            p = float(re.sub(r"[^\d.]", "", str(h.get("lowestPrice") or h.get("price") or "0")))
        except:
            p = 0
        if p <= 0:
            continue
        score = h.get("commentScore")
        try:
            score = float(score) if score else 0
        except:
            score = 0
        total_before_filter += 1
        # 评分过滤
        if min_score and min_score > 0 and score > 0 and score < min_score:
            continue
        url = h.get("detailUrl") or h.get("url", "")
        if not url and hotel_id:
            url = f"https://hotel.tuniu.com/detail/{hotel_id}"
        hotels.append({
            "name": name, "price": p,
            "address": h.get("address") or h.get("hotelAddress", ""),
            "star": h.get("starName") or h.get("star", ""),
            "source": "tuniu", "url": url,
            "brand": h.get("brandName") or "",
            "score": score,
            "distance": h.get("distance") or "",
            "meal": h.get("meal") or "",
            "room_name": h.get("roomName") or "",
            "room_window": h.get("roomWindow") or "",
            "refund": h.get("refund") or "",
            "comment_digest": h.get("commentDigest") or "",
            "pic": h.get("firstPic") or "",
            "hotel_id": hotel_id,
        })
    return hotels, total_before_filter

# ===== 第二步：多旅游平台精确比价 =====
def _call_fg(city, ci, co, kw):
    """飞猪：keyword精准过滤，搜酒店名最稳"""
    resp = _proxy("fliggy", {"city": city, "check_in": ci, "check_out": co, "keyword": kw or ""})
    data = _get_data(resp)
    if "error" in data:
        return []
    # v3飞猪格式：{data: {itemList: [...]}, status, ...}
    items = []
    if isinstance(data, dict):
        inner = data.get("data", {})
        if isinstance(inner, dict):
            items = inner.get("itemList", [])
        elif isinstance(inner, list):
            items = inner
        if not items:
            items = data.get("hotels") or data.get("hotelList") or data.get("itemList") or []
    if not isinstance(items, list):
        return []
    hotels = []
    for h in items[:20]:
        name = _clean(h.get("name") or h.get("hotelName", ""))
        if not name:
            continue
        try:
            p = float(re.sub(r"[^\d.]", "", str(h.get("price") or h.get("lowestPrice") or "0")))
        except:
            p = 0
        if p <= 0:
            continue
        hotels.append({
            "name": name, "price": p,
            "address": h.get("address", ""),
            "star": h.get("star", ""),
            "source": "fliggy",
            "url": h.get("detailUrl") or h.get("url", ""),
            "brand": h.get("brandName") or "",
        })
    return hotels

def _call_rg_detail(name, ci, co):
    """RG：hotel_detail按名查，比价首选"""
    resp = _proxy("rg_detail", {"name": name, "check_in": ci, "check_out": co})
    data = _get_data(resp)
    if "error" in data or "roomRatePlans" not in data:
        return None
    plans = data.get("roomRatePlans", [])
    prices = []
    for plan in plans:
        tp = plan.get("totalPrice")
        if tp:
            try:
                prices.append(float(tp))
            except:
                pass
        rp = plan.get("roomPrice")
        if rp:
            try:
                prices.append(float(rp))
            except:
                pass
    if not prices:
        return None
    min_p = min(prices)
    url = data.get("bookingUrl", "")
    return {"name": _clean(data.get("name", name)), "price": min_p, "source": "rg", "url": url}

def _call_tn_compare(city, ci, co, hotel_name, query_id):
    """途牛：3种策略比价"""
    strategies = []
    # 策略1：指定酒店名搜索
    if hotel_name:
        strategies.append({"city": city, "check_in": ci, "check_out": co, "keyword": hotel_name})
    # 策略2：如果有queryId翻页
    if query_id:
        strategies.append({"city": city, "check_in": ci, "check_out": co, "queryId": query_id, "pageNum": "1"})
    # 策略3：全城搜索
    if hotel_name:
        strategies.append({"city": city, "check_in": ci, "check_out": co})

    for params in strategies:
        resp = _proxy("tuniu", params)
        data = _get_data(resp)
        if "error" in data:
            continue
        hl = data.get("hotels") or data.get("hotelList") or []
        if not isinstance(hl, list):
            continue
        for h in hl[:30]:
            hname = _clean(h.get("hotelName") or h.get("name", ""))
            if not hname or not _name_match(hotel_name, hname):
                continue
            try:
                p = float(re.sub(r"[^\d.]", "", str(h.get("lowestPrice") or h.get("price") or "0")))
            except:
                p = 0
            if p <= 0:
                continue
            hotel_id = str(h.get("hotelId", ""))
            url = h.get("detailUrl") or ""
            if not url and hotel_id:
                url = f"https://hotel.tuniu.com/detail/{hotel_id}"
            return {"name": hname, "price": p, "source": "tuniu", "url": url}
    return None

def _call_tc_compare(city, ci, co, target_name):
    """同程：v3返回{text, 产品跳转链接}，从文本中提取价格"""
    resp = _proxy("tongcheng", {"city": city, "check_in": ci, "check_out": co})
    data = _get_data(resp)
    if "error" in data:
        return None
    # v3同程格式：{code: 0, msg: 'success', data: {text: '...', '产品跳转链接': {...}}}
    inner = data.get("data", data)
    if not isinstance(inner, dict):
        return None
    text = inner.get("text", "")
    links = inner.get("产品跳转链接", {})
    if not text:
        return None

    # 从文本解析酒店价格
    pats = [
        re.compile(r'^([^，。\n]+?)\s+.*?评分[\s：:]*(\d+\.?\d*).*?价格[\s：:]*(\d+[\d,.]*)\s*元', re.M),
        re.compile(r'^([^，。\n]+?)\s+.*?价格[\s：:]*(\d+[\d,.]*)\s*元', re.M),
    ]
    for para in text.split("\n\n"):
        para = para.strip()
        if not para or any(s in para for s in ["出行建议", "客服电话", "建议入住"]):
            continue
        for pat in pats:
            m = pat.match(para)
            if m:
                hname = _clean(m.group(1).strip())
                if _name_match(target_name, hname):
                    try:
                        price_group = m.group(m.lastindex)
                        pv = float(price_group.replace(",", ""))
                    except:
                        pv = 0
                    if pv > 0:
                        url = ""
                        if isinstance(links, dict):
                            for lk, ld in links.items():
                                if hname in lk or lk in hname:
                                    url = (ld.get("手机链接") or ld.get("PC链接", "")) if isinstance(ld, dict) else ""
                                    break
                        return {"name": hname, "price": pv, "source": "tongcheng", "url": url}
    return None

def _name_match(target, candidate, threshold=0.4):
    """简单名字匹配"""
    t, c = target.lower(), candidate.lower()
    if t == c or t in c or c in t:
        return True
    # 去括号后比较
    t_clean = re.sub(r'[\(（][^)）]*[\)）]', '', t).strip()
    c_clean = re.sub(r'[\(（][^)）]*[\)）]', '', c).strip()
    if t_clean and c_clean and (t_clean in c_clean or c_clean in t_clean):
        return True
    # 品牌匹配
    brand_list = ["华尔道夫","威斯汀","丽思卡尔顿","索菲特","全季","亚朵","桔子","如家","汉庭","丽枫","希尔顿","万豪","喜来登"]
    for b in brand_list:
        if b in t and b in c:
            return True
    return False

# ===== 智能提示 =====
def _smart_tips(hotels, city, kw, max_price, poi_name, min_score, total_before_filter):
    """根据搜索结果数量，给出调主轴（换区域）或调筛子（价格/评分）的建议"""
    tips = []
    n = len(hotels)
    areas = AREA_HINTS.get(city, [])
    nearby = [a for a in areas if a != (kw or "") and a != (poi_name or "")][:2]

    if n == 0:
        if min_score and min_score > 0:
            tips.append(f"💡 去掉评分限制，或降低评分要求（当前≥{min_score}分）")
        if max_price and max_price > 0:
            tips.append(f"💡 提高价格上限（当前≤¥{max_price}），或去掉价格限制")
        if not min_score and not max_price:
            tips.append("💡 去掉筛选条件，扩大搜索范围")
        if nearby:
            tips.append(f"💡 换个区域试试：{nearby[0]}、{nearby[1]}")
        if kw and len(kw) <= 3:
            tips.append(f"💡 关键词范围放大：\"{kw}\"→\"{city}\"")
    elif n <= 3:
        if min_score and min_score > 0:
            tips.append(f"💡 降低评分要求（当前≥{min_score}分）")
        if max_price and max_price > 0:
            tips.append(f"💡 提高价格上限（当前≤¥{max_price}）")
        if not min_score and not max_price:
            tips.append("💡 可以加价格或评分要求，缩小范围精选")
        if nearby:
            tips.append(f"💡 换个区域：{nearby[0]}、{nearby[1]}")
    else:
        if not max_price and not min_score:
            tips.append("📌 没找到心仪的？可以：限价（告诉我预算，如\"1000以内\"）、限评分（如\"4.5分以上\"）、或换个区域")
        elif nearby:
            tips.append(f"📌 没找到心仪的？可以换个区域：{nearby[0]}、{nearby[1]}")

    return tips

# ===== 展示格式 =====
def _safe_score(h):
    try:
        return float(h.get("score", 0) or 0)
    except:
        return 0

def _price_overview(hotels):
    if not hotels:
        return ""
    prices = [h["price"] for h in hotels if h["price"] > 0]
    if not prices:
        return ""
    lo, hi = int(min(prices)), int(max(prices))
    avg = int(sum(prices) / len(prices))
    scores = [_safe_score(h) for h in hotels if _safe_score(h) >= 4.5]
    parts = [f"💰 ¥{lo}~¥{hi} | 均价¥{avg}"]
    if scores:
        parts.append(f"4.5分以上{len(scores)}家")
    return " | ".join(parts)

def _format_browse(hotels, city, ci, co, kw, max_price, poi_name, min_score, total_before_filter):
    """第一步：浏览模式，展示途牛酒店列表"""
    dest = f"{city}{kw}" if kw else city
    lines = [f"🏨 **{dest}** 酒店浏览（{ci}~{co}）"]
    lines.append("")
    lines.append("⚠️ **以上为浏览价格，尚未比价！选定酒店后告诉我酒店名（如\"第2家\"或酒店全名），立刻启动多旅游平台比价，帮您找到全网最低价！**")
    lines.append("")
    if min_score and min_score > 0 and len(hotels) < total_before_filter:
        lines.append(f"📊 途牛为您找到{total_before_filter}家酒店，评分≥{min_score}分筛选后{len(hotels)}家")
    else:
        lines.append(f"📊 途牛为您找到{len(hotels)}家酒店")
    lines.append(_price_overview(hotels))
    lines.append("")
    for i, h in enumerate(hotels[:16], 1):
        star_str = f" · {h['star']}" if h.get("star") else ""
        score_str = f" · {h['score']}分" if _safe_score(h) > 0 else ""
        brand_str = f" · {h['brand']}" if h.get("brand") else ""
        dist_str = f" · {h['distance']}" if h.get("distance") else ""
        meal_str = ""
        if h.get("meal") and "无" not in str(h["meal"]):
            meal_str = f" · 🍽️{h['meal']}"
        window_str = ""
        if h.get("room_window") and "无" not in str(h["room_window"]):
            window_str = f" · 🪟{h['room_window']}"
        refund_str = ""
        if h.get("refund") and "不可" not in str(h["refund"]):
            refund_str = f" · ↩️可取消"

        url = h.get("url", "")
        link = f" [查看→]({url})" if url else ""
        lines.append(f"**{i}. {h['name']}**{star_str}{score_str}")
        detail_parts = [f"¥{int(h['price'])}起"]
        if brand_str:
            detail_parts.append(brand_str.strip(" · "))
        if dist_str:
            detail_parts.append(dist_str.strip(" · "))
        if meal_str:
            detail_parts.append(meal_str.strip(" · "))
        if window_str:
            detail_parts.append(window_str.strip(" · "))
        if refund_str:
            detail_parts.append(refund_str.strip(" · "))
        lines.append(f"   途牛 {' | '.join(detail_parts)}{link}")
        if h.get("comment_digest"):
            lines.append(f"   💬 {h['comment_digest'][:40]}")
        lines.append("")

    # 智能换条件提示
    tips = _smart_tips(hotels, city, kw, max_price, poi_name, min_score, total_before_filter)
    for tip in tips:
        lines.append(tip)
    if tips:
        lines.append("")

    lines.append('⚠️ **尚未比价！告诉我酒店名（如"第3家"或酒店全名），立刻启动多旅游平台比价！**')
    return "\n".join(lines)

def _format_compare(target_name, rg_result, tn_result, fg_result, tc_result, city, ci, co):
    """第二步：比价模式，展示4源比价结果"""
    lines = [f"💰 **{target_name}** 多旅游平台比价（{ci}~{co}）"]
    lines.append("")
    found = []
    if rg_result:
        found.append(("rg", rg_result))
    if fg_result:
        found.append(("fliggy", fg_result))
    if tn_result:
        found.append(("tuniu", tn_result))
    if tc_result:
        found.append(("tongcheng", tc_result))

    if not found:
        lines.append("❌ 所有平台均未找到该酒店，建议换关键词重试")
        return "\n".join(lines)

    lines.append(f"📊 {len(found)}家平台有报价，价格从低到高：")
    lines.append("")

    # 按价格排序，同价按佣金优先级
    found.sort(key=lambda x: (x[1]["price"] if x[1]["price"] > 0 else 99999, COMMISSION_PRIORITY.get(x[0], 99)))

    min_price = found[0][1]["price"] if found else 0
    for i, (src, h) in enumerate(found):
        p = int(h["price"])
        name_str = PNAME.get(src, src)
        url = h.get("url", "")
        diff_str = ""
        if p > min_price:
            diff_str = f"（贵¥{p - int(min_price)}）"
        if i == 0:
            label = f"💰 **{name_str} ¥{p}最低价**"
            link = f" [去预订→]({url})" if url else ""
            if len(found) > 1:
                second_p = found[1][1]["price"]
                label += f"（比次低省¥{int(second_p) - p}）"
            lines.append(f"{label}{link}")
        else:
            link = f" [去预订→]({url})" if url else ""
            lines.append(f" {name_str} ¥{p}{diff_str}{link}")

    lines.append("")
    lines.append("💡 价格实时变动，以实际预订为准")
    return "\n".join(lines)

# ===== 主入口 =====
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True)
    parser.add_argument("--check-in", default="")
    parser.add_argument("--check-out", default="")
    parser.add_argument("--keyword", default="")
    parser.add_argument("--hotel-name", default="")
    parser.add_argument("--max-price", type=int, default=0)
    parser.add_argument("--poi-name", default="")
    parser.add_argument("--min-score", type=float, default=0)
    args = parser.parse_args()

    city = args.city
    ci = args.check_in
    co = args.check_out
    kw = args.keyword if args.keyword and args.keyword != "None" else ""
    hotel_name = args.hotel_name if args.hotel_name and args.hotel_name != "None" else ""
    mp = args.max_price or 0
    poi_name = args.poi_name if args.poi_name and args.poi_name != "None" else ""
    ms = args.min_score or 0

    # 默认日期
    if not ci or ci == "None":
        ci = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    if not co or co == "None":
        co = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    try:
        d1 = datetime.strptime(ci, "%Y-%m-%d")
        d2 = datetime.strptime(co, "%Y-%m-%d")
        if d1 < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
            print(f"❌ 入住日期{ci}已过期"); return
        if d2 <= d1:
            print(f"❌ 离店日期({co})必须晚于入住日期({ci})"); return
    except ValueError:
        print("❌ 日期格式不正确，请使用YYYY-MM-DD格式"); return

    if hotel_name:
        # ========== 第二步：多旅游平台精确比价 ==========
        rg_result = _call_rg_detail(hotel_name, ci, co)
        tn_result = _call_tn_compare(city, ci, co, hotel_name, "")
        fg_result = None
        fg_list = _call_fg(city, ci, co, hotel_name)
        for h in fg_list:
            if _name_match(hotel_name, h["name"]):
                fg_result = h
                break
        tc_result = _call_tc_compare(city, ci, co, hotel_name)
        print(_format_compare(hotel_name, rg_result, tn_result, fg_result, tc_result, city, ci, co))
    else:
        # ========== 第一步：途牛浏览（自动2页） ==========
        hotels, total_before_filter = _tuniu_browse(city, ci, co, kw, mp, poi_name, ms)
        if not hotels:
            tips = _smart_tips([], city, kw, mp, poi_name, ms, total_before_filter)
            lines = [f"❌ 未找到{city}{kw}的酒店"]
            for tip in tips:
                lines.append(tip)
            print("\n".join(lines))
        else:
            print(_format_browse(hotels, city, ci, co, kw, mp, poi_name, ms, total_before_filter))

if __name__ == "__main__":
    main()
