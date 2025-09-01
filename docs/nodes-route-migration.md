# Nodes route migration

The admin UI previously used `:type` in node routes (`/nodes/:type/:id`).
Routes now use only the numeric identifier:

```
/nodes/:id
```

The `id` segment refers to the numeric `node.id`. For a limited transition
period the backend also accepts a `content_items.id`, but new clients should
send the `node_id`.

## Application updates

* React Router definitions should drop the `:type` segment.
* Links to nodes must point to `/nodes/${id}`.
* Route params should be parsed as integers instead of validated as UUIDs.

## Codemod

A jscodeshift script is provided to update codebases:

```bash
npx jscodeshift -t scripts/codemods/drop-node-type-segment.ts "src/**/*.tsx"
```

The codemod replaces route strings like `/nodes/:type/:id` with `/nodes/:id`,
updates `useParams` calls, and rewrites links such as
```
<navigate to={`/nodes/${type}/${id}`}/>
```
into `to={\`/nodes/${id}\`}`.

Review all changes and run your test suite after applying the codemod.
