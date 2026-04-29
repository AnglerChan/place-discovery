---
name: place-discovery
description: Discover local places and route nodes with AMap Web Service POI data plus web-search evidence. Use when Codex needs to find 城市地点, 地方产业空间, 教育训练空间, 城市系统, 基础设施景观, 低商业探索地点, AMap POI enrichment, or produce a 地点研究报告/地点路线 for a city, district, coordinate area, or travel route.
---

# Place Discovery

## Goal

Use this skill to find places with real local function, industry traces, training or research systems, infrastructure landscapes, city operations, and low commercial packaging. Do not produce ordinary tourism lists.

Prefer places that can be understood from public roads, open spaces, official exhibition halls, reservation-based visits, markets, school/public-facing areas, waterfronts, transport edges, or other legal observation points. Never recommend illegal entry.

## Resources

- Use `scripts/amap_client.py` for AMap Web Service calls. It reads only `AMAP_API_KEY`; never hardcode keys.
- Load `references/place_taxonomy.json` when you need the full keyword library, exclusion terms, score weights, or category configuration.
- Use Codex web search as the default evidence layer. Keep `SearchEvidenceProvider` as an abstraction so another search API can replace it later.

## Input Handling

Accept free-form Chinese or English requests. Internally identify the target city or area, district, route, desired themes, exclusions, time budget, transport mode, result count, output mode, and evidence depth. If a detail is absent, infer it from the user request. Treat city or area, trip length, route endpoints, explicit exclusions, and safety constraints as high priority.

## Output Format

最终结果必须是一篇中文 Markdown 文档。不要在最终结果中追加 JSON、YAML、代码块、字段字典、机器可读 schema 或其他数据结构。

每个地点应写成简短的中文地点研究条目，可按需要包含这些部分：

- 类型：一级分类和细分类.
- 推荐等级：强推荐、推荐、可作为路线节点、谨慎推荐、剔除.
- 建议方式：合法接近方式和观察方法.
- 推荐理由：说明地点的真实功能、产业痕迹、基础设施价值、训练研究价值或低商业空间价值.
- 观察重点：公共空间中可以合法观察的物件、流线、边界、标识、设备或景观结构.
- 排除风险：说明文旅包装、普通消费主导、不安全进入、敏感区域或开放性不明等问题.
- 安全提示：用保守语气说明安全和合法边界.
- AMap：有高德信息时，用普通中文写出名称、地址、坐标和 POI ID.
- 证据：当证据影响纳入、剔除、开放状态或风险判断时，引用公开官方或高质量来源.

语气应接近地点研究报告，避免“必去”、“宝藏”、“出片”、“网红”、“打卡”等旅游攻略式表达。

## Discovery Workflow

1. Parse the request into target area, route, desired categories, explicit exclusions, time budget, and transport mode.
2. Resolve the geography with AMap: district lookup for city/area names, geocode for addresses, reverse geocode for coordinates, and polygon or around search for bounded areas.
3. Generate keyword batches from the four categories. Expand by local industry when obvious from the city, e.g. 舟山 -> 渔业/港口/船舶, 无锡 -> 电动车/物联网/纺织, 杭州 -> 高校/互联网/城郊水系.
4. Fetch POI candidates through AMap keyword, around, polygon, and detail APIs. Deduplicate by POI ID, name plus location, and near-identical address.
5. Build a web evidence packet for each promising candidate. Evidence informs quality, heat, function, access, and risk; it does not replace AMap as the POI foundation.
6. Apply hard exclusions before scoring.
7. Score, rank, diversify by category, and produce a Markdown report or route output.
8. If AMap is unavailable or `AMAP_API_KEY` is missing, clearly say so in Chinese and output a prose keyword search plan plus any web-evidence-only candidates as provisional, without fabricating POI IDs.

## Classification System

Use exactly these top-level categories:

