# -*- coding: utf-8 -*-
"""
智能旅行规划 - ClawHub技能脚本
以行程规划为核心，12合1一站式旅行服务
数据源：飞猪旅行（SCF代理）+ 高德地图（SCF代理），零配置
"""
import json
import re
import urllib.request
import urllib.error

# ============ 配置 ============
FLIGGY_PROXY = "https://1439498936-6sysdjjt99.ap-guangzhou.tencentscf.com"
GAODE_PROXY = "https://1439498936-bl10af74fl.ap-guangzhou.tencentscf.com"
PROXY_TOKEN = "tp_8k2mX9vQ4z"
FLIGGY_TIMEOUT = 60
GAODE_TIMEOUT = 15

_CITIES = [
    "北京", "上海", "广州", "深圳", "成都", "杭州", "南京", "武汉", "长沙", "重庆",
    "西安", "厦门", "青岛", "大连", "昆明", "丽江", "桂林", "苏州", "珠海", "海口",
    "三亚", "天津", "济南", "沈阳", "哈尔滨", "长春", "郑州", "合肥", "福州", "南昌",
    "太原", "石家庄", "贵阳", "南宁", "兰州", "银川", "呼和浩特", "乌鲁木齐", "拉萨",
    "无锡", "宁波", "温州", "烟台", "威海", "佛山", "东莞", "中山", "惠州", "扬州",
]


