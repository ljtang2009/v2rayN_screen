-- =====================================================
-- 更新 ProfileItem 表的 Remarks 字段
-- 当 Remarks 字段不包含 "_${IndexId}" 时，将 IndexId 追加到 Remarks 末尾
-- 目的：通过包含唯一的 IndexId 来解决重复 Remarks 值的问题
-- 创建时间: 2026-03-01
-- =====================================================

-- =====================================================
-- 安全更新操作
-- =====================================================
-- 仅更新 Remarks 字段不包含 "_${IndexId}" 的记录
-- 使用 LIKE 操作符进行模式匹配，确保不会重复添加
UPDATE ProfileItem
SET Remarks = Remarks || '_' || IndexId
WHERE Remarks NOT LIKE '%_' || IndexId
  AND IndexId IS NOT NULL
  AND IndexId != '';

-- =====================================================
-- 验证查询
-- =====================================================
-- 1. 查看更新前的状态（可选）
-- SELECT Remarks, IndexId
-- FROM ProfileItem
-- WHERE Remarks NOT LIKE '%_' || IndexId
--   AND IndexId IS NOT NULL
--   AND IndexId != ''
-- LIMIT 10;

-- 2. 查看更新后的状态
SELECT Remarks, IndexId
FROM ProfileItem
WHERE Remarks LIKE '%_' || IndexId
  AND IndexId IS NOT NULL
  AND IndexId != ''
LIMIT 10;

-- 3. 统计更新的记录数
SELECT COUNT(*)
FROM ProfileItem
WHERE Remarks LIKE '%_' || IndexId
  AND IndexId IS NOT NULL
  AND IndexId != '';

-- =====================================================
-- 安全说明
-- =====================================================
-- 1. 该脚本仅更新 Remarks 字段不包含 "_${IndexId}" 的记录
-- 2. 使用 SQLite 的字符串连接操作符 "||" 进行安全拼接
-- 3. 包含对 NULL 和空字符串的检查，避免错误
-- 4. 不会覆盖或修改已包含 IndexId 的 Remarks 值
-- 5. 执行后可以通过验证查询确认更新结果

-- =====================================================
-- 执行步骤
-- =====================================================
-- 1. 备份数据库文件（guiConfigs/guiNDB.db）
-- 2. 使用 DBeaver 或其他 SQLite 客户端打开数据库
-- 3. 执行此 SQL 脚本
-- 4. 运行验证查询确认更新结果
-- 5. 检查是否有错误发生

-- =====================================================
-- 预期结果
-- =====================================================
-- 示例：
-- 原始 Remarks: "香港节点"
-- 原始 IndexId: "abc123"
-- 更新后 Remarks: "香港节点_abc123"
--
-- 注意：如果 Remarks 已经包含 "_${IndexId}"，则不会被更新
-- 示例："香港节点_abc123" 不会被修改
