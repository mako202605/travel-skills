# -*- coding: utf-8 -*-
"""
全球航班查询与预订 v1.0.0 - 腾讯云SCF代理版
1次调用完成：中文城市→代码映射→搜索→直飞/中转分组→性价比标签→中转等待
密钥存储在SCF环境变量中，脚本不含任何API密钥
"""
import argparse, json, re, sys, urllib.request, urllib.error
from datetime import datetime

# ===== 代理配置 =====
PROXY_URL = "https://1439498936-460a7b6oqn.ap-guangzhou.tencentscf.com"
PROXY_TOKEN = "tp_8k2mX9vQ4z"

# ===== 中文城市→代码映射（100+城市）=====
CITY_CODE_MAP = {
    # 中国大陆
    "北京": "BJS", "上海": "SHA", "广州": "CAN", "深圳": "SZX",
    "成都": "CTU", "杭州": "HGH", "南京": "NKG", "武汉": "WUH",
    "长沙": "CSX", "重庆": "CKG", "西安": "SIA", "厦门": "XMN",
    "青岛": "TAO", "大连": "DLC", "昆明": "KMG", "丽江": "LJG",
    "桂林": "KWL", "苏州": "SZV", "珠海": "ZUH", "海口": "HAK",
    "三亚": "SYX", "天津": "TSN", "济南": "TNA", "沈阳": "SHE",
    "哈尔滨": "HRB", "长春": "CGQ", "郑州": "CGO", "合肥": "HFE",
    "福州": "FOC", "南昌": "KHN", "太原": "TYN", "石家庄": "SJW",
    "贵阳": "KWE", "南宁": "NNG", "兰州": "LHW", "银川": "INC",
    "呼和浩特": "HET", "乌鲁木齐": "URC", "拉萨": "LXA",
    "无锡": "WUX", "宁波": "NGB", "温州": "WNZ", "烟台": "YNT",
    "威海": "WEH", "佛山": "FUO", "东莞": "DGM", "中山": "ZGN",
    "扬州": "YTY", "大理": "DLU", "西双版纳": "JHG",
    "张家界": "DYG", "九寨沟": "JZH", "黄山": "TXN",
    "洛阳": "LYA", "敦煌": "DNH",
    # 港澳台
    "香港": "HKG", "澳门": "MFM", "台北": "TPE", "高雄": "KHH",
    "台南": "TNN", "台中": "TXG", "花莲": "HUN",
    # 亚洲热门
    "东京": "NRT", "大阪": "OSA", "京都": "OSA", "冲绳": "OKA",
    "北海道": "SPK", "福冈": "FUK", "名古屋": "NGO", "札幌": "SPK",
    "首尔": "SEL", "釜山": "PUS", "济州": "CJU",
    "曼谷": "BKK", "普吉": "HKT", "清迈": "CNX", "芭提雅": "UTP",
    "新加坡": "SIN",
    "吉隆坡": "KUL", "槟城": "PEN", "沙巴": "BKI",
    "河内": "HAN", "胡志明": "SGN", "岘港": "DAD", "芽庄": "CXR",
    "巴厘岛": "DPS", "雅加达": "CGK",
    "马尼拉": "MNL", "长滩岛": "MPH",
    "暹粒": "REP",
    "仰光": "RGN",
    "加德满都": "KTM",
    "科伦坡": "CMB",
    "马累": "MLE",
    # 欧美澳非
    "纽约": "NYC", "洛杉矶": "LAX", "旧金山": "SFO", "拉斯维加斯": "LAS",
    "夏威夷": "HNL", "塞班": "SPN", "关岛": "GUM",
    "伦敦": "LON", "巴黎": "PAR", "柏林": "BER", "罗马": "ROM",
    "米兰": "MIL", "巴塞罗那": "BCN", "马德里": "MAD",
    "悉尼": "SYD", "墨尔本": "MEL", "奥克兰": "AKL",
    "迪拜": "DXB", "阿布扎比": "AUH",
    "伊斯坦布尔": "IST",
    "莫斯科": "MOW",
    "温哥华": "YVR", "多伦多": "YYZ",
    "圣保罗": "GRU",
    "墨西哥城": "MEX",
    "孟买": "BOM", "新德里": "DEL",
    "开罗": "CAI",
    "约翰内斯堡": "JNB",
}

