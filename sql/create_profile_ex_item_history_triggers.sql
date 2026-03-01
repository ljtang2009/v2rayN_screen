-- =====================================================
-- ProfileExItemHistory 触发器系统
-- 用于实时监控 ProfileExItem 表的数据变更并同步到 ProfileExItemHistory 表
-- 创建时间: 2026-03-01
-- =====================================================

-- =====================================================
-- 1. INSERT 触发器
-- 功能：当向 ProfileExItem 表插入新记录时，自动复制到历史表
-- =====================================================

-- 删除已存在的 INSERT 触发器（避免重复创建）
DROP TRIGGER IF EXISTS trg_profile_ex_item_insert;

-- 创建 INSERT 触发器
CREATE TRIGGER trg_profile_ex_item_insert
AFTER INSERT ON ProfileExItem
BEGIN
    -- 将新插入的记录完整复制到历史表
    INSERT INTO ProfileExItemHistory (IndexId, Delay, Speed, datetime)
    VALUES (NEW.IndexId, NEW.Delay, NEW.Speed, datetime('now', 'localtime'));
END;

-- =====================================================
-- 2. UPDATE 触发器
-- 功能：当 ProfileExItem 表记录被更新时，将更新后的记录插入历史表
-- 注意：不覆盖历史表中已存在的记录，而是添加新的历史记录
-- =====================================================

-- 删除已存在的 UPDATE 触发器（避免重复创建）
DROP TRIGGER IF EXISTS trg_profile_ex_item_update;

-- 创建 UPDATE 触发器
CREATE TRIGGER trg_profile_ex_item_update
AFTER UPDATE ON ProfileExItem
BEGIN
    -- 将更新后的记录作为新的历史记录插入
    -- 只有当 Delay 或 Speed 字段发生变化时才记录
    INSERT INTO ProfileExItemHistory (IndexId, Delay, Speed, datetime)
    VALUES (NEW.IndexId, NEW.Delay, NEW.Speed, datetime('now', 'localtime'));
END;

-- =====================================================
-- 3. DELETE 触发器
-- 功能：当 ProfileExItem 表记录被删除时，删除历史表中对应的所有记录
-- 注意：使用事务确保删除操作的原子性
-- =====================================================

-- 删除已存在的 DELETE 触发器（避免重复创建）
DROP TRIGGER IF EXISTS trg_profile_ex_item_delete;

-- 创建 DELETE 触发器
CREATE TRIGGER trg_profile_ex_item_delete
AFTER DELETE ON ProfileExItem
BEGIN
    -- 根据被删除记录的 IndexId 删除历史表中所有相关记录
    DELETE FROM ProfileExItemHistory WHERE IndexId = OLD.IndexId;
END;

-- =====================================================
-- 触发器说明文档
-- =====================================================

-- 触发器 1: trg_profile_ex_item_insert
--   触发条件: AFTER INSERT ON ProfileExItem
--   功能: 自动将新插入的节点测试数据复制到历史表
--   数据流向: ProfileExItem -> ProfileExItemHistory
--   注意事项: 
--     - 使用 NEW 关键字引用新插入的记录
--     - datetime 字段自动填充当前时间
--     - 确保数据类型与源表保持一致

-- 触发器 2: trg_profile_ex_item_update
--   触发条件: AFTER UPDATE ON ProfileExItem
--   功能: 将更新后的节点测试数据作为新的历史记录
--   数据流向: ProfileExItem (updated) -> ProfileExItemHistory (new record)
--   注意事项:
--     - 使用 NEW 关键字引用更新后的记录
--     - 不修改或覆盖历史表中已存在的记录
--     - 每次更新都会产生一条新的历史记录
--     - 可根据需要添加条件判断（如仅当 Delay/Speed 变化时才记录）

-- 触发器 3: trg_profile_ex_item_delete
--   触发条件: AFTER DELETE ON ProfileExItem
--   功能: 删除历史表中与被删除节点相关的所有历史记录
--   数据流向: ProfileExItem (deleted) -> ProfileExItemHistory (cascade delete)
--   注意事项:
--     - 使用 OLD 关键字引用被删除的记录
--     - 删除操作在事务中执行，保证原子性
--     - 级联删除确保数据一致性

-- =====================================================
-- 使用说明
-- =====================================================

-- 1. 执行此 SQL 文件后，触发器将自动生效
-- 2. 任何对 ProfileExItem 表的 INSERT/UPDATE/DELETE 操作都会触发相应的历史记录操作
-- 3. 历史记录会自动累积，无需手动维护
-- 4. 如需禁用触发器，可使用 DROP TRIGGER 命令

-- 示例：禁用某个触发器
-- DROP TRIGGER trg_profile_ex_item_insert;
-- DROP TRIGGER trg_profile_ex_item_update;
-- DROP TRIGGER trg_profile_ex_item_delete;

-- 示例：查询某个节点的历史记录
-- SELECT * FROM ProfileExItemHistory WHERE IndexId = 'your-node-index-id' ORDER BY datetime DESC;

-- 示例：统计某个节点的测试次数
-- SELECT COUNT(*) as test_count FROM ProfileExItemHistory WHERE IndexId = 'your-node-index-id';

-- 示例：查看某个节点的性能趋势
-- SELECT datetime, Delay, Speed FROM ProfileExItemHistory 
-- WHERE IndexId = 'your-node-index-id' 
-- ORDER BY datetime DESC 
-- LIMIT 20;