- 教育与文化: 高校、职业院校、技工学校、行业小馆、专题展示空间、地方收藏、工艺展示、训练与研究空间.
- 产业与技术: 工业园、工厂外围、公司园区、生产基地、研发中心、企业展厅、地方主力产业集聚区.
- 城市系统: 港口、码头、渡口、货运铁路、物流、仓储、水闸、泵站、堤坝、变电、热电、水务、公交/客运节点、地方媒介与视觉系统. 市场类只作为辅助城市系统节点，除非它与口岸、冷链、产业配套、迁址更新、专业生产资料流通有强关系，否则降低权重.
- 低商业探索: 自然生产景观、湿地/河堤/海塘非核心段、河网村落、老商场、电脑城、家电/家具卖场、半停业商业体、拆迁边界、新城未完工区域.

Use objective tags such as “真实运行空间”, “低消费导向”, “低包装程度”, “原有功能保留较多”, “以本地使用者为主”, “游客密度较低”, “商业植入较少”, “空间功能清晰”, “地方产业痕迹明显”, “适合公共道路外围观察”.

## Exclusion Rules

Hard-exclude unless the user explicitly requests the category:

- High-exposure ordinary scenic symbols: 西湖、武康大楼、洪崖洞、夫子庙 and similar places dominated by mature tourist movement.
- Red narrative sites: 红色、革命、烈士、胜利、战争、抗战、爱国主义教育基地、红色文化园、烈士陵园、名人故居.
- Grand historical or ancient artifact museums: broad local history museums, ancient artifact comprehensive museums, and macro-history narratives.
- Highly packaged commercial spaces: tourist commercial streets, night tours, light shows, viewing platforms, themed parks, old factories converted mainly into cafe/cultural-commerce/photo zones.
- Illegal or unsafe sites: fenced ruins, locked buildings, collapse risk, chemical/pollution risk, active construction zones, rail/highway crossing, and sensitive military/energy/traffic/port core facilities.

Context rule: “纪念馆” and “博物馆” are not absolute exclusions. Keep industry-specific or technical spaces such as 水务馆、船舶馆、纺织馆、酱文化馆、气象馆、邮政馆 when evidence supports a concrete industry or knowledge function. Exclude war, revolution, celebrity residence, and ancient-artifact comprehensive spaces.

## Keyword Library

Load the full library from `references/place_taxonomy.json`. Use these seed groups:

- 教育与文化: 大学、学院、职业技术学院、技工学校、中专、艺术学院、美术学院、航海学校、铁路学校、汽车工程学院、纺织学院、食品学院、轻工学院、船舶学院、文化馆、收藏馆、展示馆、陈列馆、水产馆、纺织馆、船舶馆、邮政馆、气象馆、水务馆、酱文化、民间博物馆.
- 产业与技术: 工业园、产业园、科技园、软件园、高新区、开发区、工厂、生产基地、总部、研发中心、展厅、工厂店、电动车、汽车、汽配、纺织、船舶、食品、物联网、半导体、光伏、新能源、机器人、智能制造、数据中心、物流装备.
- 城市系统: 港、码头、渡口、货运站、编组站、车辆段、物流园、分拨中心、冷链、仓储、水闸、泵站、堤、防洪、运河、变电站、热电厂、水务、船厂、图文快印、广告制作、喷绘、报社、广播电视台、公交总站、客运站. 农贸市场、普通批发市场、水产市场、五金市场、轻纺市场、电动车市场只作为低优先级补充关键词使用，不能仅因“真实运行”进入主推荐.
- 低商业探索: 湿地、郊野公园、河堤、绿道、水库、海塘、滩涂、围垦、鱼塘、盐田、茶园、桑园、蟹塘、稻田、养殖、老商场、百货大楼、地下商业街、电脑城、手机市场、家电卖场、家具城、停业、废弃、旧厂房、拆迁、未完工.

Use negative keywords for downranking or exclusion: 红色、革命、烈士、胜利、战争、抗战、纪念馆、故居、爱国主义教育基地、研学基地、文旅、文创街区、打卡、网红、夜游、灯光秀、观景台、古镇、老街、步行街、旅游区、度假区、景区、风景名胜区、游客中心、主题乐园、影视城、仿古、非遗商业街.

