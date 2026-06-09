#!/usr/bin/env python3
"""途牛旅行助手 v1.1 - 酒店/机票/火车票/景点门票全品类查询预订
零配置即装即用，15个工具覆盖途牛全品类API"""

import sys
import json
import urllib.request
import urllib.error

PROXY_URL = "https://1439498936-0junm3maxj.ap-guangzhou.tencentscf.com"


def _token():
    """代理认证令牌（用于请求途牛API的代理服务鉴权）"""
    return "tp_8k2mX9vQ4z"


def _post(type_name, params):
    """调用途牛代理"""
    body = json.dumps({"type": type_name, "params": params}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(PROXY_URL, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Proxy-Token", _token())
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("code") == 0:
                return data.get("data", {})
            return data
    except urllib.error.HTTPError as e:
        err = ""
        try:
            err = e.read().decode("utf-8")[:300]
        except:
            pass
        return {"error": "HTTP " + str(e.code) + ": " + err}
    except Exception as e:
        return {"error": str(e)}


# ==================== 酒店工具 ====================

def tool_tuniu_hotel_search(params):
    """途牛酒店搜索：按城市+日期搜索酒店，支持关键词/商圈/翻页"""
    if "cityName" not in params and "queryId" not in params:
        return {"error": "首页查询需传cityName，翻页查询需传queryId+pageNum"}
    return _post("tuniu_hotel_search", params)


def tool_tuniu_hotel_detail(params):
    """途牛酒店详情：查看酒店房型+报价，返回preBookParam用于下单"""
    if "hotelId" not in params and "hotelName" not in params:
        return {"error": "需传hotelId或hotelName"}
    return _post("tuniu_hotel_detail", params)


def tool_tuniu_hotel_create_order(params):
    """途牛酒店下单：基于hotel_detail返回的preBookParam预订酒店"""
    for r in ["hotelId", "roomId", "preBookParam", "checkInDate", "checkOutDate",
              "roomCount", "roomGuests", "contactName", "contactPhone"]:
        if r not in params:
            return {"error": "缺少必填参数: " + r}
    if not params.get("confirm"):
        return {"warning": "此操作将创建酒店订单，可能产生费用。请确认后设置 confirm=true 再次调用", "required_fields": list(params.keys())}
    params = {k: v for k, v in params.items() if k != "confirm"}
    return _post("tuniu_hotel_create_order", params)


# ==================== 机票工具 ====================

def tool_tuniu_flight_search(params):
    """途牛机票搜索：按出发/到达城市+日期搜索航班，支持6种查询模式"""
    for r in ["departureCityName", "arrivalCityName", "departureDate"]:
        if r not in params:
            return {"error": "缺少必填参数: " + r}
    return _post("tuniu_flight_search", params)


def tool_tuniu_flight_cabin_detail(params):
    """途牛机票舱位详情：查看航班各舱位价格，返回cabinPriceId用于下单"""
    for r in ["departureCityName", "arrivalCityName", "departureDate", "flightNo"]:
        if r not in params:
            return {"error": "缺少必填参数: " + r}
    return _post("tuniu_flight_cabin_detail", params)


def tool_tuniu_flight_booking_info(params):
    """途牛机票预订信息：获取下单时必填字段说明"""
    return _post("tuniu_flight_booking_info", params)


def tool_tuniu_flight_save_order(params):
    """途牛机票下单：基于舱位详情的cabinPriceId预订机票"""
    for r in ["departureCityName", "arrivalCityName", "departureDate", "flightNo", "cabinPriceId", "tourists"]:
        if r not in params:
            return {"error": "缺少必填参数: " + r}
    if not params.get("confirm"):
        return {"warning": "此操作将创建机票订单，可能产生费用。请确认后设置 confirm=true 再次调用", "required_fields": list(params.keys())}
    params = {k: v for k, v in params.items() if k != "confirm"}
    return _post("tuniu_flight_save_order", params)


def tool_tuniu_flight_cancel_order(params):
    """途牛机票取消订单"""
    if "orderId" not in params:
        return {"error": "缺少orderId"}
    if not params.get("confirm"):
        return {"warning": "此操作将取消机票订单，可能产生退款或费用。请确认后设置 confirm=true 再次调用", "order_id": params["orderId"]}
    params = {k: v for k, v in params.items() if k != "confirm"}
    return _post("tuniu_flight_cancel_order", params)


# ==================== 火车票工具 ====================

def tool_tuniu_train_search(params):
    """途牛火车票搜索：按出发/到达城市+日期搜索车次，支持6种排序"""
    if "departureCityName" not in params and "queryId" not in params:
        return {"error": "首页查询需传departureCityName，翻页查询需传queryId"}
    return _post("tuniu_train_search", params)


def tool_tuniu_train_detail(params):
    """途牛火车票车次详情：查看座位余票+价格，返回resId用于预订"""
    for r in ["departureStationName", "arrivalStationName", "departureDate", "trainNum"]:
        if r not in params:
            return {"error": "缺少必填参数: " + r}
    return _post("tuniu_train_detail", params)


def tool_tuniu_train_book(params):
    """途牛火车票预订：基于车次详情的resId预订火车票"""
    for r in ["resources", "adultTourists", "contact"]:
        if r not in params:
            return {"error": "缺少必填参数: " + r}
    if not params.get("confirm"):
        return {"warning": "此操作将创建火车票订单，可能产生费用。请确认后设置 confirm=true 再次调用", "required_fields": list(params.keys())}
    params = {k: v for k, v in params.items() if k != "confirm"}
    return _post("tuniu_train_book", params)


def tool_tuniu_train_order_detail(params):
    """途牛火车票订单详情"""
    if "orderId" not in params:
        return {"error": "缺少orderId"}
    return _post("tuniu_train_order_detail", params)


def tool_tuniu_train_cancel_order(params):
    """途牛火车票取消订单"""
    if "orderId" not in params:
        return {"error": "缺少orderId"}
    if not params.get("confirm"):
        return {"warning": "此操作将取消火车票订单，可能产生退款或费用。请确认后设置 confirm=true 再次调用", "order_id": params["orderId"]}
    params = {k: v for k, v in params.items() if k != "confirm"}
    return _post("tuniu_train_cancel_order", params)


# ==================== 门票工具 ====================

def tool_tuniu_ticket_query(params):
    """途牛景点门票查询：按景点名搜索门票价格"""
    if "scenic_name" not in params:
        return {"error": "缺少scenic_name"}
    return _post("tuniu_ticket_query", params)


def tool_tuniu_ticket_create_order(params):
    """途牛门票下单：基于门票查询的productId+resId预订门票"""
    for r in ["product_id", "resource_id", "depart_date", "adult_num",
              "contact_name", "contact_mobile", "tourist_1_name",
              "tourist_1_mobile", "tourist_1_cert_type", "tourist_1_cert_no"]:
        if r not in params:
            return {"error": "缺少必填参数: " + r}
    if not params.get("confirm"):
        return {"warning": "此操作将创建门票订单，可能产生费用。请确认后设置 confirm=true 再次调用", "required_fields": list(params.keys())}
    params = {k: v for k, v in params.items() if k != "confirm"}
    return _post("tuniu_ticket_create_order", params)


# ==================== 工具路由 ====================

TOOLS = {
    # 酒店
    "tuniu_hotel_search": tool_tuniu_hotel_search,
    "tuniu_hotel_detail": tool_tuniu_hotel_detail,
    "tuniu_hotel_create_order": tool_tuniu_hotel_create_order,
    # 机票
    "tuniu_flight_search": tool_tuniu_flight_search,
    "tuniu_flight_cabin_detail": tool_tuniu_flight_cabin_detail,
    "tuniu_flight_booking_info": tool_tuniu_flight_booking_info,
    "tuniu_flight_save_order": tool_tuniu_flight_save_order,
    "tuniu_flight_cancel_order": tool_tuniu_flight_cancel_order,
    # 火车票
    "tuniu_train_search": tool_tuniu_train_search,
    "tuniu_train_detail": tool_tuniu_train_detail,
    "tuniu_train_book": tool_tuniu_train_book,
    "tuniu_train_order_detail": tool_tuniu_train_order_detail,
    "tuniu_train_cancel_order": tool_tuniu_train_cancel_order,
    # 门票
    "tuniu_ticket_query": tool_tuniu_ticket_query,
    "tuniu_ticket_create_order": tool_tuniu_ticket_create_order,
}


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "用法: python3 tuniu_travel.py <tool> '<json_params>'", "available_tools": list(TOOLS.keys())}, ensure_ascii=False))
        sys.exit(1)

    tool_name = sys.argv[1]
    try:
        params = json.loads(sys.argv[2])
    except json.JSONDecodeError as e:
        print(json.dumps({"error": "参数JSON解析失败: " + str(e)}, ensure_ascii=False))
        sys.exit(1)

    if tool_name not in TOOLS:
        print(json.dumps({"error": "未知工具: " + tool_name, "available_tools": list(TOOLS.keys())}, ensure_ascii=False))
        sys.exit(1)

    try:
        result = TOOLS[tool_name](params)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
