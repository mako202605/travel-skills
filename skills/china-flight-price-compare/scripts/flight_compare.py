# -*- coding: utf-8 -*-
"""机票比价 - 多旅游平台直飞航班实时对比"""
import argparse, json, re, urllib.request, urllib.error, concurrent.futures
from datetime import datetime

PROXY_URL = "https://1439498936-htmug3p43j.ap-guangzhou.tencentscf.com"
PROXY_TOKEN = "tp_8k2mX9vQ4z"

PNAME = {"fliggy":"飞猪","tuniu":"途牛","meituan":"美团","rg":"RG","tongcheng":"同程"}
# 佣金优先级：RG(5%) > 飞猪(推广者计划) > 其他
COMMISSION_PRIORITY = {"rg": 0, "fliggy": 1, "tuniu": 2, "tongcheng": 3, "meituan": 4}

AIRLINE_MAP = {
    "CA":"国航","MU":"东航","CZ":"南航","HU":"海航","9C":"春秋","HO":"吉祥",
    "ZH":"深航","MF":"厦航","SC":"山航","3U":"川航","FM":"上航","GS":"天津航",
    "PN":"西部航","G5":"华夏航","EU":"成都航","NS":"河北航","AQ":"九元航",
    "KY":"昆明航","JR":"幸福航","D7":"首都航","TV":"西藏航","FU":"福航",
    "RY":"江西航","GJ":"长龙航","KN":"联航","LT":"龙江航","OQ":"重庆航",
    "Y8":"扬子江航","NX":"澳航","CX":"国泰","BR":"长荣","CI":"中华航",
    "NH":"全日空","JL":"日航","KE":"大韩","OZ":"韩亚","TG":"泰航",
    "FD":"泰亚航","SQ":"新航","TR":"酷航","MH":"马航","AK":"亚航",
    "VN":"越航","VJ":"越捷","BA":"英航","LH":"汉莎","AF":"法航",
    "KL":"荷航","EK":"阿联酋","EY":"阿提哈德","QR":"卡塔尔","TK":"土航",
    "SU":"俄航","AA":"美航","UA":"美联航","DL":"达美","QF":"澳航","NZ":"纽航",
}

CITY_CODE = {"上海":"SHA","北京":"PEK","广州":"CAN","深圳":"SZX","成都":"CTU",
    "重庆":"CKG","杭州":"HGH","南京":"NKG","武汉":"WUH","西安":"XIY",
    "长沙":"CSX","郑州":"CGO","昆明":"KMG","厦门":"XMN","青岛":"TAO",
    "大连":"DLC","哈尔滨":"HRB","沈阳":"SHE","天津":"TSN","海口":"HAK",
    "三亚":"SYX","贵阳":"KWE","南宁":"NNG","兰州":"LHW","太原":"TYN",
    "合肥":"HFE","福州":"FOC","南昌":"KHN","石家庄":"SJW","长春":"CGQ",
    "呼和浩特":"HET","乌鲁木齐":"URC","拉萨":"LXA","西宁":"XNN","银川":"INC"}

IATA_PORT = {
    "SHA":"虹桥","PVG":"浦东","PEK":"首都","PKX":"大兴","CAN":"白云",
    "SZX":"宝安","CTU":"双流","TFU":"天府","CKG":"江北","HGH":"萧山",
    "NKG":"禄口","WUH":"天河","XIY":"咸阳","CSX":"黄花","CGO":"新郑",
    "KMG":"长水","XMN":"高崎","TAO":"胶东","DLC":"周水子","HRB":"太平",
    "SHE":"桃仙","TSN":"滨海","HAK":"美兰","SYX":"凤凰","KWE":"龙洞堡",
    "NNG":"吴圩","LHW":"中川","TYN":"武宿","HFE":"新桥","FOC":"长乐",
    "KHN":"昌北","SJW":"正定","CGQ":"龙嘉","HET":"白塔","URC":"地窝堡",
    "LXA":"贡嘎","XNN":"曹家堡","INC":"河东",
}

def _airline_name(fn):
    if not fn: return ""
    m = re.match(r'^([A-Z0-9]{2})', fn.upper())
    return AIRLINE_MAP.get(m.group(1), m.group(1)) if m else fn

