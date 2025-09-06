-- upgrade
CREATE TABLE spaces (
    id BIGSERIAL PRIMARY KEY,
    type VARCHAR NOT NULL,
    owner_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR NOT NULL,
    settings JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE space_members (
    space_id BIGINT NOT NULL REFERENCES spaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR NOT NULL,
    PRIMARY KEY (space_id, user_id)
);

ALTER TABLE nodes ADD COLUMN space_id BIGINT;
UPDATE nodes SET space_id = account_id;
ALTER TABLE nodes ADD CONSTRAINT fk_nodes_space_id_spaces FOREIGN KEY (space_id) REFERENCES spaces(id);
ALTER TABLE nodes DROP CONSTRAINT IF EXISTS nodes_slug_key;
CREATE UNIQUE INDEX ix_nodes_space_id_slug ON nodes (space_id, slug);
CREATE INDEX ix_nodes_space_id_created_at ON nodes (space_id, created_at);

ALTER TABLE node_transitions ADD COLUMN space_id BIGINT;
UPDATE node_transitions nt SET space_id = n.account_id FROM nodes n WHERE nt.from_node_id = n.id;
ALTER TABLE node_transitions ADD CONSTRAINT fk_node_transitions_space_id_spaces FOREIGN KEY (space_id) REFERENCES spaces(id);
CREATE INDEX ix_node_transitions_space_id_created_at ON node_transitions (space_id, created_at);

ALTER TABLE navigation_cache ADD COLUMN space_id BIGINT;
UPDATE navigation_cache nc SET space_id = n.account_id FROM nodes n WHERE nc.node_slug = n.slug;
ALTER TABLE navigation_cache ADD CONSTRAINT fk_navigation_cache_space_id_spaces FOREIGN KEY (space_id) REFERENCES spaces(id);
ALTER TABLE navigation_cache DROP CONSTRAINT IF EXISTS navigation_cache_node_slug_key;
ALTER TABLE navigation_cache ADD CONSTRAINT uq_nav_cache_space_slug UNIQUE (space_id, node_slug);
CREATE INDEX ix_navigation_cache_space_id_generated_at ON navigation_cache (space_id, generated_at);

INSERT INTO spaces (id, type, owner_id, title, settings)
SELECT id, kind::text, owner_user_id, name, settings_json FROM accounts;
SELECT setval('spaces_id_seq', (SELECT COALESCE(MAX(id),0) FROM spaces));
INSERT INTO space_members (space_id, user_id, role)
SELECT account_id, user_id, role::text FROM account_members;

-- downgrade
DROP INDEX IF EXISTS ix_navigation_cache_space_id_generated_at;
ALTER TABLE navigation_cache DROP CONSTRAINT IF EXISTS uq_nav_cache_space_slug;
ALTER TABLE navigation_cache ADD CONSTRAINT navigation_cache_node_slug_key UNIQUE (node_slug);
ALTER TABLE navigation_cache DROP CONSTRAINT IF EXISTS fk_navigation_cache_space_id_spaces;
ALTER TABLE navigation_cache DROP COLUMN space_id;

DROP INDEX IF EXISTS ix_node_transitions_space_id_created_at;
ALTER TABLE node_transitions DROP CONSTRAINT IF EXISTS fk_node_transitions_space_id_spaces;
ALTER TABLE node_transitions DROP COLUMN space_id;

DROP INDEX IF EXISTS ix_nodes_space_id_created_at;
DROP INDEX IF EXISTS ix_nodes_space_id_slug;
ALTER TABLE nodes ADD CONSTRAINT nodes_slug_key UNIQUE (slug);
ALTER TABLE nodes DROP CONSTRAINT IF EXISTS fk_nodes_space_id_spaces;
ALTER TABLE nodes DROP COLUMN space_id;

DROP TABLE space_members;
DROP TABLE spaces;
