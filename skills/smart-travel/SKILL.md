---
name: smart-travel
description: 零配置即装即用｜12项工具行程规划火车票机票酒店景点美食交通打车天气｜飞猪+高德数据直连
tags: [飞猪旅行, 行程规划, 火车票, 机票, 酒店, 景点, 万豪, 美食, 交通, 天气, 打车, travel, planning]
tools:
  - name: travel_plan
    description: 智能行程规划，推荐行程方案
    primaryEnv: FLIGGY_PROXY_URL
    env:
      - name: FLIGGY_PROXY_URL
        description: 飞猪代理URL（自动配置）
        required: false
      - name: PROXY_TOKEN
        description: 代理认证Token（自动配置）
        required: false
    parameters:
      - name: params
        type: string
        description: 自然语言查询，如"3天2晚上海游"
        required: true
  - name: search_train
    description: 搜索火车票/高铁票
    parameters:
      - name: params
        type: string
        description: 自然语言查询，如"北京到上海明天的火车"
        required: true
  - name: search_flight
    description: 搜索国内航班机票
    parameters:
      - name: params
        type: string
        description: 自然语言查询，如"上海到三亚7月1号机票"
        required: true
  - name: search_hotel
    description: 搜索酒店
    parameters:
      - name: params
        type: string
        description: 自然语言查询，如"杭州西湖附近酒店"
        required: true
  - name: search_poi
    description: 搜索景点门票
    parameters:
      - name: params
        type: string
        description: 自然语言查询，如"上海迪士尼门票"
        required: true
  - name: search_marriott_hotel
    description: 搜索万豪集团酒店
    parameters:
      - name: params
        type: string
        description: 自然语言查询，如"上海万豪酒店"
        required: true
  - name: get_marriott_hotel_info
    description: 获取万豪酒店详情
    parameters:
      - name: params
        type: string
        description: 酒店名称或关键词
        required: true
  - name: search_marriott_package
    description: 搜索万豪酒店套餐
    parameters:
      - name: params
        type: string
        description: 自然语言查询，如"万豪含早套餐"
        required: true
  - name: search_food
    description: 搜索附近美食推荐
    parameters:
      - name: params
        type: string
        description: 自然语言查询，如"外滩附近美食"
        required: true
  - name: search_transport
    description: 查询市内交通方案
    parameters:
      - name: params
        type: string
        description: 自然语言查询，如"浦东机场到外滩（上海）"
        required: true
  - name: search_weather
    description: 查询目的地天气预报
    parameters:
      - name: params
        type: string
        description: 自然语言查询，如"三亚天气预报"
        required: true
  - name: take_taxi_link
    description: 生成高德一键打车链接
    parameters:
      - name: params
        type: string
        description: 自然语言查询，如"从浦东机场到外滩（上海）"
        required: true
---

# 智能旅行规划

零配置即装即用的旅行规划技能，12项工具覆盖行程规划、火车票、机票、酒店、景点、万豪、美食、交通、天气、打车，飞猪+高德数据直连。

## 能做什么

- **行程规划**：智能推荐行程方案，涵盖景点+酒店+交通
- **火车票搜索**：查车次、票价、余票
- **机票搜索**：查航班价格、时刻、航司
- **酒店搜索**：按城市/区域/品牌查酒店
- **景点门票**：查景点门票价格和预订链接
- **万豪酒店**：搜索万豪集团旗下酒店详情和套餐
- **美食推荐**：搜索附近美食，含评分和距离
- **市内交通**：查询公交/地铁/驾车路线
- **天气查询**：查询目的地天气预报
- **打车链接**：生成高德一键打车链接

## 使用示例

1. "帮我规划一个3天2晚的上海游"
2. "查北京到上海明天的火车票"
3. "三亚天气预报"
4. "上海万豪酒店有什么套餐"
5. "从浦东机场到外滩怎么走"

## 注意事项

- 价格实时变动，以实际预订页面为准
- 查询通过云端代理转发到飞猪旅行+高德地图API，代理不存储用户数据
