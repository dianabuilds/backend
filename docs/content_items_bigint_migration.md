# Content item bigint migration

This migration converts `content_items` and `node_patches` identifiers from UUIDs to bigint sequences.

## Upgrade

```
alembic upgrade 20260115_content_items_bigint_ids
```

## Rollback

```
alembic downgrade 20260101_node_tags_node_id_bigint
```

Downgrading recreates UUID columns with new values. Restore from backup if you need original UUIDs.
