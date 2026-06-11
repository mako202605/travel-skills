---
name: homestay-finder
description: 零配置即装即用，提供特色民宿搜索和AI智能推荐，基于飞猪数据直连。
tags: [民宿搜索, 特色民宿, 民宿推荐, 客栈, 飞猪旅行, homestay, B&B]
tools:
  - name: search_homestay
    description: 特色民宿结构化搜索
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
        description: 含dest_name/key_words/poi_name/check_in_date/check_out_date/max_price/sort字段
        required: true
  - name: recommend_homestay
    description: AI语义推荐特色民宿
    parameters:
      - name: params
        type: string
        description: 自然语言描述需求，如"莫干山带院子能烧烤的亲子民宿"
        required: true
---

# 特色民宿推荐

零配置即装即用的特色民宿搜索技能，2项工具覆盖结构化搜索和AI语义推荐，飞猪数据直连。

## 能做什么

- **民宿搜索**：按目的地、关键词、景点、日期、价格筛选民宿
- **AI推荐**：自然语言描述需求，智能推荐特色民宿

## 使用示例

1. {"dest_name": "大理", "key_words": "海景"}
2. "莫干山带院子能烧烤的亲子民宿，要有山景"
3. {"dest_name": "三亚", "poi_name": "亚龙湾", "max_price": 500}
4. "丽江古城附近有特色的纳西族民宿"

## 注意事项

- 自动过滤"公寓"类结果，聚焦特色民宿和客栈
- 价格实时变动，以实际预订页面为准
- 查询通过云端代理转发到飞猪旅行API，代理不存储用户数据
