from __future__ import annotations

import hashlib
import json

from domains.platform.notifications.adapters.sql.notifications import (
    NotificationRepository,
)


def test_payload_hash_is_stable_for_equivalent_meta() -> None:
    meta_a = {"b": 2, "a": 1}
    meta_b = {"a": 1, "b": 2}

    hash_a = NotificationRepository._payload_hash(
        title="hello",
        message="world",
        type_="system",
        topic_key="topic",
        channel_key="in_app",
        cta_label="Go",
        cta_url="https://example.com",
        meta=meta_a,
    )
    hash_b = NotificationRepository._payload_hash(
        title="hello",
        message="world",
        type_="system",
        topic_key="topic",
        channel_key="in_app",
        cta_label="Go",
        cta_url="https://example.com",
        meta=meta_b,
    )
    assert hash_a == hash_b

    expected_meta = json.dumps({"a": 1, "b": 2}, ensure_ascii=False, sort_keys=True)
    expected_source = "|".join(
        [
            "hello",
            "world",
            "system",
            "topic",
            "in_app",
            "Go",
            "https://example.com",
            expected_meta,
        ]
    )
    assert hash_a == hashlib.md5(expected_source.encode("utf-8")).hexdigest()


def test_payload_hash_changes_when_payload_differs() -> None:
    base_meta = {"a": 1}
    base_hash = NotificationRepository._payload_hash(
        title="hello",
        message="world",
        type_="system",
        topic_key="topic",
        channel_key="in_app",
        cta_label=None,
        cta_url=None,
        meta=base_meta,
    )
    altered_hash = NotificationRepository._payload_hash(
        title="hello",
        message="world",
        type_="system",
        topic_key="topic",
        channel_key="in_app",
        cta_label=None,
        cta_url=None,
        meta={"a": 2},
    )
    assert base_hash != altered_hash
