from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.memory import GCSResearchMemory, MemoryCorruptionError, MemoryNotFoundError
from tests.test_memory import _completed_record


class FakeNotFound(Exception):
    code = 404


class FakeBlob:
    def __init__(self, name: str, objects: dict[str, bytes]) -> None:
        self.name = name
        self._objects = objects
        self.upload_kwargs: dict[str, object] = {}

    def upload_from_string(self, payload: bytes, **kwargs: object) -> None:
        self.upload_kwargs = kwargs
        if self.name in self._objects and kwargs.get("if_generation_match") == 0:
            raise RuntimeError("precondition failed")
        self._objects[self.name] = payload

    def download_as_bytes(self) -> bytes:
        if self.name not in self._objects:
            raise FakeNotFound()
        return self._objects[self.name]


class FakeBucket:
    def __init__(self, objects: dict[str, bytes]) -> None:
        self.objects = objects
        self.blobs: dict[str, FakeBlob] = {}

    def blob(self, name: str) -> FakeBlob:
        blob = self.blobs.setdefault(name, FakeBlob(name, self.objects))
        return blob


class FakeGCSClient:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.fake_bucket = FakeBucket(self.objects)

    def bucket(self, name: str) -> FakeBucket:
        return self.fake_bucket

    def list_blobs(self, name: str, prefix: str):
        return [FakeBlob(key, self.objects) for key in sorted(self.objects) if key.startswith(prefix)]


def test_gcs_save_load_list_and_safe_object_name() -> None:
    client = FakeGCSClient()
    repository = GCSResearchMemory("deeptrace-test", client=client)
    record = _completed_record()

    asyncio.run(repository.save(record))
    loaded = asyncio.run(repository.get(record.session_id))
    history = asyncio.run(repository.list_recent())
    object_name = repository.object_name(record.session_id)

    assert object_name == f"research-sessions/{record.session_id}.json"
    assert loaded == record
    assert [item.session_id for item in history] == [record.session_id]
    assert client.fake_bucket.blobs[object_name].upload_kwargs == {
        "content_type": "application/json",
        "if_generation_match": 0,
    }


def test_gcs_malformed_missing_and_provider_errors() -> None:
    client = FakeGCSClient()
    repository = GCSResearchMemory("deeptrace-test", client=client)
    missing_id = str(uuid4())
    with pytest.raises(MemoryNotFoundError):
        asyncio.run(repository.get(missing_id))

    corrupt_id = str(uuid4())
    client.objects[repository.object_name(corrupt_id)] = b"not-json"
    with pytest.raises(MemoryCorruptionError):
        asyncio.run(repository.get(corrupt_id))
    assert asyncio.run(repository.list_recent()) == []

    record = _completed_record()
    asyncio.run(repository.save(record))
    with pytest.raises(RuntimeError, match="precondition"):
        asyncio.run(repository.save(record))
