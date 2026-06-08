---
name: tuniu-travel-assistant
description: 零配置即装即用｜15项工具查询预订全覆盖｜含预订下单和订单管理｜酒店机票火车票门票一站搞定
tags: [途牛旅行, 酒店查询, 机票查询, 火车票查询, 景点门票, 旅行助手, 出行, 途牛, tuniu, travel]
tools:
  - name: tool_tuniu_hotel_search
    description: 途牛酒店搜索，按城市+日期查询
    primaryEnv: TUNIU_PROXY_URL
    env:
      - name: TUNIU_PROXY_URL
        description: 途牛代理URL（自动配置，无需手动设置）
        required: false
      - name: PROXY_TOKEN
        description: 代理认证Token（自动配置，无需手动设置）
        required: false
    parameters:
      - name: params
        type: string
        description: 查询参数
        required: true
  - name: tool_tuniu_hotel_detail
    description: 酒店详情+房型报价
    parameters:
      - name: params
        type: string
        description: 查询参数
        required: true
  - name: tool_tuniu_hotel_create_order
    description: 酒店预订下单（可能产生费用，请确认后操作）
    parameters:
      - name: params
        type: string
        description: 查询参数
        required: true
  - name: tool_tuniu_flight_search
    description: 机票搜索，6种查询模式
    parameters:
      - name: params
        type: string
        description: 查询参数
        required: true
  - name: tool_tuniu_flight_cabin_detail
    description: 舱位价格详情
    parameters:
      - name: params
        type: string
        description: 查询参数
        required: true
  - name: tool_tuniu_flight_booking_info
    description: 获取预订必填字段说明
    parameters:
      - name: params
        type: string
        description: 查询参数
        required: true
  - name: tool_tuniu_flight_save_order
    description: 机票预订下单（可能产生费用，请确认后操作）
    parameters:
      - name: params
        type: string
        description: 查询参数
        required: true
  - name: tool_tuniu_flight_cancel_order
    description: 取消机票订单（可能产生退款或费用，请确认后操作）
    parameters:
      - name: params
        type: string
        description: 查询参数
        required: true
  - name: tool_tuniu_train_search
    description: 火车票搜索，6种排序
    parameters:
      - name: params
        type: string
        description: 查询参数
        required: true
  - name: tool_tuniu_train_detail
    description: 车次座位详情+余票
    parameters:
      - name: params
        type: string
        description: 查询参数
        required: true
  - name: tool_tuniu_train_book
    description: 火车票预订（可能产生费用，请确认后操作）
    parameters:
      - name: params
        type: string
        description: 查询参数
        required: true
  - name: tool_tuniu_train_order_detail
    description: 火车票订单详情
    parameters:
      - name: params
        type: string
        description: 查询参数
        required: true
  - name: tool_tuniu_train_cancel_order
    description: 取消火车票订单（可能产生退款或费用，请确认后操作）
    parameters:
      - name: params
        type: string
        description: 查询参数
        required: true
  - name: tool_tuniu_ticket_query
    description: 景点门票查询
    parameters:
      - name: params
        type: string
        description: 查询参数
        required: true
  - name: tool_tuniu_ticket_create_order
    description: 门票预订下单（可能产生费用，请确认后操作）
    parameters:
      - name: params
        type: string
        description: 查询参数
        required: true
---

# 途牛旅行助手

零配置即装即用的途牛旅行查询预订技能，15个工具覆盖酒店/机票/火车票/景点门票全品类API。

## 核心功能

### 🏨 酒店（3个工具）
- **酒店搜索** — 按城市+日期查询，支持关键词/商圈筛选和翻页
- **酒店详情** — 酒店详情+房型报价
- **酒店预订** — 酒店预订下单

### ✈️ 机票（5个工具）
- **机票搜索** — 6种查询模式（默认/时间/价格/周边出发/周边到达/中转）
- **舱位详情** — 舱位价格详情
- **预订信息** — 获取预订必填字段说明
- **机票下单** — 机票预订下单
- **取消机票** — 取消机票订单

### 🚄 火车票（5个工具）
- **火车票搜索** — 6种排序（出发时间/耗时/票价升降）
- **车次详情** — 车次座位详情+余票
- **火车票预订** — 火车票预订
- **订单详情** — 火车票订单详情
- **取消订单** — 取消火车票订单

### 🎫 门票（2个工具）
- **门票查询** — 景点门票查询
- **门票预订** — 门票预订下单

## 不能做什么

- 下单类工具需要多步操作（先查询获取ID→再下单），无法一步完成
- 部分小城市火车票/机票数据覆盖可能不完整，建议用大城市名查询

## 使用示例

1. "查上海6月15到17号的酒店"
2. "北京到上海6月20的机票"
3. "广州到深圳明天的火车票"
4. "故宫门票多少钱"

## 注意事项

- 价格实时变动，以实际预订页面为准
- 查询通过云端代理转发到途牛旅行API，代理不存储用户数据
- 下单类操作需多步完成，先查询获取必要ID再下单
- 预订下单和取消订单可能产生费用或退款，请确认后再操作

## 使用提示

- 酒店搜索可用cityName+checkIn+checkOut参数
- 机票搜索可用departureCityName+arrivalCityName+departureDate参数
- 火车票搜索可用departureCityName+arrivalCityName+departureDate参数
- 门票查询可用scenic_name参数