# ============ 代理调用 ============
def _call_fliggy(rtype, params):
    """调用飞猪SCF代理"""
    body = json.dumps({"type": rtype, "params": params}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(
        FLIGGY_PROXY, data=body,
        headers={"Content-Type": "application/json", "X-Proxy-Token": PROXY_TOKEN},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=FLIGGY_TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = ""
        try: err = e.read().decode("utf-8", errors="replace")[:300]
        except: pass
        return {"error": "proxy error " + str(e.code) + ": " + err}
    except Exception as e:
        return {"error": "request error: " + str(e)}


def _call_gaode(api, params):
    """调用高德SCF代理，自动解包data层"""
    body = json.dumps({"type": api, "params": params}).encode("utf-8")
    req = urllib.request.Request(
        GAODE_PROXY, data=body,
        headers={"Content-Type": "application/json", "X-Proxy-Token": PROXY_TOKEN},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=GAODE_TIMEOUT) as r:
            data = json.loads(r.read().decode("utf-8"))
            if isinstance(data, dict) and data.get("code") == 0 and "data" in data:
                return data["data"]
            return data
    except urllib.error.HTTPError as e:
        err = ""
        try: err = e.read().decode("utf-8", errors="replace")[:200]
        except: pass
        return {"error": "proxy error " + str(e.code) + ": " + err}
    except Exception as e:
        return {"error": "request error: " + str(e)}


# ============ 高德通用 ============
def _gaode_geocode(address, city=""):
    params = {"address": address}
    if city: params["city"] = city
    data = _call_gaode("geocode", params)
    if isinstance(data, dict) and data.get("status") == "1":
        geocodes = data.get("geocodes", [])
        if geocodes:
            loc = geocodes[0].get("location", "")
            if loc and "," in loc:
                parts = loc.split(",")
                return (parts[0], parts[1])
    return (None, None)


def _gaode_food_search(location, keywords="", city="", radius=3000, limit=10):
    params = {"location": location, "types": "050000", "radius": radius, "sortrule": "weight", "offset": limit, "page": 1, "extensions": "all"}
    if keywords: params["keywords"] = keywords
    if city: params["city"] = city
    data = _call_gaode("poi_around", params)
    if isinstance(data, dict) and data.get("status") == "1":
        return data.get("pois", [])
    return []


def _gaode_driving(origin, destination, city):
    params = {"origin_address": origin, "origin_city": city, "destination_address": destination, "destination_city": city, "strategy": "0"}
    data = _call_gaode("driving_route_by_address", params)
    if isinstance(data, dict):
        paths = data.get("route", {}).get("paths", [])
        if paths:
            path = paths[0]
            distance = int(path.get("distance", 0) or 0)
            duration = int(path.get("duration", 0) or 0)
            taxi_cost_raw = data.get("route", {}).get("taxi_cost", "0")
            try:
                taxi_cost = "¥" + str(int(taxi_cost_raw)) + "左右"
            except:
                taxi_cost = _estimate_taxi_cost(distance)
            return {"distance_km": round(distance / 1000, 1), "duration_min": round(duration / 60), "taxi_cost": taxi_cost}
    return {}


def _gaode_transit(origin, destination, city):
    params = {"origin_address": origin, "origin_city": city, "destination_address": destination, "destination_city": city, "city": city, "strategy": "0"}
    data = _call_gaode("transit_route_by_address", params)
    if isinstance(data, dict):
        return data.get("route", {}).get("transits", [])
    return []


def _gaode_take_taxi(slon, slat, sname, dlon, dlat, dname):
    result = _call_gaode("schema_take_taxi", {"slon": slon, "slat": slat, "sname": sname, "dlon": dlon, "dlat": dlat, "dname": dname})
    if isinstance(result, dict) and "uri" in result:
        return result["uri"]
    return ""


# ============ 辅助 ============
def _estimate_taxi_cost(distance_m):
    distance_km = distance_m / 1000
    if distance_km <= 0: return "¥0"
    if distance_km <= 3: return "¥14左右"
    cost = 14 + (distance_km - 3) * 2.5
    return "¥" + str(int(cost)) + "左右"

def _is_metro_line(line_name):
    return any(kw in line_name for kw in ["地铁", "号线", "城轨", "磁浮", "市域", "轻轨"])

def _extract_city(query):
    for city in _CITIES:
        if city in query: return city
    return ""

def _extract_dest(query):
    m = re.search(r"去(.{2,8}?)(玩|旅游|旅行|度假|出差|住)", query)
    if m:
        dest = m.group(1).strip()
        dest = re.sub(r"\d+天?$", "", dest).strip()
        dest = re.sub(r"(的|了|一|两|附近|周边|景区|区域|一带)$", "", dest).strip()
        if len(dest) >= 2: return dest
    m = re.search(r"(.{2,6}?)(旅游|旅行|度假|游玩|周末游|亲子游|蜜月游|自由行)", query)
    if m:
        dest = m.group(1).strip()
        dest = re.sub(r"[\d天]+$", "", dest).strip()
        dest = re.sub(r"(去|到|的|了|附近|周边|景区|一带)$", "", dest).strip()
        if len(dest) >= 2: return dest
    return ""

def _build_tips(current_tool, dest=""):
    all_tools = [
        ("行程规划", "行程规划"), ("火车票查询", "火车票查询"), ("机票查询", "机票查询"),
        ("酒店搜索", "酒店搜索"), ("景点门票", "景点门票"), ("万豪酒店", "万豪酒店"),
        ("美食推荐", "美食推荐"), ("市内交通", "市内交通"), ("打车链接", "打车链接"),
        ("天气查询", "天气查询"),
    ]
    tips = []
    for tool_key, label in all_tools:
        if tool_key == current_tool: continue
        if dest:
            mapping = {
                "行程规划": "规划" + dest + "行程", "火车票查询": "查去" + dest + "的火车票",
                "机票查询": "查去" + dest + "的机票", "酒店搜索": "推荐" + dest + "酒店",
                "景点门票": "推荐" + dest + "景点", "万豪酒店": "搜索" + dest + "万豪酒店",
                "美食推荐": "推荐" + dest + "美食", "市内交通": dest + "市内交通",
                "打车链接": dest + "一键打车", "天气查询": dest + "天气预报",
            }
            tips.append(mapping.get(tool_key, label))
        else:
            tips.append(label)
    return "\n\n💡 我还能帮你：" + " | ".join(tips)

def _parse_flyai_text(data):
    if isinstance(data, str):
        if data.strip() == "" or data.strip() == "null": return None
        return data
    if isinstance(data, dict):
        if "error" in data: return "搜索失败: " + data["error"]
        if "raw_text" in data: return data["raw_text"]
        inner = data.get("data", data)
        if inner is None: inner = {}
        if isinstance(inner, str): return inner
        if isinstance(inner, dict):
            item_list = inner.get("itemList", [])
            if item_list: return _format_items(item_list)
            return json.dumps(inner, ensure_ascii=False, indent=2)
    return str(data)

def _normalize_item(item):
    info = item.get("info")
    if isinstance(info, dict):
        return {"name": info.get("title", ""), "price": info.get("price", ""), "jumpUrl": info.get("jumpUrl", ""),
                "address": info.get("address", ""), "star": info.get("star", ""), "scoreDesc": info.get("scoreDesc", ""),
                "ticketPrice": info.get("ticketPrice", ""), "detailUrl": info.get("detailUrl", "")}
    return {"name": item.get("name", item.get("title", "")), "price": item.get("price", item.get("ticketPrice", "")),
            "jumpUrl": item.get("jumpUrl", item.get("detailUrl", "")), "address": item.get("address", ""),
            "star": item.get("star", ""), "scoreDesc": item.get("scoreDesc", item.get("rating", "")),
            "ticketPrice": item.get("ticketPrice", ""), "detailUrl": item.get("detailUrl", "")}

def _format_items(items):
    lines = []
    for i, item in enumerate(items[:10], 1):
        it = _normalize_item(item)
        name = it["name"] or "未知"
        line = str(i) + ". " + name
        details = []
        if it.get("star") and str(it["star"]).strip(): details.append(str(it["star"]).strip())
        if it.get("scoreDesc") and str(it["scoreDesc"]).strip(): details.append("⭐" + str(it["scoreDesc"]).strip())
        if it.get("price") and str(it["price"]).strip(): details.append("¥" + str(it["price"]).strip() + "起")
        if details: line += "  " + " | ".join(details)
        lines.append(line)
        if it.get("address"): lines.append("   📍 " + it["address"])
        url = it.get("jumpUrl") or it.get("detailUrl", "")
        if url: lines.append("   🔗 " + url)
    return "\n".join(lines)

def _format_train_items(items):
    lines = []
    for i, item in enumerate(items[:10], 1):
        name = item.get("name", item.get("title", ""))
        dep_time = item.get("depDateTime", "")
        arr_time = item.get("arrDateTime", "")
        price = item.get("price", item.get("ticketPrice", ""))
        seat = item.get("seatClassName", "")
        duration = item.get("duration", "")
        line = str(i) + ". " + name
        if dep_time and arr_time: line += "  " + dep_time + "→" + arr_time
        if duration: line += " ⏱️" + duration
        if price: line += " ¥" + str(price)
        if seat: line += " " + seat
        lines.append(line)
    return "\n".join(lines)

def _format_flight_items(items):
    lines = []
    for i, item in enumerate(items[:10], 1):
        journeys = item.get("journeys", [])
        price = item.get("ticketPrice", "")
        url = item.get("jumpUrl", "")
        total_duration = item.get("totalDuration", "")
        if journeys:
            j = journeys[0]
            jtype = j.get("journeyType", "")
            segments = j.get("segments", [])
            if segments:
                s = segments[0]
                airline = s.get("marketingTransportName", "")
                flight_no = s.get("marketingTransportNo", "")
                dep = s.get("depStationShortName", s.get("depStationName", ""))
                dep_time = s.get("depDateTime", "").split(" ")[1][:5] if " " in s.get("depDateTime", "") else s.get("depDateTime", "")
                last_s = segments[-1]
                arr = last_s.get("arrStationShortName", last_s.get("arrStationName", ""))
                arr_time = last_s.get("arrDateTime", "").split(" ")[1][:5] if " " in last_s.get("arrDateTime", "") else last_s.get("arrDateTime", "")
                line = str(i) + ". " + airline + " " + flight_no + " [" + jtype + "]"
                lines.append(line)
                lines.append("   " + dep_time + " " + dep + " → " + arr_time + " " + arr + " (" + str(total_duration) + "min)")
                if price: lines.append("   ¥" + str(price))
                if url: lines.append("   🔗 " + url)
                lines.append("")
    return "\n".join(lines)


# ============ 工具函数 ============

def travel_plan(params):
    """行程规划：智能推荐行程方案，涵盖景点+酒店+交通。"""
    query = params.get("query", "")
    if not query: return "请描述你的旅行需求，如：3天2晚上海游"
    result = _call_fliggy("fliggy_ai_search", {"query": query})
    text = _parse_flyai_text(result)
    if text is None: return "未找到行程方案，建议换个描述试试"
    dest = _extract_dest(query) or _extract_city(query) or ""
    return text + _build_tips("行程规划", dest)


def search_train(params):
    """火车票查询：查询火车票/高铁票的余票、价格和时刻表。"""
    query = params.get("query", "")
    if not query: return "请描述火车票需求，如：北京到上海明天的火车"
    result = _call_fliggy("fliggy_ai_search", {"query": query})
    text = _parse_flyai_text(result)
    if text is None: return "未找到火车票信息，建议换个描述试试"
    dest = _extract_city(query) or ""
    return text + _build_tips("火车票查询", dest)


def search_flight(params):
    """机票查询：查询国内航班实时票价、航班号、起降时间。"""
    query = params.get("query", "")
    if not query: return "请描述机票需求，如：上海到三亚7月1号机票"
    result = _call_fliggy("fliggy_ai_search", {"query": query})
    text = _parse_flyai_text(result)
    if text is None: return "未找到航班信息，建议换个描述试试"
    dest = _extract_city(query) or ""
    return text + _build_tips("机票查询", dest)


def search_hotel(params):
    """酒店搜索：搜索酒店，返回实时价格和预订链接。"""
    query = params.get("query", "")
    if not query: return "请描述酒店需求，如：杭州西湖附近酒店"
    result = _call_fliggy("fliggy_ai_search", {"query": query})
    text = _parse_flyai_text(result)
    if text is None: return "未找到酒店信息，建议换个描述试试"
    dest = _extract_city(query) or ""
    return text + _build_tips("酒店搜索", dest)


def search_poi(params):
    """景点门票：搜索景点门票，返回门票价格和购票链接。"""
    query = params.get("query", "")
    if not query: return "请描述景点需求，如：上海迪士尼门票"
    result = _call_fliggy("fliggy_ai_search", {"query": query})
    text = _parse_flyai_text(result)
    if text is None: return "未找到景点信息，建议换个描述试试"
    dest = _extract_city(query) or ""
    return text + _build_tips("景点门票", dest)


def search_marriott_hotel(params):
    """万豪酒店搜索：搜索万豪集团旗下酒店。"""
    query = params.get("query", "")
    if not query: return "请描述万豪酒店需求，如：上海万豪酒店"
    result = _call_fliggy("search_marriott_hotels", {"query": query})
    text = _parse_flyai_text(result)
    if text is None:
        result = _call_fliggy("fliggy_ai_search", {"query": query + " 万豪"})
        text = _parse_flyai_text(result)
    if text is None: return "未找到万豪酒店信息"
    dest = _extract_city(query)
    return text + _build_tips("万豪酒店", dest)


def get_marriott_hotel_info(params):
    """万豪酒店详情：获取万豪酒店详细信息。"""
    query = params.get("query", "")
    if not query: return "请提供万豪酒店名称"
    result = _call_fliggy("get_marriott_hotel_info", {"query": query})
    if isinstance(result, dict) and result.get("status") == 1:
        result = _call_fliggy("fliggy_ai_search", {"query": query + " 详细信息"})
    text = _parse_flyai_text(result)
    if text is None: return "未找到该万豪酒店详情"
    return text


def search_marriott_package(params):
    """万豪套餐搜索：搜索万豪集团在售套餐商品。"""
    query = params.get("query", "")
    if not query: return "请描述万豪套餐需求"
    result = _call_fliggy("search_marriott_packages", {"query": query})
    inner = result.get("data", result) if isinstance(result, dict) else result
    if inner is None or (isinstance(result, dict) and result.get("status") == 0 and result.get("data") is None):
        result = _call_fliggy("fliggy_ai_search", {"query": query})
    text = _parse_flyai_text(result)
    if text is None: return "未找到万豪套餐信息"
    dest = _extract_city(query)
    return text + _build_tips("万豪酒店", dest)


def search_food(params):
    """美食推荐：基于位置搜索周边餐厅美食。"""
    query = params.get("query", "")
    if not query: return "请描述美食需求，如：上海南京路附近火锅"
    dest = _extract_dest(query) or _extract_city(query)
    city = _extract_city(query)
    if not dest: dest = query.strip()[:8]
    lng, lat = _gaode_geocode(dest, city)
    if not lng: return "无法解析「" + dest + "」的位置，请告诉我具体城市和地点"
    keywords = ""
    for kw in ["火锅", "日料", "粤菜", "烧烤", "咖啡", "甜品", "川菜", "湘菜", "西餐", "海鲜", "早茶", "小吃"]:
        if kw in query: keywords = kw; break
    pois = _gaode_food_search(location=lng + "," + lat, keywords=keywords, city=city or dest, radius=3000, limit=10)
    if not pois: return "未找到" + dest + "附近的餐厅" + _build_tips("美食推荐", dest)
    lines = ["🍜 找到 " + str(len(pois)) + " 家 " + dest + "附近餐厅：", ""]
    for i, poi in enumerate(pois, 1):
        name = poi.get("name", "未知")
        type_name = poi.get("type", "")
        cuisine = ""
        if type_name:
            parts = type_name.split(";")
            if len(parts) >= 2: cuisine = parts[1]
        cuisine_tag = " [" + cuisine + "]" if cuisine else ""
        rating = poi.get("rating", "") or (poi.get("biz_ext", {}) or {}).get("rating", "")
        cost = poi.get("cost", "") or (poi.get("biz_ext", {}) or {}).get("cost", "")
        address = poi.get("address", "")
        lines.append(str(i) + ". " + name + cuisine_tag)
        detail_parts = []
        if rating and rating not in ("0", "-1"): detail_parts.append("⭐" + str(rating))
        if cost and cost not in ("0", "-1"): detail_parts.append("人均¥" + str(cost))
        if detail_parts: lines.append("   " + " | ".join(detail_parts))
        if address: lines.append("   📍 " + address)
        lines.append("")
    lines.append("💡 评分和价格仅供参考，建议出发前电话确认")
    return "\n".join(lines) + _build_tips("美食推荐", city or dest)


def search_transport(params):
    """市内交通：查询从A到B的打车预估和公交地铁路线。"""
    query = params.get("query", "")
    if not query: return "请描述交通需求，如：上海浦东机场到外滩"
    city = _extract_city(query)
    m = re.search(r"(.{2,15}?)到(.{2,15})", query)
    if not m: return "请说明出发地和目的地，如：浦东机场到外滩（上海）" + _build_tips("市内交通")
    origin = m.group(1).strip()
    destination = m.group(2).strip()
    for c in _CITIES:
        if origin.startswith(c): origin = origin[len(c):].strip(); break
    if not city: return "请告诉我城市名" + _build_tips("市内交通")

    lines = ["📍 " + origin + " → " + destination + " 交通方式", ""]

    driving = _gaode_driving(origin, destination, city)
    taxi_uri = ""
    if driving:
        lines.append("━━━ 🚗 打车/驾车 ━━━")
        lines.append("距离" + str(driving["distance_km"]) + "公里 | 约" + str(driving["duration_min"]) + "分钟 | " + driving["taxi_cost"])
        origin_lng, origin_lat = _gaode_geocode(origin, city)
        dest_lng, dest_lat = _gaode_geocode(destination, city)
        if origin_lng and dest_lng:
            taxi_uri = _gaode_take_taxi(slon=origin_lng, slat=origin_lat, sname=origin, dlon=dest_lng, dlat=dest_lat, dname=destination)
            if taxi_uri:
                lines.append("🚕 一键打车：点击直接跳高德APP打车 → " + taxi_uri)
        lines.append("")

    transit_routes = _gaode_transit(origin, destination, city)
    if transit_routes:
        real_metro = []
        real_bus = []
        for route in transit_routes:
            is_metro = False
            for seg in route.get("segments", []):
                for bl in seg.get("bus", {}).get("buslines", []):
                    if _is_metro_line(bl.get("name", "")): is_metro = True; break
            if is_metro: real_metro.append(route)
            else: real_bus.append(route)

        if real_metro:
            lines.append("━━━ 🚇 地铁/城轨 ━━━")
            for i, route in enumerate(real_metro[:2], 1):
                duration = int(route.get("duration", 0) or 0)
                cost = route.get("cost", "0")
                all_lines = []
                for seg in route.get("segments", []):
                    for bl in seg.get("bus", {}).get("buslines", []):
                        name = bl.get("name", "").split("(")[0]
                        dep = bl.get("departure_stop", {}).get("name", "")
                        arr = bl.get("arrival_stop", {}).get("name", "")
                        all_lines.append({"name": name, "dep": dep, "arr": arr})
                cost_str = "¥" + cost if cost and cost != "0" else ""
                line_names = " → ".join(l["name"] for l in all_lines)
                detail_parts = ["约" + str(round(duration / 60)) + "分钟"]
                if cost_str: detail_parts.append(cost_str)
                lines.append("方案" + str(i) + ": " + line_names + " | " + " ".join(detail_parts))
                for l in all_lines:
                    if l["dep"] or l["arr"]:
                        lines.append("  " + l["name"] + ": " + l["dep"] + "→" + l["arr"])
            lines.append("")

        if real_bus:
            lines.append("━━━ 🚌 公交 ━━━")
            for i, route in enumerate(real_bus[:2], 1):
                duration = int(route.get("duration", 0) or 0)
                cost = route.get("cost", "0")
                all_lines = []
                for seg in route.get("segments", []):
                    for bl in seg.get("bus", {}).get("buslines", []):
                        all_lines.append(bl.get("name", "").split("(")[0])
                cost_str = "¥" + cost if cost and cost != "0" else ""
                line_names = " → ".join(all_lines)
                detail_parts = ["约" + str(round(duration / 60)) + "分钟"]
                if cost_str: detail_parts.append(cost_str)
                lines.append("方案" + str(i) + ": " + line_names + " | " + " ".join(detail_parts))
            lines.append("")

    if not driving and not transit_routes:
        return "未找到合适的交通方案，建议使用地图APP导航。" + _build_tips("市内交通", city)
    lines.append("💡 以上时间和费用为预估值，实际可能因路况变化")
    return "\n".join(lines) + _build_tips("市内交通", city)


def search_weather(params):
    """天气查询：查询目的地天气预报，辅助行程安排。"""
    query = params.get("query", "")
    if not query: return "请输入城市名查询天气，如：三亚天气预报"
    city = _extract_city(query)
    if not city:
        dest = _extract_dest(query)
        if dest:
            for c in _CITIES:
                if dest.startswith(c) or c.startswith(dest): city = c; break
        if not city: return "请告诉我城市名" + _build_tips("天气查询")

    result = _call_gaode("weather", {"city": city, "extensions": "all"})
    if not isinstance(result, dict): return "天气查询失败，请稍后重试" + _build_tips("天气查询", city)
    forecasts = result.get("forecasts", [])
    if not forecasts: return "未找到" + city + "的天气预报" + _build_tips("天气查询", city)

    forecast = forecasts[0]
    city_name = forecast.get("city", city)
    casts = forecast.get("casts", [])
    lines = ["🌤️ " + city_name + " 天气预报", ""]
    for cast in casts[:5]:
        date = cast.get("date", "")
        week = cast.get("week", "")
        dayweather = cast.get("dayweather", "")
        nightweather = cast.get("nightweather", "")
        daytemp = cast.get("daytemp", "")
        nighttemp = cast.get("nighttemp", "")
        daywind = cast.get("daywind", "")
        daypower = cast.get("daypower", "")
        weather_str = dayweather
        if nightweather and nightweather != dayweather:
            weather_str = dayweather + "转" + nightweather
        temp_str = nighttemp + "°~" + daytemp + "°" if nighttemp and daytemp else ""
        wind_str = ""
        if daywind and daypower: wind_str = daywind + daypower + "级"
        line = date + "（" + week + "） " + weather_str + " " + temp_str
        if wind_str: line = line + " " + wind_str
        lines.append(line)
    lines.append("")
    lines.append("💡 天气仅供参考，出行前请再次确认")
    return "\n".join(lines) + _build_tips("天气查询", city)


def take_taxi_link(params):
    """打车链接：生成高德一键打车链接。"""
    query = params.get("query", "")
    if not query: return "请描述打车需求，如：从浦东机场到外滩（上海）"
    city = _extract_city(query)
    m = re.search(r"(.{2,15}?)到(.{2,15})", query)
    if not m: return "请说明出发地和目的地"
    origin = m.group(1).strip()
    destination = m.group(2).strip()
    for c in _CITIES:
        if origin.startswith(c): origin = origin[len(c):].strip(); break
    if not city: return "请告诉我城市名"
    origin_lng, origin_lat = _gaode_geocode(origin, city)
    dest_lng, dest_lat = _gaode_geocode(destination, city)
    if not origin_lng or not dest_lng: return "无法解析位置，请用更具体的地址"
    uri = _gaode_take_taxi(slon=origin_lng, slat=origin_lat, sname=origin, dlon=dest_lng, dlat=dest_lat, dname=destination)
    if uri:
        return "🚕 一键打车链接：点击直接跳高德APP打车 → " + uri + "\n\n" + "📍 " + origin + " → " + destination + "（" + city + "）"
    return "无法生成打车链接，请尝试用地图APP手动叫车" + _build_tips("打车链接", city)
