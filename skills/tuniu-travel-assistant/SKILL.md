---
name: tuniu-travel-assistant
description: 零配置即装即用，提供15项工具覆盖查询和预订，支持预订下单和订单管理，酒店、机票、火车票、门票一站搞定。
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
    description: 酒店预订下单（需confirm=true确认，可能产生费用）
    parameters:
      - name: params
        type: string
        description: 查询参数（含confirm=true确认字段）
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
    description: 机票预订下单（需confirm=true确认，可能产生费用）
    parameters:
      - name: params
        type: string
        description: 查询参数（含confirm=true确认字段）
        required: true
  - name: tool_tuniu_flight_cancel_order
    description: 取消机票订单（需confirm=true确认，可能产生退款或费用）
    parameters:
      - name: params
        type: string
        description: 查询参数（含confirm=true确认字段）
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
    description: 火车票预订（需confirm=true确认，可能产生费用）
    parameters:
      - name: params
        type: string
        description: 查询参数（含confirm=true确认字段）
        required: true
  - name: tool_tuniu_train_order_detail
    description: 火车票订单详情
    parameters:
      - name: params
        type: string
        description: 查询参数
        required: true
  - name: tool_tuniu_train_cancel_order
    description: 取消火车票订单（需confirm=true确认，可能产生退款或费用）
    parameters:
      - name: params
        type: string
        description: 查询参数（含confirm=true确认字段）
        required: true
  - name: tool_tuniu_ticket_query
    description: 景点门票查询
    parameters:
      - name: params
        type: string
        description: 查询参数
        required: true
  - name: tool_tuniu_ticket_create_order
    description: 门票预订下单（需confirm=true确认，可能产生费用）
    parameters:
      - name: params
        type: string
        description: 查询参数（含confirm=true确认字段）
        required: true
---

# 途牛旅行助手

零配置即装即用的途牛旅行查询预订技能，15个工具覆盖酒店/机票/火车票/景点门票全品类API。

## 数据流向说明

本技能通过腾讯云SCF代理（域名 ap-guangzhou.tencentscf.com）转发请求到途牛旅行API。传输数据包括：
- **查询类工具**：仅发送城市名、日期等搜索条件
- **预订类工具**：发送旅客姓名、手机号、证件信息等下单必需字段
- 代理仅做透传，不存储用户数据，不记录请求内容
- 代理认证采用服务端令牌鉴权（X-Proxy-Token header）

## 核心功能

### 🏨 酒店（3个工具）
- **酒店搜索** — 按城市+日期查询，支持关键词/商圈筛选和翻页
- **酒店详情** — 酒店详情+房型报价
- **酒店预订** — 酒店预订下单（需确认）

### ✈️ 机票（5个工具）
- **机票搜索** — 6种查询模式（默认/时间/价格/周边出发/周边到达/中转）
- **舱位详情** — 舱位价格详情
- **预订信息** — 获取预订必填字段说明
- **机票下单** — 机票预订下单（需确认）
- **取消机票** — 取消机票订单（需确认）

### 🚄 火车票（5个工具）
- **火车票搜索** — 6种排序（出发时间/耗时/票价升降）
- **车次详情** — 车次座位详情+余票
- **火车票预订** — 火车票预订（需确认）
- **订单详情** — 火车票订单详情
- **取消订单** — 取消火车票订单（需确认）

### 🎫 门票（2个工具）
- **门票查询** — 景点门票查询
- **门票预订** — 门票预订下单（需确认）

## 预订确认机制

所有涉及金钱操作的工具（下单/取消订单）内置确认检查：
- 首次调用时需传 `confirm=true` 参数，否则仅返回确认提示不执行操作
- Agent应在向用户展示订单详情并获得明确同意后，再设置 confirm=true 执行
- 涉及的工具：hotel_create_order、flight_save_order、flight_cancel_order、train_book、train_cancel_order、ticket_create_order

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
- 预订下单和取消订单需confirm=true确认后才执行，防止误操作

## 使用提示

- 酒店搜索可用cityName+checkIn+checkOut参数
- 机票搜索可用departureCityName+arrivalCityName+departureDate参数
- 火车票搜索可用departureCityName+arrivalCityName+departureDate参数
- 门票查询可用scenic_name参数
