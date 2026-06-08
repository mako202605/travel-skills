---
name: tuniu-travel-assistant
description: 途牛旅行，零配置即装即用，酒店/机票/火车票/景点门票全品类查询预订，15个工具覆盖途牛全品类API。
tags:
  - 途牛旅行
  - 酒店查询
  - 机票查询
  - 火车票查询
  - 景点门票
  - 旅行助手
  - 出行
  - 途牛
---

# 途牛旅行助手

零配置即装即用的途牛旅行查询预订技能，15个工具覆盖酒店/机票/火车票/景点门票全品类API。

## 核心功能

### 🏨 酒店（3个工具）
- **tuniu_hotel_search** — 酒店搜索，按城市+日期查询，支持关键词/商圈筛选和翻页
- **tuniu_hotel_detail** — 酒店详情+房型报价，返回preBookParam用于下单
- **tuniu_hotel_create_order** — 酒店预订下单

### ✈️ 机票（5个工具）
- **tuniu_flight_search** — 机票搜索，6种查询模式（默认/时间/价格/周边出发/周边到达/中转）
- **tuniu_flight_cabin_detail** — 舱位价格详情，返回cabinPriceId用于下单
- **tuniu_flight_booking_info** — 获取预订必填字段说明
- **tuniu_flight_save_order** — 机票预订下单
- **tuniu_flight_cancel_order** — 取消机票订单

### 🚄 火车票（5个工具）
- **tuniu_train_search** — 火车票搜索，6种排序（出发时间/耗时/票价升降）
- **tuniu_train_detail** — 车次座位详情+余票，返回resId用于预订
- **tuniu_train_book** — 火车票预订
- **tuniu_train_order_detail** — 火车票订单详情
- **tuniu_train_cancel_order** — 取消火车票订单

### 🎫 门票（2个工具）
- **tuniu_ticket_query** — 景点门票查询，返回productId+resId
- **tuniu_ticket_create_order** — 门票预订下单

## 参数说明

### tuniu_hotel_search
- **cityName**（首页必填）— 城市名，如：上海、北京
- **checkIn**（首页必填）— 入住日期，格式：YYYY-MM-DD
- **checkOut**（首页必填）— 离店日期，格式：YYYY-MM-DD
- keyword / poiName / prices / adultNum / childNum / childAges — 可选筛选
- **queryId** + **pageNum** — 翻页时使用

### tuniu_hotel_detail
- **hotelId** 或 **hotelName**（必填）— 酒店ID或名称
- **checkIn** / **checkOut**（必填）— 入住离店日期

### tuniu_flight_search
- **departureCityName**（必填）— 出发城市，如：北京
- **arrivalCityName**（必填）— 到达城市，如：上海
- **departureDate**（必填）— 出发日期，格式：YYYY-MM-DD
- searchType — 查询模式：0默认/1时间/2价格/3周边出发/4周边到达/5中转

### tuniu_train_search
- **departureCityName**（首页必填）— 出发城市
- **arrivalCityName**（首页必填）— 到达城市
- **departureDate**（首页必填）— 出发日期
- searchType — 排序：0出发升/1出发降/2耗时升/3耗时降/4票价升/5票价降

### tuniu_ticket_query
- **scenic_name**（必填）— 景点名称，如：故宫、迪士尼

## 使用示例

- "查上海6月15到17号的酒店" → `tuniu_hotel_search(cityName="上海", checkIn="2026-06-15", checkOut="2026-06-17")`
- "北京到上海6月20的机票" → `tuniu_flight_search(departureCityName="北京", arrivalCityName="上海", departureDate="2026-06-20")`
- "广州到深圳明天的火车票" → `tuniu_train_search(departureCityName="广州", arrivalCityName="深圳", departureDate="2026-06-09")`
- "故宫门票多少钱" → `tuniu_ticket_query(scenic_name="故宫")`

## 不能做

- 下单类工具需要多步操作（先查询获取ID→再下单），无法一步完成
- 部分小城市火车票/机票数据覆盖可能不完整，建议用大城市名查询