# 城市代码→中文映射（反向）
CODE_CITY_MAP = {v: k for k, v in CITY_CODE_MAP.items()}

# ===== 航司代码中文映射（80+）=====
AIRLINE_MAP = {
    # 中国大陆
    "CA": "国航", "MU": "东航", "CZ": "南航", "HU": "海航",
    "9C": "春秋", "HO": "吉祥", "ZH": "深航", "MF": "厦航",
    "SC": "山航", "3U": "川航", "FM": "上航",
    "GS": "天津航", "PN": "西部航", "G5": "华夏航", "EU": "成都航",
    "NS": "河北航", "AQ": "九元航", "KY": "昆明航", "LT": "龙江航",
    "JR": "幸福航", "D7": "首都航", "Y8": "扬子江航", "OQ": "重庆航",
    "TV": "西藏航", "FU": "福航", "RY": "江西航", "GJ": "长龙航",
    # 港澳台
    "CX": "国泰", "KA": "港龙", "HX": "香港航", "UO": "港快运",
    "NX": "澳航", "BR": "长荣", "CI": "中华航", "AE": "华信",
    "B7": "立荣",
    # 亚洲
    "NH": "全日空", "JL": "日航", "GK": "捷星日本", "IJ": "日本春秋", "BC": "天马",
    "KE": "大韩", "OZ": "韩亚", "7C": "济州航", "TW": "德威",
    "TG": "泰航", "FD": "泰亚航", "SL": "泰狮航",
    "SQ": "新航", "TR": "酷航", "MI": "胜安",
    "MH": "马航", "AK": "马亚航",
    "VN": "越航", "VJ": "越捷",
    "GA": "印尼鹰航", "QG": "印尼连城", "JT": "狮航",
    "5J": "宿务航", "PR": "菲航",
    # 欧美
    "BA": "英航", "VS": "维珍", "LH": "汉莎", "DE": "神鹰",
    "AF": "法航", "KL": "荷航", "AZ": "意航",
    "EK": "阿联酋", "EY": "阿提哈德", "QR": "卡塔尔",
    "TK": "土航", "SU": "俄航",
    "AA": "美航", "UA": "美联航", "DL": "达美",
    "AC": "加航",
    "QF": "澳航", "VA": "维珍澳",
    "NZ": "纽航",
    # 低成本
    "QZ": "印尼亚航",
    "U2": "易捷", "FR": "瑞安", "W6": "维兹",
    "NK": "精神航", "B6": "捷蓝", "F9": "边防航",
}

# ===== 非民用机场过滤关键词 =====
NON_AIRPORT_KEYWORDS = [
    "火车站", "巴士", "轮渡", "港口", "码头",
    "Ferry", "Bus", "Heliport", "Harbour", "Harbor",
    "空军基地", "Air Force", "Military", "Army",
    "Offline", "OffLine Point", "Closed",
    "直升机", "Helicopter",
]

# ===== 国内城市代码 =====
DOMESTIC_CITY_CODES = set(CITY_CODE_MAP.values()) | {
    "PEK", "PVG", "PKX", "TFU",
}


# ===== 代理调用 =====

