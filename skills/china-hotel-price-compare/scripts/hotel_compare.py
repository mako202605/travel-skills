# -*- coding: utf-8 -*-
"""酒店比价 - 多平台酒店实时价格对比"""
import argparse, json, re, urllib.request, urllib.error, concurrent.futures
from datetime import datetime, timedelta

# 代理配置
PROXY_URL = "https://1439498936-58nanx6r2r.ap-guangzhou.tencentscf.com"
def _token():
    """代理认证令牌（用于请求OTA平台的代理服务鉴权）"""
    return "tp_8k2mX9vQ4z"

PNAME = {"rg":"RollingGo","tuniu":"途牛","tongcheng":"同程","meituan":"美团","fliggy":"飞猪","ctrip":"携程"}
PORDER = ["rg","fliggy","tuniu","tongcheng","meituan","ctrip"]
# 佣金优先级：RG(5%) > 飞猪(推广者计划) > 其他
COMMISSION_PRIORITY = {"rg": 0, "fliggy": 1, "tuniu": 2, "tongcheng": 3, "meituan": 4, "ctrip": 5}
STAR_MAP = {"五星级":["五星级","豪华型","5星"],"高档型":["高档型","四星级","4星"],"舒适型":["舒适型","三星级","3星"],"经济型":["经济型","二星级","1星","2星"]}

BRANDS = ["华尔道夫","威斯汀","丽思卡尔顿","瑞吉","半岛","四季","文华东方","宝格丽","安缦","悦榕庄","费尔蒙","柏悦","康莱德","洲际","皇冠假日","JW万豪","W酒店","艾美","喜来登","万丽","万怡","君悦","索菲特","铂尔曼","凯宾斯基","朗廷","瑰丽","卓美亚","尼依格罗","英迪格","美爵","假日","全季","亚朵","维也纳","桔子水晶","丽枫","喆啡","美居","宜必思","康铂","诺富特","逸扉","花间堂","如家商旅","如家","汉庭","锦江之星","7天","海友","莫泰","格林豪泰","速8","锦江","金陵","开元","万达嘉华","希尔顿","万豪","凯悦","雅高"]
BRANDS.sort(key=len, reverse=True)
LUXURY = {"华尔道夫","威斯汀","丽思卡尔顿","瑞吉","半岛","四季","文华东方","宝格丽","安缦","悦榕庄","费尔蒙","柏悦","康莱德","W酒店","索菲特","铂尔曼","凯宾斯基","朗廷","瑰丽","卓美亚","尼依格罗"}
CITIES = ["上海","北京","广州","深圳","杭州","成都","南京","苏州","重庆","武汉","西安","天津","长沙","青岛","大连","厦门","昆明","三亚"]
NO_LOC = {"酒店","宾馆","公寓","客栈","民宿","饭店","大酒店","店"}
LOC_RE = re.compile(r'(外滩|豫园|新天地|陆家嘴|[\u4e00-\u9fff]{2,6}[路街道区湾桥]|[\u4e00-\u9fff]{2,6}广场|地铁站|火车站|机场)')
SPEC_RE = re.compile(r'[路街道区店]')
LANDMARKS = {"上海":["外滩","南京路","陆家嘴","迪士尼"],"北京":["三里屯","王府井","天安门","国贸"],"广州":["珠江新城","北京路","天河城","白云机场"],"深圳":["福田CBD","华强北","南山科技园"],"杭州":["西湖","灵隐寺","钱江新城"],"成都":["春熙路","太古里","宽窄巷子"],"南京":["新街口","夫子庙","中山陵"],"三亚":["亚龙湾","海棠湾","天涯海角"],"重庆":["解放碑","洪崖洞","观音桥"],"武汉":["江汉路","光谷","黄鹤楼"],"西安":["钟楼","大雁塔","回民街"],"长沙":["五一广场","橘子洲","坡子街"]}

