# Notifications

## Banners

Notifications support a `placement` field to control how they are displayed. The `banner` placement denotes messages shown at the top of the interface.

Clients can request the active banner by querying the notifications endpoint with the `placement=banner` parameter. The first returned item should be rendered as the current banner.
