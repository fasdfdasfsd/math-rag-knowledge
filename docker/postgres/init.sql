-- ============================================================
-- math-rag-knowledge / 数学冒险世界 PostgreSQL 初始化脚本
-- 版本: v2.1 (2026-06-01)
-- 说明:
--   第1节 — v1 遗留表（知识库 RAG 表，保持向后兼容）
--   第2节 — v2.1 新增 14 张核心业务表（7 个领域 × 2 表）
--   第3节 — 索引与触发器
--   第4节 — 初始种子数据
-- ============================================================

-- 启用扩展（pgvector 需单独安装，MVP 使用 Milvus 作为主向量库）
-- CREATE EXTENSION IF NOT EXISTS vector;  -- 注释：镜像未包含 pgvector，待需要时安装
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================
-- 第1节: v1 遗留表（标注为 LEGACY — 保持向后兼容）
-- 知识库 RAG 相关，由文档流水线使用
-- ============================================================

-- 知识点表 (v1 legacy)
CREATE TABLE IF NOT EXISTS knowledge_points (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(256) NOT NULL,
    description     TEXT,
    difficulty      SMALLINT DEFAULT 1 CHECK (difficulty BETWEEN 1 AND 5),
    parent_id       INTEGER REFERENCES knowledge_points(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE knowledge_points IS '[v1 LEGACY] 知识库知识点定义';

-- 文档表 (v1 legacy)
CREATE TABLE IF NOT EXISTS documents (
    id              SERIAL PRIMARY KEY,
    title           VARCHAR(512) NOT NULL,
    file_path       VARCHAR(1024),
    file_type       VARCHAR(32),
    file_size       BIGINT,
    status          VARCHAR(32) DEFAULT 'pending',
    metadata_json   JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE documents IS '[v1 LEGACY] 上传文档元数据';

-- 文档分块表 (v1 legacy)
CREATE TABLE IF NOT EXISTS document_chunks (
    id              SERIAL PRIMARY KEY,
    document_id     INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index     INTEGER NOT NULL,
    content         TEXT NOT NULL,
    token_count     INTEGER DEFAULT 0,
    embedding_id    VARCHAR(256),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE document_chunks IS '[v1 LEGACY] 文档分块及其向量 ID';

-- 对话记录表 (v1 legacy)
CREATE TABLE IF NOT EXISTS conversations (
    id              SERIAL PRIMARY KEY,
    session_id      VARCHAR(64) NOT NULL,
    role            VARCHAR(32) NOT NULL,
    content         TEXT NOT NULL,
    metadata_json   JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE conversations IS '[v1 LEGACY] LLM 对话历史记录';

-- ============================================================
-- 第2节: v2.1 核心表 — 数学冒险世界业务领域
-- 7 个领域 × 2 张表 = 14 张核心表
-- ============================================================

-- ---------- 领域 1: 知识图谱 (Knowledge Graph) ----------

-- kg_nodes: 知识点图谱节点
CREATE TABLE IF NOT EXISTS kg_nodes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            VARCHAR(64) NOT NULL UNIQUE,          -- 如 "fraction-addition"
    name            VARCHAR(256) NOT NULL,                 -- 中文名称
    domain          VARCHAR(32) NOT NULL                   -- number-algebra | geometry | statistics | comprehensive
                    CHECK (domain IN ('number-algebra', 'geometry', 'statistics', 'comprehensive')),
    description     TEXT,
    difficulty_base SMALLINT NOT NULL DEFAULT 3 CHECK (difficulty_base BETWEEN 1 AND 5),
    metadata_json   JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ                               -- 软删除
);
COMMENT ON TABLE kg_nodes IS 'v2.1 知识图谱节点 — 每个知识点为一个节点';
COMMENT ON COLUMN kg_nodes.code IS '知识点唯一编码，作为语义标识符';
COMMENT ON COLUMN kg_nodes.domain IS '所属数学领域分类';

-- kg_edges: 知识点关系边
CREATE TABLE IF NOT EXISTS kg_edges (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id       UUID NOT NULL REFERENCES kg_nodes(id) ON DELETE CASCADE,
    target_id       UUID NOT NULL REFERENCES kg_nodes(id) ON DELETE CASCADE,
    relation_type   VARCHAR(16) NOT NULL                    -- PREREQ | EXTEND | RELATED
                    CHECK (relation_type IN ('PREREQ', 'EXTEND', 'RELATED')),
    weight          NUMERIC(3,2) DEFAULT 1.0 CHECK (weight BETWEEN 0.0 AND 1.0),
    metadata_json   JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source_id, target_id, relation_type)
);
COMMENT ON TABLE kg_edges IS 'v2.1 知识图谱边 — PREREQ=前置依赖, EXTEND=后续扩展, RELATED=关联易错';
COMMENT ON COLUMN kg_edges.weight IS '关系强度 0.0~1.0，用于排序和权重计算';

-- ---------- 领域 2: 用户数据 (User Data) ----------

-- users: 用户注册信息
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role            VARCHAR(16) NOT NULL DEFAULT 'student'
                    CHECK (role IN ('student', 'parent', 'teacher', 'admin')),
    age_group       VARCHAR(8)                              -- '6-8' | '9-11' | '12-14' | NULL(parent/teacher)
                    CHECK (age_group IN ('6-8', '9-11', '12-14')),
    age_verify_level SMALLINT NOT NULL DEFAULT 0 CHECK (age_verify_level BETWEEN 0 AND 3),
    display_name    VARCHAR(100),
    email           VARCHAR(255),
    email_verified  BOOLEAN NOT NULL DEFAULT FALSE,
    parent_email    VARCHAR(255),                            -- 家长的邮箱（用于 VPC 同意流程）
    parent_consent_granted BOOLEAN NOT NULL DEFAULT FALSE,
    password_hash   VARCHAR(256),                            -- bcrypt 哈希
    status          VARCHAR(20) NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'suspended', 'deleted')),
    metadata_json   JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);
