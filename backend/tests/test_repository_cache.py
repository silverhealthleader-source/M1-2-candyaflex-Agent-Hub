from copy import deepcopy
from types import SimpleNamespace

import pytest
from google.api_core.exceptions import ResourceExhausted

from app.database import Repository


class FakeDB:
    def __init__(self):
        self.rows = {"a": {"value": 2, "memo": "original"}}
        self.reads = 0
        self.writes = 0
        self.fail_read = False
        self.fail_write = False

    def collection(self, name):
        return self

    def stream(self, **kwargs):
        self.reads += 1
        if self.fail_read:
            raise ResourceExhausted("test quota")
        return [SimpleNamespace(id=key, to_dict=lambda row=row: deepcopy(row)) for key, row in self.rows.items()]

    def document(self, key):
        def set_value(value, merge=False, **kwargs):
            if self.fail_write:
                raise ResourceExhausted("test write quota")
            self.writes += 1
            self.rows[key] = {**(self.rows.get(key, {}) if merge else {}), **deepcopy(value)}
        return SimpleNamespace(set=set_value)


def fixture():
    time = [0]
    db = FakeDB()
    return db, Repository(db, cache_seconds=900, clock=lambda: time[0]), time


def test_repeated_reads_and_get_share_snapshot_without_mutation_leaks():
    db, repo, _ = fixture()
    first = repo.list("data")
    first[0]["value"] = 100
    assert repo.list("data")[0]["value"] == 2
    assert repo.get("data", "a")["value"] == 2 and repo.get("data", "missing") is None
    assert db.reads == 1


def test_writes_update_cached_crud_results_without_reloading_collection():
    db, repo, _ = fixture()
    repo.list("data")
    repo.save("data", "b", {"value": 3})
    repo.save("data", "a", {"value": 4}, merge=True)
    assert sum(x["value"] for x in repo.list("data")) == 7
    assert repo.get("data", "a")["memo"] == "original"
    repo.soft_delete("data", "b", "stamp")
    assert [x["id"] for x in repo.list("data")] == ["a"]
    assert db.rows["b"]["value"] == 3 and db.rows["b"]["deleted"] is True
    assert db.reads == 1 and db.writes == 3


def test_cache_expiry_observes_external_changes():
    db, repo, time = fixture()
    repo.list("data")
    db.rows["a"]["value"] = 5
    assert repo.list("data")[0]["value"] == 2
    time[0] = 901
    assert repo.list("data")[0]["value"] == 5 and db.reads == 2


def test_conversation_list_uses_shorter_cache():
    db, repo, time = fixture()
    repo.list("conversations")
    time[0] = 31
    repo.list("conversations")
    assert db.reads == 2


def test_failed_write_does_not_publish_unsaved_values_to_cache():
    db, repo, _ = fixture()
    repo.list("data")
    db.fail_write = True
    with pytest.raises(ResourceExhausted):
        repo.save("data", "a", {"value": 99}, merge=True)
    assert repo.get("data", "a")["value"] == 2


def test_quota_errors_pause_new_reads_and_are_not_cached_as_empty_results():
    db, repo, time = fixture()
    db.fail_read = True
    for _ in range(2):
        with pytest.raises(ResourceExhausted):
            repo.list("data")
    assert db.reads == 1
    db.fail_read = False
    time[0] = 61
    assert len(repo.list("data")) == 1 and db.reads == 2