## AMap API Strategy

AMap is the POI foundation. Use the script rather than rewriting request code:

```bash
export AMAP_API_KEY="..."
python scripts/amap_client.py district 舟山 --extensions all
python scripts/amap_client.py search 港 --city 舟山 --limit 20
python scripts/amap_client.py around 122.207216,29.985295 5000 物流园
python scripts/amap_client.py polygon "120.0,30.0|120.2,30.0|120.2,30.2|120.0,30.2" 船厂
python scripts/amap_client.py detail B0XXXX
python scripts/amap_client.py geocode 无锡市
python scripts/amap_client.py regeo 120.31237,31.49099
```

Supported AMap capabilities:

- Administrative district parsing: resolve `adcode`, `citycode`, center, and boundary.
- Keyword search: retrieve category candidates by city, district, or keyword.
- Around search: search by center point and radius.
- Polygon search: search bounded areas or route corridors.
- ID detail lookup: enrich chosen POIs.
- Geocode and reverse geocode: convert address and coordinates.

If the key is missing, report: `AMAP_API_KEY is not set; AMap POI enrichment skipped.` Continue with keyword plans and web evidence, but mark AMap fields empty or provisional.

## Search Evidence Layer

Use web search for evidence after AMap candidate discovery. Do not use search results to fabricate AMap POIs. Cite sources in the final report when evidence materially affects inclusion, exclusion, opening/access status, or risk.

Use this conceptual interface:

```python
class SearchEvidenceProvider:
    def search(self, query: str, *, source_hint: str = "", max_results: int = 5) -> list[dict]:
        """Return public search-result metadata: title, url, snippet, source_type."""
```

Default provider: Codex built-in web search. Future adapters can implement Brave, Bocha, Tavily, SerpAPI, or a private search service without changing the output schema.

For each candidate, search in this order:

1. Official evidence: `<地点名> <城市> 官网`, `<地点名> 开放 预约`, `<地点名> 展厅 参观`, `<地点名> 政府`, `<地点名> 园区`.
2. Function evidence: `<地点名> 生产基地`, `<地点名> 市场`, `<地点名> 港口`, `<地点名> 水务`, `<地点名> 学校`, `<地点名> 物流`.
3. Heat and packaging evidence: `<地点名> 小红书`, `<地点名> 打卡`, `<地点名> 出片`, `<地点名> 攻略`, `<地点名> 周末去哪`, `<地点名> 咖啡 文创 集市`.
4. Access and risk evidence: `<地点名> 封闭`, `<地点名> 禁止拍摄`, `<地点名> 预约`, `<地点名> 危险`, `<地点名> 停业`.

Source priority:

- Highest: school/company/park/government/utility/market/operator pages, official account articles, reservation pages.
- Medium: blogs, local forums, city observation articles, photography records, industry visit reports.
- Low and mostly negative: OTA/travel platforms, review platforms, social-media result snippets, photo-check-in content.

Use only public titles/snippets/visible pages. Do not bypass platform limits, scrape private content, or store user-generated content.

## Scoring System

Start from 0 and add/subtract signals; cap final visible scores to 0-100. Remove hard-excluded places before scoring.

Add:

- 地方产业相关: +20
- 真实运行功能: +20
- 游客密度较低: +15
- 商业植入较少: +15
- 空间结构明显: +10
- 可合法接近: +10
- 视觉材料丰富: +10
- 与高校、工厂、港口、物流、水务、基础设施有关: +10
- 有路线节点价值: +5

Subtract:

- 普通农贸市场、普通批发市场、水产市场、五金市场、轻纺市场、电动车市场主导: -20
- 市场功能普通且缺少冷链、口岸、产业配套、迁址更新或专业生产资料流通信号: -15
- 平台曝光过高: -30
- 观光消费主导: -25
- 红色叙事主导: -100
- 宏大历史或古代文物综合馆: -80
- 需要非法进入: -100
- 存在明显安全风险: -100
- 商业包装过强: -40
- 原有功能消失: -30
- 只适合拍照传播: -30

Recommendation levels:

