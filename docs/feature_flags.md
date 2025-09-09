# Feature Flags

The backend exposes several feature flags that are disabled by default. They can
be toggled via the admin interface or API to gradually roll out features.

| Key | Description |
| --- | ----------- |
| content.scheduling | Enable scheduled publishing for content |
| admin.beta_dashboard | Enable beta version of admin dashboard |
| notifications.digest | Enable daily notifications digest |
| premium.gifting | Allow gifting premium subscriptions |
| nodes.navigation_v2 | Enable experimental node navigation v2 |
| navigation.weighted_manual_transitions | Enable weighted sorting for manual transitions |
| nodes.legacy_type_routes (env: FF_NODES_LEGACY_TYPE_ROUTES) | Register legacy admin type routes under `/admin/accounts/{account_id}/nodes/types/*` |
