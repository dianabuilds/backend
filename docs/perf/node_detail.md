# Node detail query performance

This document shows query plans for `NodeService.get` after adding indexes.

## Node patch overlay

Before adding `ix_node_patches_node_id` the overlay query scanned the whole table:

```
Seq Scan on node_patches  (cost=0.00..944.00 rows=48 width=29) (actual time=0.077..2.669 rows=55 loops=1)
  Filter: ((reverted_at IS NULL) AND (node_id = 1))
  Rows Removed by Filter: 49945
```

After creating the index PostgreSQL switches to a bitmap index scan:

```
Bitmap Heap Scan on node_patches  (cost=4.66..134.56 rows=48 width=29) (actual time=0.092..0.136 rows=55 loops=1)
  Recheck Cond: ((node_id = 1) AND (reverted_at IS NULL))
  Heap Blocks: exact=51
  ->  Bitmap Index Scan on ix_node_patches_node_id  (cost=0.00..4.65 rows=48 width=0) (actual time=0.076..0.076 rows=55 loops=1)
        Index Cond: (node_id = 1)
```

## Content item lookup

`NodeService.get` also looks up the content item by its primary key. The plan shows the index usage:

```
Index Scan using content_items_pkey on content_items  (cost=0.29..8.31 rows=1 width=14) (actual time=0.030..0.031 rows=1 loops=1)
  Index Cond: (id_bigint = 1)
```
