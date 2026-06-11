---
name: smart-poi
description: 零配置即装即用，提供6项工具涵盖景点推荐、门票搜索、周边发现、天气和交通查询，基于飞猪与高德数据直连。
tags: [景点推荐, 门票搜索, 周边景点, 天气查询, 交通出行, 飞猪旅行, 高德地图, POI, travel, attraction]
tools:
  - name: recommend_poi
    description: AI景点智能推荐，自然语言描述需求
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
        description: 自然语言查询，如"三亚适合亲子的海边景点"
        required: true
  - name: search_poi
    description: 景点门票结构化搜索
    parameters:
      - name: params
        type: string
        description: 含keyword/city/category/poi_level字段
        required: true
  - name: search_fast
    description: 极速搜索景点门票信息
    parameters:
      - name: params
        type: string
        description: 搜索词，如"北京故宫门票"
        required: true
  - name: nearby_poi
    description: 周边景点发现
    parameters:
      - name: params
        type: string
        description: 含location/city/radius字段
        required: true
  - name: search_weather
    description: 查询目的地天气预报
    parameters:
      - name: params
        type: string
        description: 自然语言查询，如"三亚天气预报"
        required: true
  - name: search_transport
    description: 查询去景点的交通方案
    parameters:
      - name: params
        type: string
        description: 自然语言查询，如"西湖到灵隐寺（杭州）"
        required: true
---

# 智能景点推荐

零配置即装即用的景点推荐技能，6项工具覆盖AI推荐、门票搜索、极速搜索、周边发现、天气查询、交通出行。

## 能做什么

- **AI景点推荐**：自然语言描述需求，智能推荐最合适的景点
- **门票搜索**：按关键词、城市、类型、等级结构化筛选景点
- **极速搜索**：快速查询景点、门票信息
- **周边发现**：基于位置搜索附近景点
- **天气查询**：查询目的地天气预报
- **交通出行**：查询去景点的交通方案，含打车链接

## 使用示例

1. "三亚适合亲子的海边景点"
2. "杭州5A景区推荐"
3. "西湖附近有什么景点"
4. "故宫门票多少钱"
5. "三亚天气预报"

## 注意事项

- 价格实时变动，以实际预订页面为准
- 查询通过云端代理转发到飞猪旅行+高德地图API，代理不存储用户数据