def call_proxy(api_type, params, timeout=30):
    """调用RG代理"""
    body = json.dumps({"type": api_type, "params": params}, ensure_ascii=False, separators=(",", ":"))
    req = urllib.request.Request(
        PROXY_URL, data=body.encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Proxy-Token": PROXY_TOKEN},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            result = json.loads(r.read().decode("utf-8"))
        if result.get("code") != 0:
            return {"error": result.get("error", "proxy error")}
        raw = result.get("data", "")
        ct = result.get("content_type", "")
        return _parse_mcp(raw, ct)
    except Exception as e:
        return {"error": str(e)}


def _parse_mcp(raw, content_type):
    """解析MCP JSON-RPC响应"""
    if not raw:
        return {"error": "empty response"}
    try:
        if "text/event-stream" in (content_type or ""):
            for line in raw.split("\n"):
                if line.startswith("data:"):
                    return _extract_mcp_result(json.loads(line[5:].strip()))
        return _extract_mcp_result(json.loads(raw))
    except Exception:
        return {"error": "parse fail", "raw": raw[:200]}


def _extract_mcp_result(result):
    if "error" in result:
        return {"error": str(result["error"].get("message", result["error"]))[:200]}
    res = result.get("result", result)
    if isinstance(res, dict) and "content" in res:
        contents = res["content"]
        if isinstance(contents, list) and len(contents) > 0:
            f = contents[0]
            if isinstance(f, dict) and f.get("type") == "text":
                t = f.get("text", "")
                try:
                    return json.loads(t)
                except Exception:
                    return {"raw_text": t}
    return res


# ===== 工具函数 =====

def _resolve_city_code(city_input):
    """中文城市名→代码"""
    if not city_input:
        return city_input
    if re.match(r'^[A-Z]{2,4}$', city_input.upper()):
        return city_input.upper()
    return CITY_CODE_MAP.get(city_input, city_input)


def _is_domestic(code):
    if not code:
        return False
    return code.upper() in DOMESTIC_CITY_CODES


def _get_airline_name(code):
    if not code:
        return code or ""
    name = AIRLINE_MAP.get(code.upper())
    return name if name else code


def _is_civil_airport(name):
    if not name:
        return True
    name_lower = name.lower()
    for kw in NON_AIRPORT_KEYWORDS:
        if kw.lower() in name_lower:
            return False
    return True


def _format_duration(minutes):
    try:
        minutes = int(minutes) if minutes else 0
        if minutes <= 0:
            return ""
        h = minutes // 60
        m = minutes % 60
        return f"{h}h{m}m" if m else f"{h}h"
    except (ValueError, TypeError):
        return str(minutes) if minutes else ""


def _format_time(dt_str):
    try:
        return dt_str[11:16] if len(dt_str) >= 16 else dt_str
    except (IndexError, TypeError):
        return str(dt_str) if dt_str else ""


def _format_wait_time(segs):
    if len(segs) < 2:
        return ""
    try:
        arr_time_str = segs[0].get("arrTime", "")
        dep_time_str = segs[1].get("depTime", "")
        if not arr_time_str or not dep_time_str:
            return ""
        arr_dt = datetime.fromisoformat(arr_time_str.replace("Z", "+00:00"))
        dep_dt = datetime.fromisoformat(dep_time_str.replace("Z", "+00:00"))
        wait_minutes = int((dep_dt - arr_dt).total_seconds() / 60)
        if wait_minutes <= 0:
            return ""
        return _format_duration(wait_minutes)
    except Exception:
        return ""


# ===== 航班搜索 =====

def search_flights(from_city, to_city, from_date, from_airport=None, to_airport=None,
                   cabin_grade="ECONOMY", trip_type="ONE_WAY", ret_date=None,
                   adult_number=1, child_number=0):
    """搜索航班，返回格式化结果"""
    resolved_from = _resolve_city_code(from_city)
    resolved_to = _resolve_city_code(to_city)

    if not resolved_from and not from_airport:
        return f"❌ 无法识别出发城市「{from_city}」，请使用城市代码（如BJS）或机场代码"
    if not resolved_to and not to_airport:
        return f"❌ 无法识别到达城市「{to_city}」，请使用城市代码（如SYX）或机场代码"

    params = {
        "from_city_code": resolved_from or "",
        "to_city_code": resolved_to or "",
        "date": from_date,
        "cabin_grade": cabin_grade,
        "trip_type": trip_type,
        "adult_number": adult_number,
        "child_number": child_number,
    }
    if from_airport:
        params["from_airport"] = from_airport.upper()
    if to_airport:
        params["to_airport"] = to_airport.upper()
    if ret_date:
        params["ret_date"] = ret_date

    data = call_proxy("flight", params)

    from_label = from_airport or resolved_from or from_city
    to_label = to_airport or resolved_to or to_city

    return _format_flights(data, from_label, to_label, resolved_to, to_airport)


# ===== 机场搜索 =====

def search_airports(keyword):
    """搜索机场/城市代码"""
    resolved = _resolve_city_code(keyword)
    if resolved and resolved != keyword:
        return f"✅「{keyword}」已映射为城市代码 {resolved}，可直接用中文城市名查航班"

    data = call_proxy("flight_airport", {"keyword": keyword})
    return _format_airports(data, keyword)


# ===== 格式化输出 =====

def _format_flights(data, from_label, to_label, to_city="", to_airport=""):
    if isinstance(data, dict) and "error" in data:
        return f"❌ 查询失败: {data['error']}"

    flights = None
    if isinstance(data, dict):
        flights = data.get("flightInformationList")

    if flights is None:
        return "未找到符合条件的航班。建议调整搜索条件或确认城市代码后重试。"

    if not flights:
        route = f" {from_label}→{to_label}" if from_label and to_label else ""
        return f"未找到符合条件的航班{route}。建议调整搜索条件或确认城市代码后重试。"

    # 按SmartValueScore排序
    flights.sort(key=lambda x: float(x.get("fromSmartValueScore", 0) or 0), reverse=True)
    top = flights[:10]

    direct = [f for f in top if len(f.get("fromSegments", [])) == 1]
    transfer = [f for f in top if len(f.get("fromSegments", [])) > 1]

    route_info = f" {from_label}→{to_label}" if from_label and to_label else ""
    lines = [f"✈️ 找到 {len(flights)} 个航班方案{route_info}，展示前10：", ""]

    if direct:
        lines.append(f"━━━ 直飞航班 ({len(direct)}个) ━━━")
        lines.append("")
        for i, fl in enumerate(direct, 1):
            _format_single_flight(lines, i, fl)

    if transfer:
        lines.append(f"━━━ 中转航班 ({len(transfer)}个) ━━━")
        lines.append("")
        for i, fl in enumerate(transfer, 1):
            idx = len(direct) + i
            _format_single_flight(lines, idx, fl)

    lines.append("⚠️ 价格为参考价，以实际下单为准")

    # 附加服务提示
    dest_code = to_airport or to_city
    dest_name = CODE_CITY_MAP.get(dest_code, "")
    tips = []
    if dest_name:
        tips.append(f"🏨推荐{dest_name}酒店")
    else:
        tips.append("🏨目的地酒店")
    is_dom = _is_domestic(to_city) or _is_domestic(to_airport)
    if is_dom:
        city_name = dest_name or dest_code
        tips.append(f"🚇{city_name}市内交通")
    if tips:
        lines.append("\n📋 附加服务：" + " | ".join(tips))

    return "\n".join(lines)


def _format_single_flight(lines, idx, fl):
    from_segs = fl.get("fromSegments", [])
    if not from_segs:
        return

    adult_price = fl.get("totalAdultPrice", "")
    currency = fl.get("currency", "")
    carrier = fl.get("validatingCarrier", "")
    carrier_cn = _get_airline_name(carrier)
    smart_score = float(fl.get("fromSmartValueScore", 0) or 0)

    price_str = f"¥{adult_price}" if adult_price else "价格待查"
    score_label = " 🏆性价比之选" if smart_score >= 80 else ""

    if len(from_segs) == 1:
        seg = from_segs[0]
        fn = seg.get("flightNumber", "")
        dep = seg.get("depAirport", "")
        arr = seg.get("arrAirport", "")
        dep_t = _format_time(seg.get("depTime", ""))
        arr_t = _format_time(seg.get("arrTime", ""))
        dur = int(seg.get("duration", "0") or 0)
        dur_str = _format_duration(dur)

        lines.append(f"{idx}. {fn} [{carrier_cn}]{score_label}")
        lines.append(f"   {dep} {dep_t} → {arr} {arr_t}（{dur_str}）")
        lines.append(f"   💰 {price_str} {currency}")
        lines.append("")
    else:
        lines.append(f"{idx}. 中转 [{carrier_cn}]{score_label}")
        for j, seg in enumerate(from_segs):
            fn = seg.get("flightNumber", "")
            dep = seg.get("depAirport", "")
            arr = seg.get("arrAirport", "")
            dep_t = _format_time(seg.get("depTime", ""))
            arr_t = _format_time(seg.get("arrTime", ""))
            prefix = "├" if j < len(from_segs) - 1 else "└"
            lines.append(f"   {prefix} 第{j+1}段: {fn} {dep}{dep_t}→{arr}{arr_t}")

        wait = _format_wait_time(from_segs)
        if wait:
            lines.append(f"   ⏱️ 中转等待{wait}")

        lines.append(f"   💰 {price_str} {currency}")
        lines.append("")


def _format_airports(data, keyword):
    if isinstance(data, dict) and "error" in data:
        return f"❌ 搜索失败: {data['error']}"

    airports = None
    if isinstance(data, dict):
        airports = data.get("airPortInformationList")

    if not airports:
        return f"未找到匹配「{keyword}」的机场或城市。请尝试其他关键词，或直接使用中文城市名查航班。"

    civil_airports = [ap for ap in airports if _is_civil_airport(ap.get("airportName", ""))]

    if not civil_airports:
        return f"未找到匹配「{keyword}」的民用机场。请尝试其他关键词，或直接使用中文城市名查航班。"

    lines = [f"✈️ 找到 {len(civil_airports)} 个结果：", ""]

    for i, ap in enumerate(civil_airports, 1):
        name = ap.get("airportName", "")
        code = ap.get("airportCode", "")
        city = ap.get("cityName", "")
        city_code = ap.get("cityCode", "")
        country = ap.get("countryName", "")

        lines.append(f"{i}. {name}（{code}）")
        detail_parts = []
        if city:
            detail_parts.append(f"城市: {city}（{city_code}）")
        if country:
            detail_parts.append(f"国家: {country}")
        if detail_parts:
            lines.append("   " + " | ".join(detail_parts))
        lines.append("")

    lines.append("💡 cityCode可用于城市级查航班，airportCode可用于精确查航班")
    lines.append("💡 也支持中文城市名直接查航班（如'北京→东京'）")
    return "\n".join(lines)


# ===== CLI入口 =====

def main():
    parser = argparse.ArgumentParser(description="全球航班查询与预订")
    sub = parser.add_subparsers(dest="command", help="子命令")

    # search_flights
    p_flight = sub.add_parser("search", help="搜索航班")
    p_flight.add_argument("--from-city", required=True, help="出发城市（中文/代码）")
    p_flight.add_argument("--to-city", required=True, help="到达城市（中文/代码）")
    p_flight.add_argument("--date", required=True, help="出发日期 YYYY-MM-DD")
    p_flight.add_argument("--from-airport", help="出发机场代码（可选）")
    p_flight.add_argument("--to-airport", help="到达机场代码（可选）")
    p_flight.add_argument("--cabin", default="ECONOMY", choices=["ECONOMY", "BUSINESS", "FIRST"], help="舱位等级")
    p_flight.add_argument("--trip-type", default="ONE_WAY", choices=["ONE_WAY", "ROUND_TRIP"], help="行程类型")
    p_flight.add_argument("--ret-date", help="返程日期（往返时必填）")
    p_flight.add_argument("--adults", type=int, default=1, help="成人数量")
    p_flight.add_argument("--children", type=int, default=0, help="儿童数量")

    # search_airports
    p_airport = sub.add_parser("airport", help="搜索机场/城市代码")
    p_airport.add_argument("--keyword", required=True, help="搜索关键词")

    args = parser.parse_args()

    if args.command == "search":
        print(search_flights(
            from_city=args.from_city,
            to_city=args.to_city,
            from_date=args.date,
            from_airport=args.from_airport,
            to_airport=args.to_airport,
            cabin_grade=args.cabin,
            trip_type=args.trip_type,
            ret_date=args.ret_date,
            adult_number=args.adults,
            child_number=args.children,
        ))
    elif args.command == "airport":
        print(search_airports(args.keyword))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
