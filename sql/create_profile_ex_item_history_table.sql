-- =====================================================
-- ProfileExItemHistory 表创建脚本
-- 用于记录 ProfileExItem 表中节点测试数据的历史变化
-- 创建时间: 2026-03-01
-- =====================================================

-- 创建 ProfileExItemHistory 表
CREATE TABLE IF NOT EXISTS ProfileExItemHistory (
    Id          INTEGER PRIMARY KEY AUTOINCREMENT,
    IndexId     TEXT NOT NULL,
    Delay       INTEGER DEFAULT 0,
    Speed       REAL DEFAULT 0,
    Datetime    TEXT DEFAULT (datetime('now', 'localtime'))
);

-- 创建索引以优化按 IndexId 查询历史记录的性能
CREATE INDEX IF NOT EXISTS idx_profile_ex_item_history_index_id 
    ON ProfileExItemHistory(IndexId);

-- 创建索引以优化按时间范围查询的性能
CREATE INDEX IF NOT EXISTS idx_profile_ex_item_history_datetime 
    ON ProfileExItemHistory(datetime);

-- 字段说明:
-- Id        : 自增主键，唯一标识每条历史记录
-- IndexId   : 关联 ProfileExItem 表的索引ID，标识哪个节点的测试数据
-- Delay     : 延迟值(毫秒)，记录测试时的延迟结果
-- Speed     : 速度值(MB/s)，记录测试时的下载速度
-- Datetime  : 记录创建时间，默认为当前本地时间
