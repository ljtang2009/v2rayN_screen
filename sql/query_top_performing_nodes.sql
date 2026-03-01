-- =====================================================
-- 优秀节点筛选查询脚本 (修正版 v2)
-- 从 ProfileExItemHistory 表中识别表现优秀的节点
-- 修正内容：
-- 1. Delay 为 0 表示不能连接，应排除
-- 2. 协议类型根据 v2rayN 源码中的 EConfigType 枚举映射显示
-- 3. 移除时间范围限制，查询全部历史数据
-- 4. 取消测试次数限制
-- 5. 新增"连接成功率"列
-- 6. 调整排序逻辑：连接成功率 DESC, 测试次数 DESC, 平均延迟 ASC, 延迟波动率 ASC
-- 创建时间: 2026-03-01
-- 最后修改: 2026-03-01
-- =====================================================

-- =====================================================
-- 查询1: 获取表现最优秀的节点（综合评分 - 无时间限制）
-- =====================================================
-- 说明：基于连接成功率、平均延迟、测试次数和稳定性综合评估节点性能
-- 修改内容：
--   - 移除时间范围限制（查询全部历史数据）
--   - 取消测试次数限制
--   - 新增"连接成功率"列（保留两位小数）
--   - 调整排序逻辑：连接成功率 DESC, 测试次数 DESC, 平均延迟 ASC, 延迟波动率 ASC
SELECT 
    p.IndexId,
    p.Remarks AS 节点名称,
    CASE p.ConfigType
        WHEN 1 THEN 'VMess'
        WHEN 2 THEN 'Custom'
        WHEN 3 THEN 'Shadowsocks'
        WHEN 4 THEN 'SOCKS'
        WHEN 5 THEN 'VLESS'
        WHEN 6 THEN 'Trojan'
        WHEN 7 THEN 'Hysteria2'
        WHEN 8 THEN 'TUIC'
        WHEN 9 THEN 'WireGuard'
        WHEN 10 THEN 'HTTP'
        WHEN 11 THEN 'Anytls'
        WHEN 101 THEN 'PolicyGroup'
        WHEN 102 THEN 'ProxyChain'
        ELSE 'Unknown'
    END AS 协议类型,
    p.Address AS 服务器地址,
    p.Port AS 端口,
    COUNT(h.id) AS 测试次数,
    MAX(h.datetime) AS 最近测试时间,
    ROUND(SUM(CASE WHEN h.Delay > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(h.id), 2) AS 连接成功率,
    AVG(h.Delay) AS 平均延迟,
    MIN(h.Delay) AS 最低延迟,
    MAX(h.Delay) AS 最高延迟,
    ROUND(AVG(h.Speed), 2) AS 平均速度,
    MAX(h.Speed) AS 最高速度,
    ROUND((MAX(h.Delay) - MIN(h.Delay)) * 1.0 / NULLIF(AVG(h.Delay), 0), 2) AS 延迟波动率
FROM ProfileItem p
INNER JOIN ProfileExItemHistory h ON p.IndexId = h.IndexId
WHERE h.Delay IS NOT NULL
GROUP BY p.IndexId, p.Remarks, p.ConfigType, p.Address, p.Port
ORDER BY 连接成功率 DESC, 测试次数 DESC, 平均延迟 ASC, 延迟波动率 ASC
LIMIT 100;

-- =====================================================
-- 查询2: 获取延迟最低的节点（即时性能 - 无时间限制）
-- =====================================================
-- 说明：适用于需要当前最优节点的场景
-- 修改内容：
--   - 移除时间范围限制（查询全部历史数据）
--   - 调整排序逻辑：连接成功率 DESC, 测试次数 DESC, 延迟 ASC, 测试时间 DESC
SELECT 
    p.IndexId,
    p.Remarks AS 节点名称,
    CASE p.ConfigType
        WHEN 1 THEN 'VMess'
        WHEN 2 THEN 'Custom'
        WHEN 3 THEN 'Shadowsocks'
        WHEN 4 THEN 'SOCKS'
        WHEN 5 THEN 'VLESS'
        WHEN 6 THEN 'Trojan'
        WHEN 7 THEN 'Hysteria2'
        WHEN 8 THEN 'TUIC'
        WHEN 9 THEN 'WireGuard'
        WHEN 10 THEN 'HTTP'
        WHEN 11 THEN 'Anytls'
        WHEN 101 THEN 'PolicyGroup'
        WHEN 102 THEN 'ProxyChain'
        ELSE 'Unknown'
    END AS 协议类型,
    p.Address AS 服务器地址,
    p.Port AS 端口,
    h.Delay AS 延迟,
    h.Speed AS 速度,
    h.datetime AS 测试时间
FROM ProfileItem p
INNER JOIN ProfileExItemHistory h ON p.IndexId = h.IndexId
WHERE h.Delay > 0
    AND h.Delay IS NOT NULL
ORDER BY h.Delay ASC, h.datetime DESC;

-- =====================================================
-- 查询3: 获取稳定节点（稳定性优先 - 无时间限制）
-- =====================================================
-- 说明：筛选延迟波动小、连接稳定的节点
-- 修改内容：
--   - 移除时间范围限制（查询全部历史数据）
--   - 取消测试次数限制
--   - 调整排序逻辑：连接成功率 DESC, 延迟波动率 ASC, 平均延迟 ASC
SELECT 
    p.IndexId,
    p.Remarks AS 节点名称,
    CASE p.ConfigType
        WHEN 1 THEN 'VMess'
        WHEN 2 THEN 'Custom'
        WHEN 3 THEN 'Shadowsocks'
        WHEN 4 THEN 'SOCKS'
        WHEN 5 THEN 'VLESS'
        WHEN 6 THEN 'Trojan'
        WHEN 7 THEN 'Hysteria2'
        WHEN 8 THEN 'TUIC'
        WHEN 9 THEN 'WireGuard'
        WHEN 10 THEN 'HTTP'
        WHEN 11 THEN 'Anytls'
        WHEN 101 THEN 'PolicyGroup'
        WHEN 102 THEN 'ProxyChain'
        ELSE 'Unknown'
    END AS 协议类型,
    p.Address AS 服务器地址,
    COUNT(h.id) AS 测试次数,
    ROUND(AVG(h.Delay), 0) AS 平均延迟,
    ROUND(AVG(h.Speed), 2) AS 平均速度,
    ROUND((MAX(h.Delay) - MIN(h.Delay)) * 1.0 / NULLIF(AVG(h.Delay), 0), 2) AS 延迟波动率,
    SUM(CASE WHEN h.Delay <= 0 THEN 1 ELSE 0 END) AS 失败次数,
    ROUND(SUM(CASE WHEN h.Delay > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(h.id), 2) AS 连接成功率
FROM ProfileItem p
INNER JOIN ProfileExItemHistory h ON p.IndexId = h.IndexId
WHERE h.Delay IS NOT NULL
GROUP BY p.IndexId, p.Remarks, p.ConfigType, p.Address
ORDER BY 连接成功率 DESC, 延迟波动率 ASC, 平均延迟 ASC;

-- =====================================================
-- 查询4: 按订阅分组筛选各组最优节点（无时间限制）
-- =====================================================
-- 说明：为每个订阅组筛选出表现最好的节点
-- 修改内容：
--   - 移除时间范围限制（查询全部历史数据）
--   - 取消测试次数限制
--   - 新增"连接成功率"列
--   - 调整排序逻辑：订阅组, 连接成功率 DESC, 测试次数 DESC, 平均延迟 ASC
SELECT 
    s.Remarks AS 订阅组,
    p.IndexId,
    p.Remarks AS 节点名称,
    CASE p.ConfigType
        WHEN 1 THEN 'VMess'
        WHEN 2 THEN 'Custom'
        WHEN 3 THEN 'Shadowsocks'
        WHEN 4 THEN 'SOCKS'
        WHEN 5 THEN 'VLESS'
        WHEN 6 THEN 'Trojan'
        WHEN 7 THEN 'Hysteria2'
        WHEN 8 THEN 'TUIC'
        WHEN 9 THEN 'WireGuard'
        WHEN 10 THEN 'HTTP'
        WHEN 11 THEN 'Anytls'
        WHEN 101 THEN 'PolicyGroup'
        WHEN 102 THEN 'ProxyChain'
        ELSE 'Unknown'
    END AS 协议类型,
    COUNT(h.id) AS 测试次数,
    ROUND(AVG(h.Delay), 0) AS 平均延迟,
    ROUND(AVG(h.Speed), 2) AS 平均速度,
    MAX(h.datetime) AS 最近测试时间,
    ROUND(SUM(CASE WHEN h.Delay > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(h.id), 2) AS 连接成功率
FROM ProfileItem p
INNER JOIN ProfileExItemHistory h ON p.IndexId = h.IndexId
LEFT JOIN SubItem s ON p.Subid = s.Id
WHERE h.Delay IS NOT NULL
GROUP BY s.Remarks, p.IndexId, p.Remarks, p.ConfigType
ORDER BY s.Remarks, 连接成功率 DESC, 测试次数 DESC, 平均延迟 ASC;

-- =====================================================
-- 查询5: 节点性能趋势分析（单个节点的历史表现 - 无时间限制）
-- =====================================================
-- 说明：分析指定节点的完整历史性能变化趋势
-- 修改内容：
--   - 移除时间范围限制（查询全部历史数据）
--   - 新增"连接成功率"列
-- 使用方法：将 'your-node-index-id' 替换为实际的 IndexId
SELECT 
    date(h.datetime) AS 日期,
    COUNT(*) AS 测试次数,
    ROUND(AVG(h.Delay), 0) AS 平均延迟,
    MIN(h.Delay) AS 最低延迟,
    MAX(h.Delay) AS 最高延迟,
    ROUND(AVG(h.Speed), 2) AS 平均速度,
    MAX(h.Speed) AS 最高速度,
    SUM(CASE WHEN h.Delay <= 0 THEN 1 ELSE 0 END) AS 失败次数,
    ROUND(SUM(CASE WHEN h.Delay > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS 连接成功率
FROM ProfileExItemHistory h
WHERE h.IndexId = 'your-node-index-id'              -- 替换为实际节点ID
    AND h.Delay IS NOT NULL
GROUP BY date(h.datetime)
ORDER BY 日期 DESC;

-- =====================================================
-- 关键筛选条件说明（修正版 v2）
-- =====================================================
-- 
-- 1. Delay 值含义：
--    - Delay > 0     : 节点正常，值为延迟毫秒数（越小越好）
--    - Delay = 0     : 节点无法连接或超时
--    - Delay < 0     : 节点无法连接或超时（兼容旧版本）
--    - Delay IS NULL : 数据异常，应排除
--
-- 2. 时间范围：
--    - 所有查询已移除时间范围限制，查询全部历史数据
--    - 如需添加时间范围，可在 WHERE 子句中添加：
--      AND h.datetime >= datetime('now', '-7 days')
--
-- 3. 性能评估指标：
--    - 连接成功率    : 越高越好，建议 >= 95%
--    - 平均延迟      : 越低越好，建议 < 200ms
--    - 延迟波动率    : 越低越好，建议 < 0.5（50%）
--    - 测试次数      : 越多越可靠，建议 >= 3次
--
-- 4. 排序规则（查询1）：
--    - 第一优先级：连接成功率降序（成功率高的排在前面）
--    - 第二优先级：测试次数降序（测试次数多的更可靠）
--    - 第三优先级：平均延迟升序（延迟低的排在前面）
--    - 第四优先级：延迟波动率升序（波动小的更稳定）

-- =====================================================
-- 使用建议
-- =====================================================
-- 
-- 1. 日常使用：运行查询1，获取综合表现最好的节点（无时间限制）
-- 2. 急需最优节点：运行查询2，获取延迟最低的节点
-- 3. 长期稳定使用：运行查询3，筛选高连接成功率、低波动的节点
-- 4. 订阅管理：运行查询4，为每个订阅组选择最优节点
-- 5. 节点评估：运行查询5，分析特定节点的完整历史表现

-- =====================================================
-- 参数配置说明
-- =====================================================
-- 
-- 修改以下参数可自定义查询行为：
-- 
-- 添加时间范围（如需）：
--   - 在 WHERE 子句中添加：
--     AND h.datetime >= datetime('now', '-7 days')   -- 最近7天
--     AND h.datetime >= datetime('now', '-1 day')    -- 最近24小时
--     AND h.datetime >= datetime('now', '-30 days')  -- 最近30天
--
-- 添加测试次数限制（如需）：
--   - 在 HAVING 子句中添加：
--     HAVING COUNT(h.id) >= 3                         -- 至少3次
--     HAVING COUNT(h.id) >= 5                         -- 至少5次
--
-- 添加连接成功率阈值（如需）：
--   - 在 HAVING 子句中添加：
--     HAVING 连接成功率 >= 95                         -- 连接成功率95%以上
--     HAVING 连接成功率 >= 90                         -- 连接成功率90%以上
--
-- 添加延迟波动率阈值（如需）：
--   - 在 HAVING 子句中添加：
--     HAVING 延迟波动率 <= 0.5                        -- 延迟波动率不超过50%
--     HAVING 延迟波动率 <= 0.3                        -- 延迟波动率不超过30%

-- =====================================================
-- 连接成功率计算说明
-- =====================================================
-- 
-- 连接成功率计算公式：
--   连接成功率 = (成功连接次数 / 总连接次数) × 100%
--
-- 其中：
--   - 成功连接次数 = SUM(CASE WHEN h.Delay > 0 THEN 1 ELSE 0 END)
--   - 总连接次数 = COUNT(h.id)
--   - 保留两位小数：ROUND(..., 2)
--
-- 示例：
--   - 某节点共测试10次，其中8次成功（Delay > 0），2次失败（Delay <= 0）
--   - 连接成功率 = (8 / 10) × 100% = 80.00%
