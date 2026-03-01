-- =====================================================
-- 触发器验证脚本
-- 用于验证数据库中所有触发器的存在状态
-- 创建时间: 2026-03-01
-- =====================================================

-- =====================================================
-- 查询1: 查看所有触发器的基本信息
-- =====================================================
SELECT 
    name AS 触发器名称,
    tbl_name AS 关联表名,
    sql AS 触发器定义SQL
FROM sqlite_master 
WHERE type = 'trigger'
ORDER BY tbl_name, name;

-- =====================================================
-- 查询2: 查看ProfileExItem表相关的触发器详情
-- =====================================================
SELECT 
    name AS 触发器名称,
    CASE 
        WHEN sql LIKE '%AFTER INSERT%' THEN 'AFTER INSERT'
        WHEN sql LIKE '%AFTER UPDATE%' THEN 'AFTER UPDATE'
        WHEN sql LIKE '%AFTER DELETE%' THEN 'AFTER DELETE'
        WHEN sql LIKE '%BEFORE INSERT%' THEN 'BEFORE INSERT'
        WHEN sql LIKE '%BEFORE UPDATE%' THEN 'BEFORE UPDATE'
        WHEN sql LIKE '%BEFORE DELETE%' THEN 'BEFORE DELETE'
        ELSE '未知类型'
    END AS 触发时机,
    sql AS 完整定义
FROM sqlite_master 
WHERE type = 'trigger' 
    AND tbl_name = 'ProfileExItem';

-- =====================================================
-- 查询3: 统计触发器数量
-- =====================================================
SELECT 
    COUNT(*) AS 触发器总数
FROM sqlite_master 
WHERE type = 'trigger';

-- =====================================================
-- 查询4: 按表分组统计触发器数量
-- =====================================================
SELECT 
    tbl_name AS 表名,
    COUNT(*) AS 触发器数量,
    GROUP_CONCAT(name, ', ') AS 触发器列表
FROM sqlite_master 
WHERE type = 'trigger'
GROUP BY tbl_name;

-- =====================================================
-- 使用说明
-- =====================================================
-- 1. 在 DBeaver 或其他 SQLite 客户端中执行此脚本
-- 2. 查询1: 显示所有触发器的基本信息
-- 3. 查询2: 专门查看 ProfileExItem 表的触发器
-- 4. 查询3: 统计数据库中触发器总数
-- 5. 查询4: 按表分组查看触发器分布
--
-- 预期结果（如果触发器创建成功）：
-- 触发器名称                    | 关联表名      | 触发时机
-- ------------------------------|---------------|----------
-- trg_profile_ex_item_insert    | ProfileExItem | AFTER INSERT
-- trg_profile_ex_item_update    | ProfileExItem | AFTER UPDATE
-- trg_profile_ex_item_delete    | ProfileExItem | AFTER DELETE