def _clean_airline(name):
    if not name: return ""
    for sep in ["｜","|"]:
        if sep in name:
            name = name.split(sep)[-1].strip()
    return name

def _fmt_time(t):
    if not t: return ""
    t = str(t).strip()
    m = re.search(r'(\d{1,2}:\d{2})', t)
    return m.group(1) if m else t[:5]

def _fmt_duration(d):
    if not d: return ""
    d = str(d).strip()
    if re.match(r'^\d+h\d+m$', d): return d
    if d.isdigit():
        h, m = divmod(int(d), 60)
        return f"{h}h{m:02d}m" if m else f"{h}h"
    return d

def call_proxy(source, params, timeout=40):
    """调用flight-proxy2(v3)，返回纯JSON data"""
    body = json.dumps({"source": source, "params": params}, ensure_ascii=False)
    req = urllib.request.Request(PROXY_URL, data=body.encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Proxy-Token": PROXY_TOKEN}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            result = json.loads(r.read().decode("utf-8"))
        if result.get("code") != 0 or result.get("error"):
            return {"error": result.get("error", "proxy error")}
        return result.get("data", {})
    except Exception as e:
        return {"error": str(e)}

def _tuniu_flight_url(from_city, to_city, date):
    tuniu_city = {"北京":"beijing","上海":"shanghai","广州":"guangzhou","深圳":"shenzhen",
        "成都":"chengdu","杭州":"hangzhou","南京":"nanjing","武汉":"wuhan","西安":"xian",
        "重庆":"chongqing","长沙":"changsha","郑州":"zhengzhou","昆明":"kunming",
        "厦门":"xiamen","青岛":"qingdao","大连":"dalian","哈尔滨":"haerbin","沈阳":"shenyang",
        "天津":"tianjin","海口":"haikou","三亚":"sanya","贵阳":"guiyang","南宁":"nanning"}
    fc = tuniu_city.get(from_city, "")
    tc = tuniu_city.get(to_city, "")
    if fc and tc:
        return f"https://flight.tuniu.com/{fc}-{tc}/{date.replace('-','')}"
    return ""

def _parse_fliggy(data, from_city, to_city, date):
    """飞猪：data = {"data":{"itemList":[...]}, ...}"""
    if isinstance(data, dict) and "error" in data: return []
    try:
        d2 = data.get("data") if isinstance(data, dict) else None
        if not d2: return []
        if "itemList" not in d2:
            # 兼容：data可能直接就是内层
            if "itemList" in data:
                d2 = data
            else:
                return []
    except: return []
    il = d2.get("itemList", []) or []
    flights = []
    for item in il[:30]:
        for j in item.get("journeys", []):
            if "中转" in str(j.get("journeyType", "")): continue
            segs = j.get("segments", [])
            if not segs: continue
            seg = segs[0]
            fn = seg.get("marketingTransportNo", "")
            if not fn: continue
            tp = item.get("ticketPrice", 0)
            price = 0
            if isinstance(tp, dict):
                price = tp.get("adultPrice", 0) or tp.get("price", 0)
            elif isinstance(tp, (str, int, float)):
                try: price = float(tp)
                except: price = 0
            url = item.get("jumpUrl", "")
            if fn and price > 0:
                flights.append({"flight_no": fn.upper().replace(" ", ""),
                    "airline": _clean_airline(_airline_name(fn)),
                    "dep_time": _fmt_time(seg.get("depDateTime", "")),
                    "arr_time": _fmt_time(seg.get("arrDateTime", "")),
                    "dep_port": seg.get("depStationShortName", ""),
                    "arr_port": seg.get("arrStationShortName", ""),
                    "cabin": seg.get("seatClassName", "经济舱"),
                    "duration": _fmt_duration(j.get("totalDuration", "") or seg.get("duration", "")),
                    "price": price, "source": "fliggy", "url": url})
    return flights[:20]

def _parse_tuniu(data, from_city, to_city, date):
    """途牛：data = {"data":[...], ...} 或 data = [...]"""
    if isinstance(data, dict) and "error" in data: return []
    try:
        fl = data.get("data", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        if not isinstance(fl, list):
            fl = data.get("flightList", []) if isinstance(data, dict) else []
        if not isinstance(fl, list): return []
    except: return []
    flights = []
    for f in fl[:20]:
        fn = f.get("flightNumber", "")
        if not fn or "中转" in str(f.get("type", "")): continue
        price = f.get("basePrice", 0)
        try: price = float(price)
        except: price = 0
        if fn and price > 0:
            flights.append({"flight_no": fn.upper().replace(" ", ""),
                "airline": _clean_airline(f.get("airlineCompany", "") or _airline_name(fn)),
                "dep_time": _fmt_time(f.get("departureTime", "")),
                "arr_time": _fmt_time(f.get("arrivalTime", "")),
                "dep_port": f.get("departureAirport", ""),
                "arr_port": f.get("arrivalAirport", ""),
                "cabin": f.get("cabinClass", "经济舱"),
                "duration": _fmt_duration(f.get("totalDuration", "") or f.get("flyTime", "")),
                "price": price, "source": "tuniu",
                "url": _tuniu_flight_url(from_city, to_city, date)})
    return flights

def _parse_meituan(data, from_city, to_city, date):
    """美团：data = 字符串(Markdown含航班信息)"""
    if isinstance(data, dict) and "error" in data: return []
    raw = data if isinstance(data, str) else ""
    if not raw: return []
    # 美团忙不过来
    if "忙不过来" in raw or "success" in raw: return []
    try:
        # data可能是JSON字符串
        d = json.loads(raw) if raw.startswith("{") else None
        if d and isinstance(d, dict):
            inner_data = d.get("data", "")
            if isinstance(inner_data, str):
                raw = inner_data
            elif isinstance(inner_data, dict):
                return []  # 非预期格式
    except: pass
    flights = []; seen = set()
    p1 = re.compile(r'\[([^\]]*?([A-Z]{2}\d{3,4})[^\]]*?(\d{1,2}:\d{2})\s*[→\-~—]\s*(\d{1,2}:\d{2})[^\]]*?[￥¥](\d{1,5})[^\]]*?)\]\(([^)]+)\)')
    for m in p1.finditer(raw):
        fn = m.group(2).upper().replace(" ", "")
        if fn in seen: continue
        seen.add(fn)
        try:
            price = float(m.group(5))
            if price <= 0: continue
            flights.append({"flight_no": fn,
                "airline": _clean_airline(_airline_name(fn)),
                "dep_time": m.group(3), "arr_time": m.group(4),
                "dep_port": "", "arr_port": "",
                "cabin": "经济舱", "duration": "",
                "price": price, "source": "meituan", "url": m.group(6)})
        except: continue
    # 备用正则：纯文本格式
    p2 = re.compile(r'([A-Z]{2}\d{3,4})\s+.*?(\d{1,2}:\d{2})\s*[→\-~—]\s*(\d{1,2}:\d{2}).*?[￥¥](\d+)')
    for m in p2.finditer(raw):
        fn = m.group(1).upper().replace(" ", "")
        if fn in seen: continue
        seen.add(fn)
        try:
            price = float(m.group(4))
            if price <= 0: continue
            flights.append({"flight_no": fn,
                "airline": _clean_airline(_airline_name(fn)),
                "dep_time": m.group(2), "arr_time": m.group(3),
                "dep_port": "", "arr_port": "",
                "cabin": "经济舱", "duration": "",
                "price": price, "source": "meituan", "url": ""})
        except: continue
    return flights

def _parse_tongcheng(data, from_city, to_city, date):
    """同程：data = {"code":"0","data":{...}}"""
    if isinstance(data, dict) and "error" in data: return []
    try:
        if isinstance(data, str):
            data = json.loads(data)
        if not isinstance(data, dict): return []
        if data.get("code") not in ["0", 0]: return []
        inner = data.get("data", {}) or {}
        text = inner.get("text", "")
        links = inner.get("产品跳转链接", {}) or {}
        struct_flights = inner.get("__tc_struct_flights", [])
    except: return []
    flights = []; seen = set()
    if isinstance(struct_flights, list):
        for f in struct_flights:
            fn = (f.get("flightNo") or "").upper().replace(" ", "")
            if not fn or fn in seen: continue
            if "TRANSFER" in str(f.get("tripType", "")): continue
            price = f.get("price", 0)
            try: price = float(price)
            except: price = 0
            dep_port = f.get("depAirportShortName", "") or f.get("depAirportName", "")
            arr_port = f.get("arrAirportShortName", "") or f.get("arrAirportName", "")
            dt = f.get("depAirportTerminal", "")
            at = f.get("arrAirportTerminal", "")
            if dt: dep_port += dt
            if at: arr_port += at
            if fn and price > 0:
                seen.add(fn)
                flights.append({"flight_no": fn,
                    "airline": _clean_airline(f.get("airlineShortName", "") or _airline_name(fn)),
                    "dep_time": f.get("depTime", ""), "arr_time": f.get("arrTime", ""),
                    "dep_port": dep_port, "arr_port": arr_port, "cabin": "经济舱",
                    "duration": f.get("runTime", ""), "price": price,
                    "source": "tongcheng", "url": f.get("redirectUrl", "")})
    if text:
        p = re.compile(r'([A-Z0-9]{2}\d{3,4})\s+([^\s→]+?)(T\d)?\s+(\d{1,2}:\d{2})[→\-]\s*([^\s，]+?)(T\d)?\s+(\d{1,2}:\d{2})[，,].*?(?:经济舱)?(\d+)元')
        for m in p.finditer(text):
            fn = m.group(1).upper().replace(" ", "")
            if fn in seen: continue
            seen.add(fn)
            dep_port = (m.group(2) or "").strip()
            arr_port = (m.group(5) or "").strip()
            if m.group(3): dep_port += m.group(3)
            if m.group(6): arr_port += m.group(6)
            try: price = float(m.group(8))
            except: continue
            if price <= 0: continue
            url = ""
            fl = links.get(fn, {})
            if isinstance(fl, dict): url = fl.get("手机链接", "") or fl.get("PC链接", "")
            flights.append({"flight_no": fn, "airline": _clean_airline(_airline_name(fn)),
                "dep_time": m.group(4), "arr_time": m.group(7) or "",
                "dep_port": dep_port, "arr_port": arr_port,
                "cabin": "经济舱", "duration": "", "price": price,
                "source": "tongcheng", "url": url})
    return flights

def _parse_rg(data, from_city, to_city, date):
    """RG：data = {"flightInformationList":[...], ...}"""
    if isinstance(data, dict) and "error" in data: return []
    if isinstance(data, str):
        try: data = json.loads(data)
        except: return []
    if not isinstance(data, dict): return []
    fallback_date = data.get("__rg_fallback_date")
    fl = data.get("flightInformationList", [])
    if not isinstance(fl, list): return []
    target_codes = set()
    code = CITY_CODE.get(to_city, "")
    if code: target_codes.add(code)
    multi = {"北京": {"PEK", "PKX"}, "上海": {"SHA", "PVG"}, "成都": {"CTU", "TFU"}}
    if to_city in multi: target_codes.update(multi[to_city])
    flights = []
    for f in fl[:60]:
        segs = f.get("fromSegments", [])
        if not segs or len(segs) > 1: continue
        seg = segs[0]
        fn = seg.get("flightNumber", "")
        if not fn: continue
        arr_code = seg.get("arrAirport", "")
        if target_codes and arr_code not in target_codes: continue
        carrier = f.get("validatingCarrier", "")
        price = f.get("totalAdultPrice", 0)
        try: price = float(price)
        except: price = 0
        cabin = "全价经济舱" if price > 1500 else "经济舱"
        if fn and price > 0:
            fdict = {"flight_no": fn.upper().replace(" ", ""),
                "airline": _clean_airline(_airline_name(carrier) if carrier else _airline_name(fn)),
                "dep_time": _fmt_time(seg.get("depTime", "")),
                "arr_time": _fmt_time(seg.get("arrTime", "")),
                "dep_port": IATA_PORT.get(seg.get("depAirport", ""), seg.get("depAirport", "")),
                "arr_port": IATA_PORT.get(seg.get("arrAirport", ""), seg.get("arrAirport", "")),
                "cabin": cabin, "duration": _fmt_duration(seg.get("duration", "")),
                "price": price, "source": "rg", "url": f.get("bookingUrl", "")}
            if fallback_date: fdict["fallback_date"] = fallback_date
            flights.append(fdict)
    return flights[:20]

def _match_flights(all_flights):
    by_fn = {}
    for f in all_flights:
        fn = f["flight_no"]
        if fn not in by_fn: by_fn[fn] = {}
        src = f["source"]
        if src in by_fn[fn]:
            if f["price"] < by_fn[fn][src]["price"]: by_fn[fn][src] = f
        else: by_fn[fn][src] = f
    result = []
    for fn, platforms in by_fn.items():
        prices = [f["price"] for f in platforms.values() if f["price"] > 0]
        if not prices: continue
        min_price = min(prices)
        # 同价优先选有佣金的：RG>飞猪>其他
        best_src = min(platforms.keys(),
            key=lambda s: (platforms[s]["price"], COMMISSION_PRIORITY.get(s, 99)))
        rep = platforms[best_src]
        result.append({"flight_no": fn, "airline": rep["airline"],
            "dep_time": rep["dep_time"], "arr_time": rep["arr_time"],
            "dep_port": rep["dep_port"], "arr_port": rep["arr_port"],
            "cabin": rep["cabin"], "duration": rep["duration"],
            "platforms": platforms, "min_price": min_price, "platform_count": len(platforms),
            "best_source": best_src})
    return result

def _format(flights, from_city, to_city, date, failed_srcs=None, rg_fallback=False):
    flights.sort(key=lambda x: (-x["platform_count"], x["min_price"]))
    multi = [f for f in flights if f["platform_count"] >= 2][:8]
    single = [f for f in flights if f["platform_count"] == 1][:5]
    total = len(flights)
    show_count = len(multi) + len(single)
    lines = [f"✈️ **{from_city}→{to_city}** {date} 机票比价", ""]
    lines.append(f"📊 共找到{total}个航班，当前展示{show_count}个")
    lines.append("")
    idx = 0
    for f in multi:
        idx += 1
        dt = f["dep_time"] or "--:--"
        at = f["arr_time"] or "--:--"
        dur = f"  {f['duration']}" if f["duration"] else ""
        ports = ""
        dp, ap = f["dep_port"], f["arr_port"]
        if dp and ap: ports = f"  {dp}→{ap}"
        elif dp: ports = f"  {dp}出发"
        pc = f["platform_count"]
        tag = f"  ✅{pc}家比价" if pc >= 3 else f"  {pc}家比价"
        lines.append(f"**{idx}. {f['airline']} {f['flight_no']}**  {dt}-{at}{dur}{ports}{tag}")
        sorted_p = sorted(f["platforms"].items(),
            key=lambda x: (x[1]["price"] if x[1]["price"] > 0 else 99999, COMMISSION_PRIORITY.get(x[0], 99)))
        parts = []
        lowest_url = ""
        for i, (s, ph) in enumerate(sorted_p):
            p = ph["price"]
            cabin_note = "（全价）" if ph.get("cabin") == "全价经济舱" else ""
            ps = f"¥{int(p)}起" if s == "meituan" and p > 0 else (f"¥{int(p)}{cabin_note}" if p > 0 else "—")
            label = f"{PNAME[s]} {ps}"
            if i == 0:
                label = f"💰 {label}最低价"
                url = ph.get("url", "")
                if url: lowest_url = f" [去预订→]({url})"
            parts.append(label)
        lines.append("   " + " | ".join(parts) + lowest_url)
        prices = [(s, ph["price"]) for s, ph in sorted_p if ph["price"] > 0]
        if len(prices) >= 2:
            lowest_s, lowest_p = prices[0]
            second_p = prices[1][1]
            highest_p = prices[-1][1]
            if lowest_p < second_p * 0.4:
                lines.append(f"   ⚠️ {PNAME.get(lowest_s, '')}价格异常偏低，可能不含税费")
            elif highest_p / lowest_p > 3.0:
                lines.append("   ⚠️ 价差较大，建议核实")
        lines.append("")
    if single:
        lines.append("---")
        lines.append("📌 更多航班（仅单平台报价）")
        lines.append("")
        for f in single:
            idx += 1
            dt = f["dep_time"] or "--:--"
            at = f["arr_time"] or "--:--"
            s = list(f["platforms"].keys())[0]
            p = f["platforms"][s]["price"]
            cabin_note = "（全价）" if f["platforms"][s].get("cabin") == "全价经济舱" else ""
            ps = f"¥{int(p)}起" if s == "meituan" else f"¥{int(p)}{cabin_note}"
            url = f["platforms"][s].get("url", "")
            link = f" [去预订→]({url})" if url else ""
            lines.append(f"**{idx}. {f['airline']} {f['flight_no']}**  {dt}-{at}  {PNAME[s]} {ps}{link}")
            lines.append("")
    lines.append("仅展示直飞航班 | 美团为起步价 | RG全价票为参考价 | 价格实时变动，以实际预订为准")
    if rg_fallback:
        lines.append("⏰ RG当天航班数据暂不可用，已自动查询次日航班供参考")
    if failed_srcs:
        fnames = "、".join(PNAME.get(s, s) for s in failed_srcs if s in PNAME)
        if fnames: lines.append(f"⚠️ {fnames}本次未返回数据，实际可比平台可能更多")
    tips = []
    mp = len(multi)
    if mp >= 3: tips.append(f"💡 共{mp}个航班有多平台比价，标💰的为最低价")
    if total > 8: tips.append("💡 缩小范围：加时段（早班/上午/下午/晚班）、航司（国航/东航/南航）、价格上限（¥XXX内）、出发机场")
    if tips: lines.append(""); lines.extend(tips)
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-city", required=True)
    parser.add_argument("--to-city", required=True)
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    from_city, to_city, date = args.from_city, args.to_city, args.date
    if not from_city or not to_city or not date:
        print("❌ 请提供出发城市、到达城市和出发日期"); return
    try:
        d = datetime.strptime(date, "%Y-%m-%d")
        if d < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
            print(f"❌ 出发日期{date}已过期"); return
    except ValueError:
        print("❌ 日期格式不正确，请使用YYYY-MM-DD格式"); return
    all_flights = []; src_results = {}; rg_fallback = False
    def fetch_source(source, parse_fn, params):
        try:
            data = call_proxy(source, params)
            if isinstance(data, dict) and "error" in data and "flightInformationList" not in data and "data" not in data:
                return source, [], False
            flights = parse_fn(data, from_city, to_city, date)
            return source, flights, bool(flights)
        except: return source, [], False
    common_params = {"from_city": from_city, "to_city": to_city, "date": date}
    rg_params = {**common_params, "from_city_code": CITY_CODE.get(from_city, from_city), "to_city_code": CITY_CODE.get(to_city, to_city)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        futs = {
            ex.submit(fetch_source, "fliggy", _parse_fliggy, common_params): "fliggy",
            ex.submit(fetch_source, "tuniu", _parse_tuniu, common_params): "tuniu",
            ex.submit(fetch_source, "tongcheng", _parse_tongcheng, common_params): "tongcheng",
            ex.submit(fetch_source, "meituan", _parse_meituan, common_params): "meituan",
            ex.submit(fetch_source, "rg", _parse_rg, rg_params): "rg",
        }
        for f in concurrent.futures.as_completed(futs, timeout=70):
            src = futs[f]
            try:
                _, flights, ok = f.result(timeout=40)
                if flights:
                    all_flights.extend(flights)
                    if src == "rg":
                        for fl in flights:
                            if fl.get("fallback_date"): rg_fallback = True; break
                src_results[src] = ok
            except: src_results[src] = False
    failed_srcs = [s for s, ok in src_results.items() if not ok]
    if not all_flights:
        print(f"未找到{from_city}→{to_city} {date}的航班数据，建议稍后重试"); return
    matched = _match_flights(all_flights)
    if not matched:
        print(f"未找到{from_city}→{to_city} {date}的可比价航班"); return
    print(_format(matched, from_city, to_city, date, failed_srcs, rg_fallback))

if __name__ == "__main__":
    main()