- 85-100: 强推荐
- 70-84: 推荐
- 55-69: 可作为路线节点
- 40-54: 谨慎推荐
- Below 40: 不推荐, normally omit from final results
- Any hard exclusion: 剔除

## Ranking Logic

Rank by hard-exclusion status, score, evidence quality, AMap confidence, legal access, category diversity, and route fit. Avoid outputting many near-duplicates from the same industrial park, market cluster, or waterfront. If several POIs describe one system, merge them into one candidate such as “沈家门渔港外围” and list representative AMap POIs.

市场排序规则：普通农贸市场、普通批发市场、水产市场、五金市场、轻纺市场、电动车市场通常应降为“可作为路线节点”或直接省略。只有当一个市场能清楚揭示更大的城市系统时，才保留在主推荐中，例如港口周边渔业物流、冷链分拨、铁路或陆港物流、产业供应链、新老市场迁址更新、生产资料流通，并且这些内容不能被其他基础设施或产业节点更好地代表。

Prefer a balanced final set: at least two categories when possible, with one or more strong city-system or industry anchors.

## Route Generation Logic

If the user asks for a route:

- Arrange 3-6 places per day.
- Prefer 顺路 over quantity.
- Alternate industry, street/market, infrastructure, education/culture, and low-commercial nodes.
- Avoid stacking multiple high-fatigue or peripheral sites back-to-back.
- Keep rest time and food/transport buffers implicit in the schedule.
- Mark “可跳过项” and “备选项”.
- For factories, ports, traffic, energy, abandoned, or semi-abandoned sites, recommend only public-road/peripheral observation unless an official open mechanism exists.

## Safety and Legality

Use conservative safety language:

- Recommend public roads, open paths, legal markets, public campus/open exhibition areas, or official reservation channels.
- Do not recommend climbing fences, entering locked buildings, crossing railway/highway/construction zones, or approaching sensitive cores.
- Do not encourage photographing areas marked as prohibited.
- Mark solo suitability as “谨慎” or “不建议” for remote waterfronts, industrial edges, semi-abandoned commercial spaces, night visits, and places with weak public foot traffic.
- If evidence is unclear, say “仅建议白天从公共道路观察，现场以管理标识为准”.

## Example Inputs

- “帮我找舟山适合探索的地点”
- “无锡两天，想看产业、老商场、湿地和基础设施”
- “杭州不要西湖、不要武康路那种地方，想看高校、厂区和城市边界”
- “从无锡到舟山自驾，沿路找地点”

## Example Output Shape

# 舟山地点候选

## 1. 沈家门渔港外围

类型：城市系统 / 港口与渔业
推荐等级：强推荐
建议方式：公共道路外围观察，适合作为路线节点
推荐理由：这里保留渔港、冷链、水产交易、船舶停靠等真实功能，能体现舟山的渔业城市结构。
观察重点：渔船、冷链车辆、水产市场、港区边界、地方招牌。
排除风险：不进入封闭码头，不拍摄明确禁止拍摄区域。
AMap：名称、地址、经纬度、POI ID、类型

## 辅助节点：沈家门水产市场

类型：城市系统 / 水产交易
推荐等级：可作为路线节点
建议方式：只在白天开放时段观察公共交易区。
推荐理由：可补充理解渔港供应链，但普通市场属性较强，不应压过港口、码头、冷链、船厂等主节点。
观察重点：水产交易、冷链车辆、市场与港区之间的物流关系。
排除风险：如果现场以零售消费为主，或商业包装强，应降级或跳过。

## Extensible Configuration

Keep these adjustable without rewriting the skill:

- `AMAP_API_KEY`: environment variable for AMap Web Service.
- `SearchEvidenceProvider`: adapter for Codex web search now; Brave/Bocha/Tavily/SerpAPI later.
- `references/place_taxonomy.json`: categories, keywords, city-industry expansions, negative terms, hard exclusions, score weights.
- Result limits: default 12 report candidates, 3-6 route nodes per day.
- Evidence depth: `standard` for quick reports, `deep` for more source checking.
