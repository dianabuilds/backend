# Database migrations

The project uses Alembic for schema migrations.

## Creating a migration

```bash
alembic revision --autogenerate -m "add new table"
```

## Applying migrations

```bash
alembic upgrade head
```

## Viewing history

```bash
alembic history
```

## Rollback scenarios

To revert the last migration:

```bash
alembic downgrade -1
```

To roll back to a specific revision:

```bash
alembic downgrade <revision_id>
```

Always back up your data before downgrading in production. After a rollback you may need to regenerate ORM models or data fixtures to match the previous schema.
