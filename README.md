# v2rayN 节点测试与筛选工具

一款基于 [2dust/v2rayN](https://github.com/2dust/v2rayN) 开发的增强型节点测试与筛选工具，提供全面的节点性能评估、历史记录追踪和智能筛选功能，帮助用户快速找到最优代理节点。

---

## 项目背景

v2rayN 是一款流行的 Windows 平台 v2ray客户端，但在面对大量节点时，用户往往难以快速识别性能最优的节点。本项目通过扩展 v2rayN 的功能，提供专业的节点测试与筛选能力，解决以下痛点：

- **节点质量参差不齐**：大量订阅节点中混杂着无效或低速节点
- **测试历史缺失**：无法追踪节点的历史性能表现
- **筛选效率低下**：手动筛选耗时且容易遗漏优质节点

---

## 功能介绍

- **节点质量评估**：基于 [2dust/v2ray-api](https://github.com/2dust/v2ray-api) 评估节点质量，提供节点质量评估结果。
- **节点历史记录**：记录节点历史测试结果，提供节点历史测试结果。
- **节点筛选**：提供智能筛选功能，自动筛选出性能最佳的节点。
- **优秀节点导出**：自动筛选优秀节点并导出为 v2rayN 兼容的分享链接格式。

## 开发步骤

### 步骤一：获取 2dust/v2rayN 源码

```bash
git clone https://github.com/2dust/v2rayN.git v2rayN_source_code
```

### 步骤二：数据库客户端连接本地数据库

推荐使用 DBeaver。数据库文件路径：`guiConfigs/guiNDB.db`

### 步骤三：创建节点测试历史记录表

为支持节点测试历史记录功能，需要创建 `ProfileExItemHistory` 表，用于记录 `ProfileExItem` 表中节点测试数据的历史变化。

**SQL 文件位置**：`sql/create_profile_ex_item_history_table.sql`

**表结构说明**：

| 字段名 | 数据类型 | 说明 |
|-------|---------|------|
| id | INTEGER | 自增主键，唯一标识每条历史记录 |
| IndexId | TEXT | 关联 ProfileExItem 表的索引ID |
| Delay | INTEGER | 延迟值（毫秒），记录测试时的延迟结果 |
| Speed | REAL | 速度值（MB/s），记录测试时的下载速度 |
| datetime | TEXT | 记录创建时间，默认为当前本地时间 |

**执行方式**：

使用 DBeaver 或其他 SQLite 客户端执行 SQL 脚本，或在代码中通过 `SQLiteHelper` 执行：

```csharp
SQLiteHelper.Instance.CreateTable<ProfileExItemHistory>();
```

### 步骤四：创建历史记录触发器系统

为自动同步 `ProfileExItem` 表的数据变更到 `ProfileExItemHistory` 表，需要创建数据库触发器系统。

**SQL 文件位置**：`sql/create_profile_ex_item_history_triggers.sql`

**触发器功能说明**：

| 触发器名称 | 触发类型 | 功能说明 |
|------------|----------|---------|
| `trg_profile_ex_item_insert` | AFTER INSERT | 当向 ProfileExItem 表插入新记录时，自动复制到历史表 |
| `trg_profile_ex_item_update` | AFTER UPDATE | 当 ProfileExItem 表记录被更新时，将更新后的记录作为新的历史记录插入 |
| `trg_profile_ex_item_delete` | AFTER DELETE | 当 ProfileExItem 表记录被删除时，级联删除历史表中对应的所有记录 |

**触发器特点**：

- **自动同步**：无需手动维护历史记录，所有数据变更自动记录
- **数据完整性**：确保历史记录与主表数据保持一致
- **事务安全**：删除操作使用事务保证原子性
- **可重复执行**：SQL 脚本包含 `DROP TRIGGER IF EXISTS` 语句，可安全重复执行

**执行方式**：

使用 DBeaver 或其他 SQLite 客户端执行 SQL 脚本：

```sql
-- 在 DBeaver 中打开并执行该文件
-- 或通过命令行执行
sqlite3 guiConfigs/guiNDB.db < sql/create_profile_ex_item_history_triggers.sql
```

**注意事项**：

1. **执行顺序**：必须先执行步骤三创建 `ProfileExItemHistory` 表，再执行本步骤创建触发器
2. **数据累积**：每次更新都会产生新的历史记录，建议定期清理旧数据
3. **性能影响**：触发器会增加写操作的开销，但在节点测试场景下影响可忽略
4. **禁用触发器**：如需禁用触发器，可执行 `DROP TRIGGER` 命令

**验证触发器是否生效**：

**SQL 文件位置**：`sql/verify_triggers.sql`

执行以下 SQL 查询语句验证数据库中所有触发器的存在状态：

```sql
-- 查看所有触发器的基本信息
SELECT 
    name AS 触发器名称,
    tbl_name AS 关联表名,
    sql AS 触发器定义SQL
FROM sqlite_master 
WHERE type = 'trigger'
ORDER BY tbl_name, name;
```

**验证步骤**：

1. **查看触发器列表**：执行上述查询，确认以下三个触发器已创建：
   - `trg_profile_ex_item_insert` - 插入触发器
   - `trg_profile_ex_item_update` - 更新触发器
   - `trg_profile_ex_item_delete` - 删除触发器

2. **查看 ProfileExItem 表相关触发器详情**：
   ```sql
   SELECT 
       name AS 触发器名称,
       CASE 
           WHEN sql LIKE '%AFTER INSERT%' THEN 'AFTER INSERT'
           WHEN sql LIKE '%AFTER UPDATE%' THEN 'AFTER UPDATE'
           WHEN sql LIKE '%AFTER DELETE%' THEN 'AFTER DELETE'
           ELSE '未知类型'
       END AS 触发时机
   FROM sqlite_master 
   WHERE type = 'trigger' 
       AND tbl_name = 'ProfileExItem';
   ```

3. **测试触发器功能**：
   ```sql
   -- 插入测试数据
   INSERT INTO ProfileExItem (IndexId, Delay, Speed, Sort, Message) 
   VALUES ('test-id', 100, 5.5, 0, 'test');

   -- 查看历史表是否自动插入记录
   SELECT * FROM ProfileExItemHistory WHERE IndexId = 'test-id';

   -- 更新测试数据
   UPDATE ProfileExItem SET Delay = 150, Speed = 8.0 WHERE IndexId = 'test-id';

   -- 查看历史表是否新增记录
   SELECT * FROM ProfileExItemHistory WHERE IndexId = 'test-id' ORDER BY datetime DESC;

   -- 清理测试数据
   DELETE FROM ProfileExItem WHERE IndexId = 'test-id';
   ```

**预期验证结果**：

| 触发器名称 | 关联表名 | 触发时机 | 状态 |
|-----------|---------|---------|------|
| trg_profile_ex_item_insert | ProfileExItem | AFTER INSERT | ✓ 已创建 |
| trg_profile_ex_item_update | ProfileExItem | AFTER UPDATE | ✓ 已创建 |
| trg_profile_ex_item_delete | ProfileExItem | AFTER DELETE | ✓ 已创建 |

### 步骤五：更新 ProfileItem 表的 Remarks 字段

为解决节点名称重复的问题，需要将唯一的 `IndexId` 追加到 `Remarks` 字段末尾，确保每个节点都有唯一的显示名称。

**SQL 文件位置**：`sql/update_profile_item_remarks.sql`

**操作目的**：

- **解决重复名称问题**：通过在 Remarks 字段中包含唯一的 IndexId，确保每个节点都有唯一的显示名称
- **保持向后兼容**：仅更新 Remarks 字段不包含 IndexId 的记录，避免重复添加
- **提升识别度**：节点名称中包含唯一标识，便于用户快速识别和区分

**执行步骤**：

1. **备份数据库**：在执行更新前，务必备份 `guiConfigs/guiNDB.db` 文件

2. **执行 SQL 脚本**：
   - 使用 DBeaver 或其他 SQLite 客户端打开数据库
   - 执行 `sql/update_profile_item_remarks.sql` 脚本
   - 或通过命令行执行：
     ```bash
     sqlite3 guiConfigs/guiNDB.db < sql/update_profile_item_remarks.sql
     ```

3. **验证更新结果**：
   - 执行脚本中的验证查询，确认更新是否成功
   - 检查节点列表中是否显示带有 IndexId 的节点名称

**更新规则**：

| 条件 | 操作 | 示例 |
|-----|------|------|
| Remarks 不包含 "_${IndexId}" | 追加 "_${IndexId}" 到 Remarks 末尾 | "香港节点" → "香港节点_abc123" |
| Remarks 已包含 "_${IndexId}" | 不进行更新 | "香港节点_abc123" → 保持不变 |
| IndexId 为 NULL 或空 | 不进行更新 | - |

**预期结果**：

- 所有 Remarks 字段不包含 IndexId 的节点都会被更新
- 已包含 IndexId 的节点保持不变
- 节点名称格式：`原名称_IndexId`

**注意事项**：

1. **数据备份**：执行前务必备份数据库文件，以防操作失误
2. **操作不可逆**：更新后无法自动恢复到原始状态，只能通过备份恢复
3. **性能影响**：对于大量节点的数据库，可能需要短暂的执行时间
4. **兼容性**：更新不会影响现有功能，仅修改节点显示名称

**验证步骤**：

1. **查看更新前的状态**（可选）：
   ```sql
   SELECT Remarks, IndexId
   FROM ProfileItem
   WHERE Remarks NOT LIKE '%_' || IndexId
     AND IndexId IS NOT NULL
     AND IndexId != ''
   LIMIT 10;
   ```

2. **查看更新后的状态**：
   ```sql
   SELECT Remarks, IndexId
   FROM ProfileItem
   WHERE Remarks LIKE '%_' || IndexId
     AND IndexId IS NOT NULL
     AND IndexId != ''
   LIMIT 10;
   ```

3. **统计更新的记录数**：
   ```sql
   SELECT COUNT(*)
   FROM ProfileItem
   WHERE Remarks LIKE '%_' || IndexId
     AND IndexId IS NOT NULL
     AND IndexId != '';
   ```

### 步骤六：查询优秀节点

为从 `ProfileExItemHistory` 表中识别表现优秀的节点，提供了两种查询方式：

| 方式 | 工具 | 适用场景 |
|-----|------|---------|
| **方式一** | 数据库客户端（DBeaver等） | 需要可视化操作、自定义查询、导出多种格式 |
| **方式二** | Python 脚本 | 快速查看结果、命令行操作、自动化集成 |

---

#### 方式一：使用数据库客户端执行 SQL

**SQL 文件位置**：`sql/query_top_performing_nodes.sql`

**查询目的和功能**：

该脚本提供多种维度的节点性能分析查询，帮助用户快速识别最优节点：

| 查询编号 | 功能描述 | 适用场景 |
|---------|---------|---------|
| **查询1** | 综合评分筛选 | 基于连接成功率、平均延迟、测试次数和稳定性综合评估节点性能 |
| **查询2** | 即时性能筛选 | 查询全部历史数据，返回延迟最低的节点 |
| **查询3** | 稳定性优先筛选 | 筛选高连接成功率、低波动率的稳定节点 |
| **查询4** | 按订阅分组筛选 | 为每个订阅组分别筛选最优节点 |
| **查询5** | 单个节点趋势分析 | 分析指定节点的完整历史性能变化趋势 |

**关键筛选条件说明**：

| 字段 | 筛选规则 | 说明 |
|-----|---------|------|
| **Delay** | `Delay > 0` | 排除无法连接的节点（Delay = 0 表示连接失败） |
| **Delay** | `Delay IS NOT NULL` | 排除延迟为空的异常记录 |
| **时间范围** | 无限制 | 查询全部历史数据（可按需添加时间范围） |
| **测试次数** | 无限制 | 不设置测试次数的最低或最高阈值（可按需添加） |

**Delay 值含义详解**：

| Delay 值 | 含义 | 处理方式 |
|---------|------|---------|
| `Delay > 0` | 节点正常，值为延迟毫秒数 | ✓ 纳入优秀节点评选 |
| `Delay = 0` | 节点无法连接或超时 | ✗ 排除，不纳入评选 |
| `Delay < 0` | 节点无法连接或超时（兼容旧版本） | ✗ 排除，不纳入评选 |
| `Delay IS NULL` | 数据异常 | ✗ 排除，不纳入评选 |

**时间范围配置方法（可选）**：

如需添加时间范围限制，可在 WHERE 子句中添加以下条件：

```sql
-- 最近24小时
AND h.datetime >= datetime('now', '-1 day')

-- 最近7天
AND h.datetime >= datetime('now', '-7 days')

-- 最近30天
AND h.datetime >= datetime('now', '-30 days')
```

**查询结果解释**：

**查询1（综合评分）结果示例**：

| 字段 | 说明 | 优秀标准 |
|-----|------|---------|
| 节点名称 | 节点的备注名称 | - |
| 协议类型 | 根据 v2rayN 源码映射的协议类型名称（VMess/VLESS/Trojan等） | - |
| 测试次数 | 历史测试记录数 | 越多越可靠 |
| 平均延迟 | 平均响应时间 | < 200ms |
| 最低延迟 | 历史最低延迟 | - |
| 最高延迟 | 历史最高延迟 | - |
| 平均速度 | 平均下载速度 | 越高越好 |
| 延迟波动率 | (最高-最低)/平均 | < 0.5（50%）|
| 最近测试时间 | 最后一次测试时间 | - |
| 连接成功率 | (成功连接次数/总连接次数)×100% | ≥ 95% |

**协议类型映射说明**：

| 数值 | 协议类型 |
|-----|---------|
| 1 | VMess |
| 2 | Custom |
| 3 | Shadowsocks |
| 4 | SOCKS |
| 5 | VLESS |
| 6 | Trojan |
| 7 | Hysteria2 |
| 8 | TUIC |
| 9 | WireGuard |
| 10 | HTTP |
| 11 | Anytls |
| 101 | PolicyGroup |
| 102 | ProxyChain |

**性能评估指标说明**：

| 指标 | 计算公式 | 优秀标准 |
|-----|---------|---------|
| **连接成功率** | `SUM(CASE WHEN Delay > 0 THEN 1 ELSE 0 END) × 100 / COUNT(*)` | ≥ 95% |
| **平均延迟** | `AVG(Delay)` | < 200ms |
| **延迟波动率** | `(MAX - MIN) / AVG` | < 0.5（波动小）|
| **测试次数** | `COUNT(*)` | 越多越可靠 |

**排序规则（查询1）**：

| 优先级 | 排序字段 | 排序方式 | 说明 |
|-------|---------|---------|------|
| 第一 | 连接成功率 | DESC | 连接成功率高的排在前面 |
| 第二 | 测试次数 | DESC | 测试次数多的更可靠 |
| 第三 | 平均延迟 | ASC | 延迟低的排在前面 |
| 第四 | 延迟波动率 | ASC | 波动小的更稳定 |

**连接成功率计算说明**：

```sql
连接成功率 = (成功连接次数 / 总连接次数) × 100%
```

其中：
- **成功连接次数** = `SUM(CASE WHEN h.Delay > 0 THEN 1 ELSE 0 END)`
- **总连接次数** = `COUNT(h.id)`
- **保留两位小数**：`ROUND(..., 2)`

**示例**：
- 某节点共测试10次，其中8次成功（Delay > 0），2次失败（Delay <= 0）
- 连接成功率 = (8 / 10) × 100% = **80.00%**

**使用建议**：

1. **日常使用**：运行查询1，获取综合表现最好的节点（无时间限制）
2. **急需最优节点**：运行查询2，获取延迟最低的节点
3. **长期稳定使用**：运行查询3，筛选高连接成功率、低波动的节点
4. **订阅管理**：运行查询4，为每个订阅组选择最优节点
5. **节点评估**：运行查询5，分析特定节点的完整历史表现

**可选参数配置**：

如需添加筛选条件，可在查询中添加以下参数：

```sql
-- 添加时间范围限制
WHERE h.datetime >= datetime('now', '-7 days')

-- 添加测试次数限制
HAVING COUNT(h.id) >= 3

-- 添加连接成功率阈值
HAVING 连接成功率 >= 95

-- 添加延迟波动率阈值
HAVING 延迟波动率 <= 0.5
```

---

#### 方式二：使用 Python 脚本执行

为方便用户快速执行优秀节点筛选查询，提供了 Python SQL 查询执行脚本，可直接在命令行中查看查询结果。

**程序文件位置**：`run_query1.py`

**功能特点**：

- **自动提取**：自动从 SQL 文件中提取"查询1"语句
- **格式化输出**：以表格格式和 Python 列表格式展示查询结果
- **轻量高效**：仅使用 Python 内置模块，无需安装额外依赖
- **错误处理**：完善的错误捕获和提示机制

**前置条件**：

1. Python 3.6 或更高版本
2. 已完成步骤三至步骤五的数据库配置
3. v2rayN 数据库中存在测试历史数据

**配置说明**：

打开 `run_query1.py` 文件，修改以下配置变量：

```python
# SQLite 数据库文件路径（必填）
DB_PATH = r"D:\APP\v2rayN-windows-64-SelfContained\guiConfigs\guiNDB.db"

# SQL 脚本文件路径（必填）
SQL_FILE_PATH = r"d:\Projects\v2rayN_screen\sql\query_top_performing_nodes.sql"
```

**使用方法**：

```bash
python run_query1.py
```

**输出格式**：

程序提供两种输出格式：

1. **表格格式**：以对齐的表格形式展示所有查询结果，便于阅读
2. **Python 列表格式**：展示列名、数据行数和前5行数据示例，便于程序处理

**输出示例**：

```
========================================================================================================================
查询结果：共 100 条记录
========================================================================================================================
IndexId             | 节点名称                          | 协议类型     | 服务器地址              | 端口  | 测试次数 | ...
------------------------------------------------------------------------------------------------------------------------
5084675974927988181 | 🇭🇰 HK_5084675974927988181        | Shadowsocks | cf.008500.xyz           | 443   | 4        | ...
4802567806037122553 | HK-ss_4802567806037122553        | Shadowsocks | cf.008500.xyz           | 443   | 4        | ...
========================================================================================================================

Python 列表格式：
----------------------------------------
列名: ['IndexId', '节点名称', '协议类型', '服务器地址', '端口', '测试次数', '最近测试时间', '连接成功率', '平均延迟', '最低延迟', '最高延迟', '平均速度', '最高速度', '延迟波动率']
数据行数: 100

前5行数据示例：
  [0] ['5084675974927988181', '🇭🇰 HK_5084675974927988181', 'Shadowsocks', 'cf.008500.xyz', 443, 4, '2026-03-02 01:53:18', 100.0, 43.0, 35, 57, 0.0, 0.0, 0.51]
  [1] ['4802567806037122553', 'HK-ss_4802567806037122553', 'Shadowsocks', 'cf.008500.xyz', 443, 4, '2026-03-02 01:53:18', 100.0, 46.75, 38, 57, 0.0, 0.0, 0.41]
  ...
```

**错误处理**：

| 错误类型 | 处理方式 |
|---------|---------|
| SQL 文件不存在 | 输出错误提示，程序退出 |
| 数据库文件不存在 | 输出错误提示，程序退出 |
| 数据库连接失败 | 输出错误提示，程序退出 |
| 查询执行失败 | 输出错误提示，程序退出 |
| 查询结果为空 | 输出提示信息 |

**注意事项**：

1. **数据库安全**：程序仅进行查询操作，不会修改数据库
2. **字符编码**：SQL 文件和输出均使用 UTF-8 编码
3. **结果限制**：查询1默认返回前100条记录，可在 SQL 文件中修改 `LIMIT` 值

### 步骤七：优秀节点自动导出工具

为方便用户快速导出优秀节点，提供了 Python 自动化导出工具，可自动筛选优秀节点并导出为 v2rayN 兼容的分享链接格式。

**程序文件位置**：`export_top_nodes.py`

**功能特点**：

- **自动筛选**：基于步骤六的查询1，自动筛选评分最高的节点
- **格式兼容**：导出格式与 v2rayN 原生"导出分享链接至剪贴板"功能完全一致
- **多协议支持**：支持 VMess、VLESS、Trojan、Shadowsocks、SOCKS、Hysteria2、TUIC、WireGuard 等主流协议
- **智能命名**：导出文件自动以当前日期命名，如存在则添加时间戳或序号
- **完整日志**：记录程序执行过程，便于问题排查

**前置条件**：

1. Python 3.6 或更高版本（使用内置模块，无需安装额外依赖）
2. 已完成步骤三至步骤六的数据库配置
3. v2rayN 数据库中存在测试历史数据

**配置说明**：

打开 `export_top_nodes.py` 文件，修改以下配置变量：

```python
# SQLite 数据库文件路径（必填）
DB_PATH = r"D:\APP\v2rayN-windows-64-SelfContained\guiConfigs\guiNDB.db"

# SQL 脚本文件路径（必填）
SQL_FILE_PATH = r"d:\Projects\v2rayN_screen\sql\query_top_performing_nodes.sql"

# 导出文件目录（必填）
EXPORT_DIR = r"E:\Download"

# 最大导出节点数量（可选，默认100）
MAX_NODES = 100

# 日志级别（可选，默认 INFO）
LOG_LEVEL = logging.INFO
```

**使用方法**：

1. **配置参数**：根据实际情况修改上述配置变量

2. **运行程序**：
   ```bash
   python export_top_nodes.py
   ```

3. **查看结果**：
   - 程序执行日志会显示在控制台
   - 导出文件保存在配置的 `EXPORT_DIR` 目录下
   - 文件名格式：`MMDD.txt`（如 `0301.txt`）

**执行流程**：

```
程序启动
    ↓
读取 SQL 文件
    ↓
提取查询1语句
    ↓
连接数据库并执行查询
    ↓
获取优秀节点列表
    ↓
查询节点完整配置
    ↓
生成分享链接
    ↓
导出到文件
    ↓
程序结束
```

**支持的协议**：

| 协议类型 | 链接格式 | 说明 |
|---------|---------|------|
| VMess | `vmess://Base64(JSON)` | Base64 编码的 JSON 配置 |
| VLESS | `vless://UUID@地址:端口?参数#备注` | URL 格式 |
| Trojan | `trojan://密码@地址:端口?参数#备注` | URL 格式 |
| Shadowsocks | `ss://Base64(方法:密码)@地址:端口#备注` | SIP002 格式 |
| SOCKS | `socks://Base64(用户:密码)@地址:端口#备注` | URL 格式 |
| Hysteria2 | `hysteria2://密码@地址:端口?参数#备注` | URL 格式 |
| TUIC | `tuic://UUID:密码@地址:端口?参数#备注` | URL 格式 |
| WireGuard | `wireguard://私钥@地址:端口?参数#备注` | URL 格式 |

**导出文件示例**：

```
vmess://eyJ2IjoyLCJwcyI6IuW5v+S4nOeUqOaItyIsImFkZCI6IjE5Mi4xNjguMS4xIiwicG9ydCI6NDQzLCJpZCI6IjEyMzQ1Njc4LWFiY2QtMTIzNC01Njc4LTEyMzQ1Njc4YWJjZCIsImFpZCI6MCwic2N5IjoiYXV0byIsIm5ldCI6IndzIiwidHlwZSI6Im5vbmUiLCJob3N0IjoiZXhhbXBsZS5jb20iLCJwYXRoIjoiL3BhdGgiLCJ0bHMiOiJ0bHMiLCJzbmkiOiJleGFtcGxlLmNvbSJ9
vless://12345678-abcd-1234-5678-12345678abcd@192.168.1.1:443?encryption=none&security=tls&sni=example.com&type=ws&host=example.com&path=/path#节点名称
trojan://password123@192.168.1.1:443?security=tls&sni=example.com&type=ws#节点名称
ss://YWVzLTI1Ni1nY206cGFzc3dvcmQxMjM=@192.168.1.1:8388#节点名称
```

**错误处理**：

程序包含完善的错误处理机制：

| 错误类型 | 处理方式 |
|---------|---------|
| 数据库文件不存在 | 输出错误日志，程序退出 |
| SQL 文件读取失败 | 输出错误日志，程序退出 |
| 数据库连接失败 | 输出错误日志，程序退出 |
| 查询结果为空 | 输出警告日志，程序正常退出 |
| 节点配置不完整 | 跳过该节点，继续处理其他节点 |
| 文件写入失败 | 输出错误日志，程序退出 |
| 权限不足 | 输出错误日志，程序退出 |

**注意事项**：

1. **数据库安全**：程序仅进行查询操作，不会修改或损坏原始数据库
2. **配置完整性**：部分节点可能因配置不完整而无法生成分享链接，程序会跳过这些节点
3. **协议兼容性**：Custom、HTTP、PolicyGroup、ProxyChain 等协议类型暂不支持导出
4. **文件编码**：导出文件使用 UTF-8 编码，确保中文备注正确显示

**验证导出结果**：

1. 打开 v2rayN 应用
2. 点击"服务器" → "从剪贴板导入批量URL"
3. 或直接打开导出的 .txt 文件，复制内容后导入
4. 检查节点是否成功导入并可用

**免责声明**：本工具仅供学习和技术研究使用，请遵守当地法律法规。

---

## 项目结构

```
v2rayN_screen/
├── README.md                                          # 项目说明文档
├── export_top_nodes.py                                # 优秀节点导出工具
├── run_query1.py                                      # SQL 查询执行脚本
├── sql/
│   ├── create_profile_ex_item_history_table.sql       # 创建历史记录表
│   ├── create_profile_ex_item_history_triggers.sql    # 创建触发器
│   ├── verify_triggers.sql                            # 验证触发器
│   ├── update_profile_item_remarks.sql                # 更新节点名称
│   └── query_top_performing_nodes.sql                 # 优秀节点筛选查询
└── v2rayN_source_code/                                # v2rayN 源码（需克隆）
```

---

## 常见问题

### 1. 触发器不生效怎么办？

**检查步骤**：
1. 确认 `ProfileExItemHistory` 表已创建
2. 执行 `sql/verify_triggers.sql` 验证触发器是否存在
3. 检查触发器 SQL 语句是否正确执行

### 2. 查询结果为空怎么办？

**可能原因**：
1. `ProfileExItemHistory` 表中没有历史数据
2. 节点尚未进行测试
3. 时间范围限制过于严格

**解决方法**：
1. 在 v2rayN 中进行节点测试
2. 检查历史表是否有数据：`SELECT COUNT(*) FROM ProfileExItemHistory`
3. 调整查询的时间范围条件

### 3. 导出的节点无法导入 v2rayN？

**可能原因**：
1. 节点配置不完整
2. 协议类型不支持
3. 文件编码问题

**解决方法**：
1. 检查程序日志，查看哪些节点生成失败
2. 确认节点配置是否完整（地址、端口、密码等）
3. 确保导出文件使用 UTF-8 编码

### 4. 如何修改筛选条件？

**修改方法**：
1. 打开 `sql/query_top_performing_nodes.sql`
2. 根据注释说明修改 WHERE 或 HAVING 子句
3. 可添加时间范围、测试次数、连接成功率等条件

---