# ===== 代理调用 =====
def call_proxy(source, api_type, params):
    """调用SCF代理，返回原始响应体"""
    body = json.dumps({"source": source, "type": api_type, "params": params}, ensure_ascii=False)
    req = urllib.request.Request(PROXY_URL, data=body.encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Proxy-Token": _token()}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            result = json.loads(r.read().decode("utf-8"))
        if result.get("code") != 0 or result.get("error"):
            return {"error": result.get("error", "proxy error")}
        return {"raw": result.get("data", ""), "content_type": result.get("content_type", "")}
    except Exception as e:
        return {"error": str(e)}

def _mcp_result(result):
    if "error" in result:
        return {"error": str(result["error"].get("message", result["error"]))[:200]}
    content = result.get("result",{}).get("content",[])
    if content and isinstance(content, list) and len(content) > 0:
        f = content[0]
        if isinstance(f, dict) and f.get("type") == "text":
            t = f.get("text","")
            if "Error executing tool" in t: return {"error": t[:200]}
            try: return json.loads(t)
            except: return {"raw_text": t}
    sc = result.get("result",{}).get("structuredContent")
    if sc: return sc
    return {"error": "无法解析响应"}

def _parse_mcp(raw, content_type):
    """解析MCP协议响应"""
    try:
        if "text/event-stream" in content_type:
            for line in raw.split("\n"):
                if line.startswith("data:"):
                    return _mcp_result(json.loads(line[5:].strip()))
        return _mcp_result(json.loads(raw))
    except:
        return {"error": "parse fail"}

def _clean(name):
    name = re.sub(r'\s*\([A-Za-z][^)]*\)', '', name).strip()
    while name and name[-1] in ')）':
        if (name.count('(')+name.count('（')) < (name.count(')')+name.count('）')):
            name = name[:-1].rstrip()
        else: break
    return name.strip()

# ===== 各源数据解析 =====

def _parse_rg(proxy_resp, city, ci, co, kw):
    data = _parse_mcp(proxy_resp.get("raw",""), proxy_resp.get("content_type",""))
    if "error" in data or "hotelInformationList" not in data: return []
    hotels = []
    for h in data.get("hotelInformationList",[])[:20]:
        pi = h.get("price",{})
        p = pi.get("lowestPrice")
        if p is None or not pi.get("hasPrice"): continue
        name = _clean(h.get("name",""))
        if not name: continue
        hotels.append({"name":name,"price":float(p),"address":h.get("address",""),"latitude":h.get("latitude"),"longitude":h.get("longitude"),"star":h.get("starRating",""),"source":"rg","url":h.get("bookingUrl",""),"brand":h.get("brand") or ""})
    return hotels

def _parse_tuniu(proxy_resp, city, ci, co, kw):
    data = _parse_mcp(proxy_resp.get("raw",""), proxy_resp.get("content_type",""))
    if "error" in data: return []
    hl = data.get("hotels") or data.get("hotelList") or (data if isinstance(data,list) else [])
    if not isinstance(hl,list): return []
    hotels = []
    for h in hl[:15]:
        name = _clean(h.get("hotelName") or h.get("name",""))
        if not name: continue
        try: p = float(re.sub(r"[^\d.]","",str(h.get("lowestPrice") or h.get("price") or "0")))
        except: p = 0
        if p <= 0: continue
        hotels.append({"name":name,"price":p,"address":h.get("address") or h.get("hotelAddress",""),"latitude":h.get("latitude"),"longitude":h.get("longitude"),"star":h.get("starName") or h.get("star",""),"source":"tuniu","url":h.get("detailUrl") or h.get("url","") or (f"https://hotel.tuniu.com/detail/{h.get("hotelId","")}" if h.get("hotelId") else ""),"brand":h.get("brandName") or ""})
    return hotels

def _parse_tongcheng(proxy_resp, city, ci, co, kw):
    raw = proxy_resp.get("raw","")
    err = proxy_resp.get("error")
    if err: return []
    try:
        result = json.loads(raw)
        if result.get("code") != "0": return []
        text = result.get("data",{}).get("text","")
        links = result.get("data",{}).get("产品跳转链接",{})
    except: return []
    hotels = []
    pats = [
        re.compile(r'^([^，。\n]+?)\s+距[\u4e00-\u9fff]+直线\d+[米公里]*，\s*评分[\s：:]*(\d+\.?\d*)[，,]?\s*价格[\s：:]*(\d+[\d,.]*)\s*元',re.M),
        re.compile(r'^([^，。\n]+?)\s+.*?评分[\s：:]*(\d+\.?\d*).*?价格[\s：:]*(\d+[\d,.]*)\s*元',re.M),
        re.compile(r'^([^，。\n]+?)\s+.*?价格[\s：:]*(\d+[\d,.]*)\s*元',re.M),
    ]
    for para in text.split("\n\n"):
        para = para.strip()
        if not para or any(s in para for s in ["出行建议","客服电话","建议入住"]): continue
        name, pv = "", 0.0
        for pat in pats:
            m = pat.match(para)
            if m:
                name = _clean(m.group(1).strip())
                try: pv = float(m.group(m.lastindex).replace(",",""))
                except: pv = 0
                break
        if not name or pv <= 0: continue
        url = ""
        for lk, ld in links.items():
            if name in lk or lk in name:
                url = (ld.get("手机链接") or ld.get("PC链接","")) if isinstance(ld, dict) else ""
                break
        hotels.append({"name":name,"price":pv,"address":"","latitude":None,"longitude":None,"star":"","source":"tongcheng","url":url,"brand":""})
    return hotels[:15]

def _parse_meituan(proxy_resp, city, ci, co, kw):
    raw = proxy_resp.get("raw","")
    err = proxy_resp.get("error")
    if err: return []
    try: result = json.loads(raw)
    except: return []
    if result.get("code") != 0: return []
    data = result.get("data","")
    if not isinstance(data, str): return []
    hotels = []
    p1 = re.compile(r'\[\*\*(.+?)\*\*\]\(([^)]+)\).*?￥(\d{3,}[\d,.]*)\s*(?:起|/晚|共)',re.DOTALL)
    for m in p1.finditer(data):
        name = _clean(m.group(1).replace("\\(","(").replace("\\)",")"))
        if not name: continue
        try: p = float(m.group(3).replace(",",""))
        except: continue
        if p <= 0: continue
        star = ""
        sm = re.search(r'(豪华型|高档型|舒适型|经济型|五星级|四星级|三星级)', m.group(0))
        if sm: star = sm.group(1)
        hotels.append({"name":name,"price":p,"address":"","latitude":None,"longitude":None,"star":star,"source":"meituan","url":m.group(2).strip(),"brand":""})
    if not hotels:
        p2 = re.compile(r'\*\*(.+?)\*\*[^￥]*?￥(\d{3,}[\d,.]*)\s*(?:起|/晚|共)',re.DOTALL)
        seen = set()
        for m in p2.finditer(data):
            name = _clean(m.group(1).replace("\\(","(").replace("\\)",")"))
            if not name or name in seen: continue
            try: p = float(m.group(2).replace(",",""))
            except: continue
            if p <= 0: continue
            seen.add(name)
            star = ""
            sm = re.search(r'(豪华型|高档型|舒适型|经济型)', m.group(0))
            if sm: star = sm.group(1)
            hotels.append({"name":name,"price":p,"address":"","latitude":None,"longitude":None,"star":star,"source":"meituan","url":"","brand":""})
    return [h for h in hotels if h["price"] >= 20][:15]

def _parse_fliggy(proxy_resp, city, ci, co, kw):
    raw = proxy_resp.get("raw","")
    err = proxy_resp.get("error")
    if err: return []
    try:
        d = json.loads(raw)
        ct = d.get("result",{}).get("content",[])
        if not ct: return []
        inner = json.loads(ct[0].get("text","{}"))
    except: return []
    if "error" in inner: return []
    d2 = inner.get("data") or inner
    if not isinstance(d2, dict): return []
    il = d2.get("itemList",[]) or []
    hotels = []
    for h in il[:15]:
        name = _clean(h.get("name",""))
        if not name: continue
        try: p = float(re.sub(r"[^\d.]","",str(h.get("price","0"))))
        except: p = 0
        if p <= 0: continue
        hotels.append({"name":name,"price":p,"address":h.get("address",""),"latitude":h.get("latitude"),"longitude":h.get("longitude"),"star":h.get("star",""),"source":"fliggy","url":h.get("detailUrl",""),"brand":h.get("brandName") or ""})
    return hotels

# ===== 品牌匹配 =====
def _brand(name):
    c = re.sub(r'[\(（][^)）]*[\)）]', '', name)
    for b in BRANDS:
        if b in c: return b
    return ""

def _loc_tokens(name, brand=""):
    bc = re.findall(r'[\(（]([^)）]+)[\)）]', name)
    b_locs = []
    for b in bc:
        b = b.replace("金标","").strip()
        if b and b not in NO_LOC:
            for c in CITIES:
                if b.startswith(c): b = b[len(c):]; break
            parts = LOC_RE.split(b)
            meaningful = [p.strip() for p in parts if len(p.strip())>=2 and p.strip() not in NO_LOC]
            b_locs.extend(meaningful if meaningful else [b])
    c = re.sub(r'[\(（][^)）]*[\)）]', '', name)
    if brand and brand in c: c = c.replace(brand,"",1)
    for ci in CITIES:
        if c.startswith(ci): c = c[len(ci):]; break
    for sfx in ["国际酒店","大酒店","酒店","宾馆","公寓","客栈","民宿","饭店"]:
        if c.endswith(sfx) and len(c)>len(sfx): c = c[:-len(sfx)]; break
    c = c.replace("·"," ").replace("—"," ").replace("-"," ").replace("金标","")
    raw = [t.strip() for t in re.split(r'[\s,，、]',c) if len(t.strip())>=2 and t.strip() not in NO_LOC]
    all_t = set(raw + b_locs)
    fine = set()
    for t in all_t:
        parts = LOC_RE.split(t)
        meaningful = [p.strip() for p in parts if len(p.strip())>=2 and p.strip() not in NO_LOC]
        fine.update(meaningful if meaningful else [t])
    return list(fine)

def _sim(n1, n2):
    b1, b2 = _brand(n1), _brand(n2)
    l1, l2 = _loc_tokens(n1, b1), _loc_tokens(n2, b2)
    if b1 and b2:
        if b1 != b2: return 0.0
        if b1 in LUXURY: return 0.9
        if not l1 or not l2: return 0.4
        ov = set(l1) & set(l2)
        sp = [t for t in ov if SPEC_RE.search(t)]
        gn = [t for t in ov if not SPEC_RE.search(t)]
        if sp: return 0.85
        if len(gn) >= 2:
            if any(SPEC_RE.search(t) for t in set(l1)-ov) and any(SPEC_RE.search(t) for t in set(l2)-ov): return 0.0
            return 0.7
        if gn:
            if any(SPEC_RE.search(t) for t in set(l1)-ov) and any(SPEC_RE.search(t) for t in set(l2)-ov): return 0.0
            return 0.45
        return 0.0
    if b1 and not b2:
        return (0.8 if (l1 and l2 and set(l1)&set(l2)) else 0.35) if b1 in n2 else 0.0
    if b2 and not b1:
        return (0.8 if (l1 and l2 and set(l1)&set(l2)) else 0.35) if b2 in n1 else 0.0
    s1, s2 = set(l1), set(l2)
    if s1 and s2:
        ov = len(s1 & s2)
        un = len(s1 | s2)
        if un > 0:
            sim = ov / un
            if ov >= 2 and sim >= 0.4: return 0.7
            if ov >= 1 and sim >= 0.5: return 0.6
        for t1 in l1:
            for t2 in l2:
                if t1 in t2 or t2 in t1:
                    if SPEC_RE.search(t1) or SPEC_RE.search(t2): return 0.5
                    return 0.30
    cn1 = re.sub(r'[\(（][^)）]*[\)）]','',n1).lower()
    cn2 = re.sub(r'[\(（][^)）]*[\)）]','',n2).lower()
    if cn1 in cn2 or cn2 in cn1: return 0.5
    return 0.0

def _is_relevant(name, addr, kw):
    if not kw or len(kw) < 2: return True
    nl, al = name.lower(), (addr or "").lower()
    if kw in nl or kw in al: return True
    for t in re.split(r'[附近周边左右]', kw):
        t = t.strip()
        if len(t) >= 2 and (t in nl or t in al): return True
    b = _brand(nl)
    if b and b in kw: return True
    return False

# ===== 跨平台匹配 =====
def _match(all_hotels):
    if not all_hotels: return []
    by_src = {}
    for h in all_hotels: by_src.setdefault(h["source"],[]).append(h)
    srcs = list(by_src.keys())
    if len(srcs) == 1:
        return [{"name":h["name"],"platforms":{srcs[0]:h},"min_price":h["price"],"platform_count":1} for h in by_src[srcs[0]]]
    used = {s: set() for s in srcs}
    matched = []
    srcs_sorted = sorted(srcs, key=lambda s: len(by_src[s]), reverse=True)
    base = srcs_sorted[0]
    for bh in by_src[base]:
        grp = {base: bh}
        used[base].add(id(bh))
        for s in srcs:
            if s == base: continue
            best, best_sim = None, 0.35
            for oh in by_src[s]:
                if id(oh) in used[s]: continue
                sim = _sim(bh["name"], oh["name"])
                if sim > 0.25 and bh.get("latitude") and oh.get("latitude"):
                    try:
                        if abs(float(bh["latitude"])-float(oh["latitude"]))<0.005 and abs(float(bh["longitude"])-float(oh["longitude"]))<0.005:
                            sim = max(sim, 0.6)
                    except: pass
                if sim > best_sim: best_sim = sim; best = oh
            if best: grp[s] = best; used[s].add(id(best))
        prices = [h["price"] for h in grp.values() if h["price"]>0]
        matched.append({"name":bh["name"],"platforms":grp,"min_price":min(prices) if prices else 0,"platform_count":len(grp)})
    remaining = {}
    for s in srcs:
        if s == base: continue
        rem = [h for h in by_src[s] if id(h) not in used[s]]
        if rem: remaining[s] = rem
    if remaining:
        rem_srcs = sorted(remaining.keys(), key=lambda s: len(remaining[s]), reverse=True)
        rem_used = set()
        for base_s in rem_srcs:
            for bh in remaining[base_s]:
                if id(bh) in rem_used: continue
                grp = {base_s: bh}
                rem_used.add(id(bh))
                for s in rem_srcs:
                    if s == base_s: continue
                    best, best_sim = None, 0.35
                    for oh in remaining[s]:
                        if id(oh) in rem_used: continue
                        sim = _sim(bh["name"], oh["name"])
                        if sim > 0.25 and bh.get("latitude") and oh.get("latitude"):
                            try:
                                if abs(float(bh["latitude"])-float(oh["latitude"]))<0.005 and abs(float(bh["longitude"])-float(oh["longitude"]))<0.005:
                                    sim = max(sim, 0.6)
                            except: pass
                        if sim > best_sim: best_sim = sim; best = oh
                    if best: grp[s] = best; rem_used.add(id(best))
                prices = [h["price"] for h in grp.values() if h["price"]>0]
                matched.append({"name":bh["name"],"platforms":grp,"min_price":min(prices) if prices else 0,"platform_count":len(grp)})
    return matched

def _filter(matched, max_price=0, star_level=""):
    f = matched
    if max_price and max_price > 0: f = [h for h in f if h["min_price"] <= max_price]
    if star_level:
        allowed = STAR_MAP.get(star_level, [star_level])
        r = []
        for h in f:
            ms, no_info = False, True
            for ph in h["platforms"].values():
                sv = str(ph.get("star",""))
                if sv:
                    no_info = False
                    if any(a in sv for a in allowed): ms = True; break
            if ms or no_info: r.append(h)
        f = r
    return f

def _star_val(hotel):
    for s in PORDER:
        if s in hotel["platforms"]:
            sv = str(hotel["platforms"][s].get("star",""))
            m = re.search(r'(\d+\.?\d*)', sv)
            if m:
                try: return float(m.group(1))
                except: pass
            if "五" in sv or "豪华" in sv: return 5.0
            if "四" in sv or "高档" in sv: return 4.0
            if "舒适" in sv or "三" in sv: return 3.0
            if "经济" in sv: return 2.0
    return 0.0

def _disparity(hotel):
    if hotel["platform_count"] < 2: return False
    prices = [h["price"] for h in hotel["platforms"].values() if h["price"] > 0]
    return len(prices) >= 2 and max(prices) / min(prices) > 3.0

def _format(matched, city, ci, co, kw, max_price=0, star_level="", sort_by="price", has_date=True, failed_srcs=None):
    if sort_by == "rating":
        matched.sort(key=lambda x: (-x["platform_count"],-_star_val(x),x["min_price"]))
    else:
        matched.sort(key=lambda x: (-x["platform_count"],x["min_price"]))
    multi_all = [h for h in matched if h["platform_count"]>=2]
    single_all = [h for h in matched if h["platform_count"]==1]
    multi = multi_all[:8]
    single = single_all[:2]
    dest = f"{city}{kw}" if kw else city
    total = len(matched)
    show_count = len(multi) + len(single)
    lines = [f"🏨 **{dest}** 酒店比价（{ci}~{co}）"]
    lines.append(f"📊 共找到{total}家酒店，当前展示{show_count}家")
    lines.append("")
    tags = []
    if max_price: tags.append(f"预算≤¥{max_price}")
    if star_level: tags.append(star_level)
    if tags: lines.append(f"筛选：{' | '.join(tags)}"); lines.append("")
    idx = 0
    for h in multi:
        idx += 1
        pc = h["platform_count"]
        tag = f"  {pc}家平台比价" if pc>=3 else f"  仅{pc}家平台有报价"
        lines.append(f"**{idx}. {h['name']}**{tag}")
        # 排序：价格升序，同价按佣金优先级（RG>飞猪>其他）
        sorted_p = sorted(h["platforms"].items(),
            key=lambda x: (x[1]["price"] if x[1]["price"] > 0 else 99999, COMMISSION_PRIORITY.get(x[0], 99)))
        parts = []
        lowest_url = ""
        for i, (s, ph) in enumerate(sorted_p):
            p = ph["price"]
            ps = f"¥{int(p)}起" if s == "meituan" and p > 0 else (f"¥{int(p)}" if p > 0 else "—")
            label = f"{PNAME[s]} {ps}"
            if i == 0:
                label = f"💰 {label}最低价"
                url = ph.get("url", "")
                if url: lowest_url = f" [去预订→]({url})"
            parts.append(label)
        lines.append("   " + " | ".join(parts) + lowest_url)
        # 价差异常提醒
        prices = [(s, ph["price"]) for s, ph in sorted_p if ph["price"] > 0]
        if len(prices) >= 2:
            lowest_s, lowest_p = prices[0]
            second_p = prices[1][1]
            if lowest_p < second_p * 0.4:
                lines.append(f"   ⚠️ {PNAME.get(lowest_s, '')}价格异常偏低，可能非标准间")
            elif _disparity(h):
                lines.append("   ⚠️ 价差较大，建议核实")
        lines.append("")
    if single:
        lines.append("---"); lines.append("📌 更多酒店（仅单平台报价）"); lines.append("")
        for h in single:
            idx += 1
            s = list(h["platforms"].keys())[0]
            p = h["platforms"][s]["price"]
            ps = f"¥{int(p)}起" if s=="meituan" and p>0 else f"¥{int(p)}"
            url = h["platforms"][s].get("url", "")
            link = f" [去预订→]({url})" if url else ""
            lines.append(f"**{idx}. {h['name']}**  {PNAME[s]} {ps}{link}"); lines.append("")
    lines.append("美团为起步价（不含日期） | 携程数据暂未接入 | 价格实时变动，以实际预订为准")
    if failed_srcs:
        fnames = "、".join(PNAME.get(s, s) for s in failed_srcs if s in PNAME)
        if fnames:
            lines.append(f"⚠️ {fnames}本次未返回数据，实际可比平台可能更多")
    tips = []
    if not has_date: tips.append("💡 如需其他日期，告诉入住和离店时间即可重搜")
    total = len(matched)
    lm = LANDMARKS.get(city,["市中心","火车站"])
    refine_hint = "💡 缩小范围：加区域或地标（如" + "、".join(lm[:3]) + "）、预算（如¥500以内）、星级（如五星级）、品牌（如万豪）"
    if total > 10:
        tips.append(refine_hint)
    elif not (kw and len(kw)>=2):
        tips.append(refine_hint)
    mp_count = len([h for h in matched if h["platform_count"] >= 2])
    if mp_count >= 3:
        tips.append(f"💡 共{mp_count}家酒店有多平台比价，标💰的为最低价")
    if mp_count < 3 and kw: tips.append("💡 多平台比价结果较少，换个关键词或扩大区域可能有更多发现")
    if tips: lines.append(""); lines.extend(tips)
    return "\n".join(lines)

# ===== 主入口 =====
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True)
    parser.add_argument("--check-in", default="")
    parser.add_argument("--check-out", default="")
    parser.add_argument("--keyword", default="")
    parser.add_argument("--max-price", type=int, default=0)
    parser.add_argument("--star-level", default="")
    parser.add_argument("--sort-by", default="price")
    args = parser.parse_args()

    city = args.city
    ci = args.check_in
    co = args.check_out
    kw = args.keyword if args.keyword and args.keyword != "None" else ""
    mp = args.max_price or 0
    sl = args.star_level if args.star_level and args.star_level != "None" else ""
    sb = args.sort_by if args.sort_by and args.sort_by != "None" else "price"
    has_date = bool(ci and ci not in ("","None"))
    if not ci or ci=="None": ci=(datetime.now()+timedelta(days=1)).strftime("%Y-%m-%d")
    if not co or co=="None": co=(datetime.now()+timedelta(days=2)).strftime("%Y-%m-%d")
    try:
        d1=datetime.strptime(ci,"%Y-%m-%d"); d2=datetime.strptime(co,"%Y-%m-%d")
        if d1<datetime.now().replace(hour=0,minute=0,second=0,microsecond=0):
            print(f"❌ 入住日期{ci}已过期"); return
        if d2<=d1:
            print(f"❌ 离店日期({co})必须晚于入住日期({ci})"); return
    except ValueError:
        print("❌ 日期格式不正确，请使用YYYY-MM-DD格式"); return

    # 通过代理并行查询5个数据源
    all_hotels = []
    src_results = {}

    def fetch_source(source, parse_fn, params):
        try:
            proxy_resp = call_proxy(source, "hotel", params)
            if "error" in proxy_resp and "raw" not in proxy_resp:
                return source, [], False
            hotels = parse_fn(proxy_resp, city, ci, co, kw)
            return source, hotels, bool(hotels)
        except:
            return source, [], False

    common_params = {"city": city, "check_in": ci, "check_out": co, "keyword": kw}

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        futs = {
            ex.submit(fetch_source, "rg", _parse_rg, common_params): "rg",
            ex.submit(fetch_source, "tuniu", _parse_tuniu, common_params): "tuniu",
            ex.submit(fetch_source, "tongcheng", _parse_tongcheng, common_params): "tongcheng",
            ex.submit(fetch_source, "meituan", _parse_meituan, common_params): "meituan",
            ex.submit(fetch_source, "fliggy", _parse_fliggy, common_params): "fliggy",
        }
        for f in concurrent.futures.as_completed(futs, timeout=70):
            src = futs[f]
            try:
                _, hotels, ok = f.result(timeout=40)
                if hotels:
                    all_hotels.extend(hotels)
                src_results[src] = ok
            except:
                src_results[src] = False

    failed_srcs = [s for s, ok in src_results.items() if not ok]
    if not all_hotels:
        print(f"未找到{city}的酒店数据，建议稍后重试或补充区域关键词"); return
    if kw and len(kw)>=2:
        rel = [h for h in all_hotels if _is_relevant(h["name"],h.get("address",""),kw)]
        if len(rel)>=5: all_hotels=rel
    matched = _match(all_hotels)
    if not matched:
        print(f"未找到{city}的可比价酒店，建议换关键词或补充区域"); return
    matched = _filter(matched, mp, sl)
    if not matched:
        bh = f"，预算≤¥{mp}" if mp else ""
        sh = f"，{sl}" if sl else ""
        print(f"未找到{city}{bh}{sh}的酒店，试试放宽预算或星级要求"); return
    print(_format(matched, city, ci, co, kw, mp, sl, sb, has_date, failed_srcs))

if __name__ == "__main__":
    main()