COMMENT ON TABLE users IS 'v2.1 用户注册信息 — 学生/家长/教师/管理员';
COMMENT ON COLUMN users.age_verify_level IS 'COPPA 年龄验证级别 0=自声明, 1=邮箱, 2=支付验证, 3=正式认证';
COMMENT ON COLUMN users.parent_consent_granted IS 'VPC 家长同意是否已授予';

-- user_sessions: 用户认证与会话
CREATE TABLE IF NOT EXISTS user_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token   VARCHAR(512) NOT NULL,
    device_fingerprint VARCHAR(128),
    ip_address      INET,
    is_valid        BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE user_sessions IS 'v2.1 用户认证会话 — refresh_token 轮转管理';
COMMENT ON COLUMN user_sessions.device_fingerprint IS '设备指纹（可选，用于 Token 绑定）';

-- ---------- 领域 3: 世界状态 (World State) ----------

-- world_states: 每位用户的世界进化状态
CREATE TABLE IF NOT EXISTS world_states (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    current_phase   SMALLINT NOT NULL DEFAULT 1 CHECK (current_phase BETWEEN 1 AND 5),
    current_theme   VARCHAR(32) NOT NULL DEFAULT 'magic-forest'
                    CHECK (current_theme IN (
                        'magic-forest', 'ocean-kingdom', 'space-station',
                        'ancient-civilization', 'seasonal'
                    )),
    current_vehicle VARCHAR(24) NOT NULL DEFAULT 'magic-broom'
                    CHECK (current_vehicle IN (
                        'magic-broom', 'submarine', 'starship',
                        'time-machine', 'golden-chariot', 'generic-portal'
                    )),
    total_levels_completed INTEGER NOT NULL DEFAULT 0,
    current_node_id VARCHAR(64),                             -- 地图节点 ID (varchar 兼容多种 ID 格式)
    metadata_json   JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id)
);
COMMENT ON TABLE world_states IS 'v2.1 每位用户的世界进化状态（只有一行/用户）';
COMMENT ON COLUMN world_states.current_phase IS '进化阶段 1=新手村, 2=海底, 3=星际, 4=古文明, 5=季节/交叉';

