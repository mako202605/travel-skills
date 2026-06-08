---
name: gaode-map-pro
description: 高德地图全能版技能，免申请Key即用，22项地图能力全覆盖：地理编码、逆地理编码、POI搜索、周边搜索、POI详情、输入提示、行政区划查询、驾车/公交/步行/骑行路线规划（坐标版+地址版）、天气查询、IP定位、距离测量、静态地图、坐标转换、唤端导航、唤端打车。零配置即装即用。
tags:
  - 高德地图
  - 路线规划
  - 周边搜索
  - 位置服务
  - 天气查询
  - IP定位
  - 地图API
  - 旅行助手
  - 导航
  - 打车
---

# 高德地图全能版

免申请Key即用的高德地图技能，22项能力覆盖地图服务全场景。零配置即装即用。

## 能力概览

| 序号 | 工具 | 说明 |
|------|------|------|
| 1 | geocode | 地址转经纬度坐标 |
| 2 | regeocode | 经纬度转详细地址 |
| 3 | poi_search | 关键词搜索兴趣点 |
| 4 | poi_around | 周边搜索兴趣点 |
| 5 | poi_detail | POI详情查询 |
| 6 | input_tips | 输入提示自动补全 |
| 7 | district | 行政区划查询 |
| 8 | driving_route | 驾车路线规划（坐标版） |
| 9 | transit_route | 公交路线规划（坐标版） |
| 10 | walking_route | 步行路线规划（坐标版） |
| 11 | cycling_route | 骑行路线规划（坐标版） |
| 12 | driving_route_by_address | 驾车路线规划（地址版） |
| 13 | transit_route_by_address | 公交路线规划（地址版） |
| 14 | walking_route_by_address | 步行路线规划（地址版） |
| 15 | cycling_route_by_address | 骑行路线规划（地址版） |
| 16 | weather | 天气查询 |
| 17 | ip_location | IP定位 |
| 18 | distance | 距离测量 |
| 19 | staticmap | 静态地图生成 |
| 20 | coordinate_convert | 坐标转换 |
| 21 | schema_navi | 唤端导航 |
| 22 | schema_take_taxi | 唤端打车 |

## 工作流程

1. 根据用户需求判断调用哪个工具
2. 执行 `python3 scripts/gaode_map_pro.py <tool> '<json_params>'`
3. 解析JSON输出，以自然语言回复用户

## 工具参数说明

### geocode
地址转经纬度。参数：address(必填), city(选填)

### regeocode
经纬度转地址。参数：location(必填,"lng,lat"), extensions(选填,base/all)

### poi_search
关键词搜索POI。参数：keywords(必填), city(选填), types(选填), offset(选填), page(选填), citylimit(选填)

### poi_around
周边搜索POI。参数：location(必填), keywords(必填), radius(选填,默认3000), offset(选填), page(选填), types(选填)

### poi_detail
POI详情。参数：id(必填)

### input_tips
输入提示。参数：keywords(必填), city(选填), datatype(选填,默认all)

### district
行政区划查询。参数：keywords(选填), subdistrict(选填,默认1)

### driving_route
驾车路线。参数：origin(必填,"lng,lat"), destination(必填,"lng,lat"), strategy(选填), waypoints(选填)

### transit_route
公交路线。参数：origin(必填), destination(必填), city(必填), cityd(选填,跨城必填)

### walking_route
步行路线。参数：origin(必填), destination(必填)

### cycling_route
骑行路线。参数：origin(必填), destination(必填)

### driving_route_by_address
驾车路线（地址版）。参数：origin_address(必填), destination_address(必填), origin_city(选填), destination_city(选填)

### transit_route_by_address
公交路线（地址版）。参数：origin_address(必填), destination_address(必填), city(必填), cityd(选填), origin_city(选填), destination_city(选填)

### walking_route_by_address
步行路线（地址版）。参数：origin_address(必填), destination_address(必填), origin_city(选填), destination_city(选填)

### cycling_route_by_address
骑行路线（地址版）。参数：origin_address(必填), destination_address(必填), origin_city(选填), destination_city(选填)

### weather
天气查询。参数：city(必填,城市名或adcode), extensions(选填,base实况/all预报)

### ip_location
IP定位。参数：ip(选填,不填则定位当前IP)

### distance
距离测量。参数：origins(必填,起点经纬度,多个用|分隔), destination(必填,终点经纬度), type(选填,0直线/1驾车/3步行)

### staticmap
静态地图。参数：location(选填,中心点), zoom(选填,3-17), size(选填,默认400*400), scale(选填,1/2), markers(选填,标记点), labels(选填,标签), paths(选填,路线), traffic(选填)

### coordinate_convert
坐标转换。参数：coords(必填,经纬度), coordsys(必填,gps/baidu/mapbar/autonavi)

### schema_navi
唤端导航。参数：lon(必填,终点经度), lat(必填,终点纬度), name(选填,终点名称), dev(选填,0高德坐标/1GPS)

### schema_take_taxi
唤端打车。参数：slon(选填,起点经度), slat(选填,起点纬度), sname(选填,起点名称), dlon(必填,终点经度), dlat(必填,终点纬度), dname(选填,终点名称)

## 使用示例

```
# 地理编码
python3 scripts/gaode_map_pro.py geocode '{"address": "广州塔", "city": "广州"}'

# POI搜索
python3 scripts/gaode_map_pro.py poi_search '{"keywords": "肯德基", "city": "广州"}'

# 驾车路线（地址版）
python3 scripts/gaode_map_pro.py driving_route_by_address '{"origin_address": "广州塔", "destination_address": "珠江新城", "origin_city": "广州"}'

# 天气查询（含预报）
python3 scripts/gaode_map_pro.py weather '{"city": "广州", "extensions": "all"}'

# 距离测量
python3 scripts/gaode_map_pro.py distance '{"origins": "116.48,39.99", "destination": "116.40,39.91", "type": "1"}'

# 唤端导航
python3 scripts/gaode_map_pro.py schema_navi '{"lon": "116.397428", "lat": "39.90923", "name": "天安门"}'

# 唤端打车
python3 scripts/gaode_map_pro.py schema_take_taxi '{"dlon": "116.397428", "dlat": "39.90923", "dname": "天安门"}'
```

## 工具联动建议

- 模糊搜索地点：input_tips → poi_search → poi_detail
- 地址到路线：geocode → driving_route，或直接用 driving_route_by_address
- 定位到天气：ip_location → weather
- 区划到POI：district → poi_search
- 搜索到导航：poi_search → schema_navi
- 搜索到打车：poi_search → schema_take_taxi
- 距离预判：distance → driving_route_by_address

## 不能做

- 不支持室内导航和实时公交到站
- 步行路线最大100km，骑行最大500km
- 静态地图为图片URL，不含交互功能
- 唤端导航/打车生成URI，需用户在移动端点击才能跳转高德APP
- 坐标转换仅支持转成高德坐标系，不支持高德转其他