-- map_node_progress: 地图节点解锁进度
CREATE TABLE IF NOT EXISTS map_node_progress (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    node_id         VARCHAR(64) NOT NULL,                    -- 节点标识符
    node_name       VARCHAR(256),
    status          VARCHAR(20) NOT NULL DEFAULT 'locked'
                    CHECK (status IN ('locked', 'available', 'in_progress', 'completed')),
    unlocked_at     TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    metadata_json   JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, node_id)
);
COMMENT ON TABLE map_node_progress IS 'v2.1 每位用户的地图节点解锁状态';

-- ---------- 领域 4: 学情画像 (Learning Profile) ----------

-- mastery_records: 知识点掌握度矩阵
CREATE TABLE IF NOT EXISTS mastery_records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kg_node_id      UUID NOT NULL REFERENCES kg_nodes(id) ON DELETE CASCADE,
    mastery_level   NUMERIC(4,3) NOT NULL DEFAULT 0.0 CHECK (mastery_level BETWEEN 0.0 AND 1.0),
    correct_count   INTEGER NOT NULL DEFAULT 0,
    total_count     INTEGER NOT NULL DEFAULT 0,
    consecutive_correct INTEGER NOT NULL DEFAULT 0,
    consecutive_error   INTEGER NOT NULL DEFAULT 0,
    last_reviewed_at TIMESTAMPTZ,
    next_review_at  TIMESTAMPTZ,                              -- 间隔复习调度时间
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, kg_node_id)
);
COMMENT ON TABLE mastery_records IS 'v2.1 知识点掌握度矩阵 — 每用户每知识点一行';
COMMENT ON COLUMN mastery_records.mastery_level IS '掌握度 0.0~1.0，由决策引擎更新';

-- learning_profiles: 学习风格与偏好画像
CREATE TABLE IF NOT EXISTS learning_profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    thinking_style  VARCHAR(16) DEFAULT 'intuitive'
                    CHECK (thinking_style IN ('analytical', 'intuitive')),
    preferred_senses JSONB DEFAULT '["visual", "auditory"]',  -- preferredSenses 数组
    favorite_npc_ids JSONB DEFAULT '[]',                      -- 喜好 NPC ID 列表
    weak_point_ids  JSONB DEFAULT '[]',                        -- 薄弱知识点 ID 列表
    interaction_count INTEGER NOT NULL DEFAULT 0,
    avg_completion_time_sec NUMERIC(8,2),
    metadata_json   JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id)
);
COMMENT ON TABLE learning_profiles IS 'v2.1 学习风格与偏好画像（只有一行/用户）';
COMMENT ON COLUMN learning_profiles.preferred_senses IS '偏好感官类型数组: visual, auditory, tactile, olfactory';

-- ---------- 领域 5: NPC 角色 (NPC Characters) ----------

-- npc_characters: NPC 角色定义
CREATE TABLE IF NOT EXISTS npc_characters (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            VARCHAR(64) NOT NULL UNIQUE,              -- 如 "fraction-prince"
    name            VARCHAR(128) NOT NULL,                    -- 中文角色名
    domain_tags     JSONB DEFAULT '[]',                       -- 关联领域标签
    personality_traits JSONB DEFAULT '[]',                    -- 性格特征标签
    visual_desc     TEXT,                                     -- 外观描述
    catchphrases    JSONB DEFAULT '[]',                       -- 口头禅列表
    difficulty_range SMALLINT[] DEFAULT '{1,5}',              -- 适用难度范围 [min, max]
    metadata_json   JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE npc_characters IS 'v2.1 NPC 角色定义 — 30+ 数学拟人化角色';

-- npc_relationship_progress: 用户与 NPC 的关系进展
CREATE TABLE IF NOT EXISTS npc_relationship_progress (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    npc_id          UUID NOT NULL REFERENCES npc_characters(id) ON DELETE CASCADE,
    relationship_level SMALLINT NOT NULL DEFAULT 0 CHECK (relationship_level BETWEEN 0 AND 5),
    total_interactions INTEGER NOT NULL DEFAULT 0,
    last_interaction_at TIMESTAMPTZ,
    last_interaction_summary TEXT,                            -- 上次互动的剧情摘要
    metadata_json   JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, npc_id)
);
COMMENT ON TABLE npc_relationship_progress IS 'v2.1 用户-NPC 关系进展 — 0=陌生, 5=挚友';

-- ---------- 领域 6: 课标映射 (Curriculum Mapping) ----------

-- curriculum_standards: 国家标准课标定义
CREATE TABLE IF NOT EXISTS curriculum_standards (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grade           SMALLINT NOT NULL CHECK (grade BETWEEN 1 AND 9),
    semester        SMALLINT NOT NULL CHECK (semester IN (1, 2)),
    chapter         VARCHAR(256) NOT NULL,                    -- 章节名
    topic           VARCHAR(512),                              -- 主题描述
    metadata_json   JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE curriculum_standards IS 'v2.1 国家标准课标定义 — 按年级/学期/章节组织';

-- knowledge_curriculum_mapping: 知识点 ↔ 课标映射
CREATE TABLE IF NOT EXISTS knowledge_curriculum_mapping (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kg_node_id      UUID NOT NULL REFERENCES kg_nodes(id) ON DELETE CASCADE,
    curriculum_id   UUID NOT NULL REFERENCES curriculum_standards(id) ON DELETE CASCADE,
    relevance       NUMERIC(3,2) DEFAULT 1.0 CHECK (relevance BETWEEN 0.0 AND 1.0),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (kg_node_id, curriculum_id)
);
COMMENT ON TABLE knowledge_curriculum_mapping IS 'v2.1 知识点与课标的 N:M 映射';

-- ---------- 领域 7: 关卡缓存 (Level Cache) ----------

-- level_pregen_cache: 预生成关卡缓存池
CREATE TABLE IF NOT EXISTS level_pregen_cache (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    constraint_hash VARCHAR(64) NOT NULL,                     -- 约束包哈希（用于匹配）
    status          VARCHAR(20) NOT NULL DEFAULT 'pre_generating'
                    CHECK (status IN ('pre_generating', 'ready', 'claimed', 'expired')),
    context_json    JSONB NOT NULL DEFAULT '{}',              -- 完整 ConstraintPackage
    level_json      JSONB,                                    -- 生成的完整关卡内容（审核通过后）
    grade_level     SMALLINT,
    difficulty_range SMALLINT[],
    claimed_by      UUID REFERENCES users(id),                -- 认领该关卡的 user_id
    claimed_at      TIMESTAMPTZ,
    ttl             INTERVAL NOT NULL DEFAULT '6 hours',      -- 过期时间
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE level_pregen_cache IS 'v2.1 预生成关卡缓存池 — Background Worker 填充, LLM 调用替代';
COMMENT ON COLUMN level_pregen_cache.constraint_hash IS 'MD5(constraint_package) 用于快速匹配预生成结果';
CREATE INDEX IF NOT EXISTS idx_pregen_lookup ON level_pregen_cache(constraint_hash, status)
    WHERE status = 'ready';

-- level_completion_history: 闯关历史记录
CREATE TABLE IF NOT EXISTS level_completion_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kg_node_id      UUID NOT NULL REFERENCES kg_nodes(id),
    level_json      JSONB NOT NULL,                           -- 实际使用的关卡内容快照
    mode_type       VARCHAR(16) NOT NULL
                    CHECK (mode_type IN ('hero', 'tutor', 'explorer', 'review')),
    difficulty_used SMALLINT NOT NULL CHECK (difficulty_used BETWEEN 1 AND 5),
    is_pregen_hit   BOOLEAN NOT NULL DEFAULT FALSE,           -- 是否命中预生成池
    interaction_data JSONB DEFAULT '[]',                      -- 答题交互记录
    score           NUMERIC(5,2),                              -- 关卡得分
    total_time_sec  NUMERIC(8,2),                             -- 完成耗时
    llm_tokens_used INTEGER DEFAULT 0,                        -- 本次 LLM Token 消耗
    need_review     BOOLEAN NOT NULL DEFAULT FALSE,            -- 是否需要人工审核
    completed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE level_completion_history IS 'v2.1 闯关历史记录 — 用于学情分析、审计、回放';

-- ---------- 安全架构补充表 ----------

-- audit_log: HMAC 链式哈希审计日志（SecEng 要求）
CREATE TABLE IF NOT EXISTS audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type      VARCHAR(64) NOT NULL,                     -- 如 "level.completed", "user.consent.granted"
    actor_id        UUID REFERENCES users(id),
    resource_type   VARCHAR(64),
    resource_id     VARCHAR(128),
    action          VARCHAR(32) NOT NULL,
    detail_json     JSONB DEFAULT '{}',
    prev_hash       VARCHAR(64) NOT NULL,                     -- 上一条记录的 hash
    current_hash    VARCHAR(64) NOT NULL,                     -- HMAC-SHA256(prev_hash || event_data)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE audit_log IS '[安全] HMAC 链式哈希审计日志 — 不可篡改';

-- ============================================================
-- 第3节: 索引与触发器
-- ============================================================

-- ---- 3a. v1 遗留表索引 ----
CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_docs_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON document_chunks(document_id);

-- ---- 3b. v2.1 核心表索引 ----
-- 知识图谱
CREATE INDEX IF NOT EXISTS idx_kg_nodes_code ON kg_nodes(code);
CREATE INDEX IF NOT EXISTS idx_kg_nodes_domain ON kg_nodes(domain);
CREATE INDEX IF NOT EXISTS idx_kg_edges_source ON kg_edges(source_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_kg_edges_target ON kg_edges(target_id, relation_type);

-- 用户
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id, is_valid)
    WHERE is_valid = TRUE;

-- 世界状态
CREATE INDEX IF NOT EXISTS idx_world_states_user ON world_states(user_id);
CREATE INDEX IF NOT EXISTS idx_map_progress_user ON map_node_progress(user_id, status);

-- 学情画像
CREATE INDEX IF NOT EXISTS idx_mastery_user ON mastery_records(user_id);
CREATE INDEX IF NOT EXISTS idx_mastery_next_review ON mastery_records(next_review_at)
    WHERE next_review_at IS NOT NULL;

-- NPC
CREATE INDEX IF NOT EXISTS idx_npc_relationship_user ON npc_relationship_progress(user_id);

-- 课标
CREATE INDEX IF NOT EXISTS idx_curriculum_grade ON curriculum_standards(grade, semester);
CREATE INDEX IF NOT EXISTS idx_kcm_kg_node ON knowledge_curriculum_mapping(kg_node_id);
CREATE INDEX IF NOT EXISTS idx_kcm_curriculum ON knowledge_curriculum_mapping(curriculum_id);

-- 关卡缓存
CREATE INDEX IF NOT EXISTS idx_pregen_status ON level_pregen_cache(status, created_at);
CREATE INDEX IF NOT EXISTS idx_level_history_user ON level_completion_history(user_id, completed_at);

-- 审计日志
CREATE INDEX IF NOT EXISTS idx_audit_log_actor ON audit_log(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_type ON audit_log(event_type, created_at);

-- ---- 3c. updated_at 自动更新触发器 ----
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为所有含 updated_at 的 v2.1 表附加触发器
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN
        SELECT unnest(ARRAY[
            'kg_nodes', 'users', 'world_states', 'map_node_progress',
            'mastery_records', 'learning_profiles', 'npc_characters',
            'npc_relationship_progress', 'curriculum_standards',
            'level_pregen_cache'
        ])
    LOOP
        EXECUTE format(
            'CREATE TRIGGER set_%I_updated_at
             BEFORE UPDATE ON %I
             FOR EACH ROW
             EXECUTE FUNCTION update_updated_at_column()',
            tbl, tbl
        );
    END LOOP;
END;
$$;

-- ============================================================
-- 第4节: 初始种子数据
-- ============================================================

-- 插入基础 NPC 角色（30+ 中的前 5 个 MVP 角色）
INSERT INTO npc_characters (code, name, domain_tags, personality_traits, catchphrases, difficulty_range)
VALUES
    ('fraction-prince',   '分数王子',   '["number-algebra"]',  '["勇敢", "正义"]',  '["数学的勇气就在你心中！"]',               '{1,5}'),
    ('zero-king',         '零国王',     '["number-algebra"]',  '["睿智", "温和"]',  '["零不是没有，而是起点。"]',               '{1,3}'),
    ('decimal-elf',       '小数精灵',   '["number-algebra"]',  '["调皮", "机灵"]',  '["小数点会跳舞哟~"]',                      '{2,5}'),
    ('geometry-dragon',   '几何龙',    '["geometry"]',        '["威严", "神秘"]',  '["三角形的秘密在第三边。"]',               '{2,5}'),
    ('statistics-owl',    '统计猫头鹰', '["statistics"]',      '["冷静", "博学"]',  '["数据会说话，只要你愿意听。"]',           '{3,5}')
ON CONFLICT (code) DO NOTHING;

-- 插入初始知识点（小学数学核心知识点前置节点）
INSERT INTO kg_nodes (code, name, domain, description, difficulty_base)
VALUES
    ('number-concept',       '数的概念',     'number-algebra', '自然数、整数的基本概念', 1),
    ('addition-subtraction', '加减法',       'number-algebra', '100 以内加减法',        1),
    ('multiplication-div',   '乘除法',       'number-algebra', '九九乘法表及简单除法',  2),
    ('fraction-concept',     '分数概念',     'number-algebra', '分数的基本概念和表示',  2),
    ('fraction-comparison',  '分数比较',     'number-algebra', '同分母/异分母分数比较', 3),
    ('fraction-addition',    '分数加减',     'number-algebra', '同分母/异分母分数加减', 3),
    ('decimal-concept',      '小数概念',     'number-algebra', '小数的基本概念',        2),
    ('geometry-basic',       '基础几何',     'geometry',       '点线面角的基本认识',    2),
    ('area-perimeter',       '周长与面积',   'geometry',       '长方形正方形的周长面积', 3)
ON CONFLICT (code) DO NOTHING;

-- 插入知识图谱边关系
INSERT INTO kg_edges (source_id, target_id, relation_type, weight)
SELECT
    (SELECT id FROM kg_nodes WHERE code = 'number-concept'),
    (SELECT id FROM kg_nodes WHERE code = 'addition-subtraction'),
    'PREREQ', 1.0
WHERE EXISTS (SELECT 1 FROM kg_nodes WHERE code = 'number-concept')
  AND EXISTS (SELECT 1 FROM kg_nodes WHERE code = 'addition-subtraction');

INSERT INTO kg_edges (source_id, target_id, relation_type, weight)
SELECT
    (SELECT id FROM kg_nodes WHERE code = 'addition-subtraction'),
    (SELECT id FROM kg_nodes WHERE code = 'multiplication-div'),
    'PREREQ', 1.0
WHERE EXISTS (SELECT 1 FROM kg_nodes WHERE code = 'addition-subtraction')
  AND EXISTS (SELECT 1 FROM kg_nodes WHERE code = 'multiplication-div');

INSERT INTO kg_edges (source_id, target_id, relation_type, weight)
SELECT
    (SELECT id FROM kg_nodes WHERE code = 'multiplication-div'),
    (SELECT id FROM kg_nodes WHERE code = 'fraction-concept'),
    'PREREQ', 1.0
WHERE EXISTS (SELECT 1 FROM kg_nodes WHERE code = 'multiplication-div')
  AND EXISTS (SELECT 1 FROM kg_nodes WHERE code = 'fraction-concept');

INSERT INTO kg_edges (source_id, target_id, relation_type, weight)
SELECT
    (SELECT id FROM kg_nodes WHERE code = 'fraction-concept'),
    (SELECT id FROM kg_nodes WHERE code = 'fraction-comparison'),
    'PREREQ', 1.0
WHERE EXISTS (SELECT 1 FROM kg_nodes WHERE code = 'fraction-concept')
  AND EXISTS (SELECT 1 FROM kg_nodes WHERE code = 'fraction-comparison');

INSERT INTO kg_edges (source_id, target_id, relation_type, weight)
SELECT
    (SELECT id FROM kg_nodes WHERE code = 'fraction-comparison'),
    (SELECT id FROM kg_nodes WHERE code = 'fraction-addition'),
    'PREREQ', 1.0
WHERE EXISTS (SELECT 1 FROM kg_nodes WHERE code = 'fraction-comparison')
  AND EXISTS (SELECT 1 FROM kg_nodes WHERE code = 'fraction-addition');
