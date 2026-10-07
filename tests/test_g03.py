import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from ticket_app.analysis_provider import LocalAnalysisProvider, MockAnalysisProvider
from ticket_app.api import create_app

POLICY = json.loads(Path("scenarios/g03.json").read_text())
FIXTURES = json.loads(Path("fixtures/g03.json").read_text())
FORBIDDEN = ("approved", "paid", "sent", "completed", "granted")
GOOD = '{"summary":"Holiday request for review.","category":"leave","priority":"low","next_action":"Route to the leave team."}'


def client(tmp_path, provider):
    return TestClient(create_app(provider=provider, policy=POLICY, db_path=str(tmp_path / "t.db")))


def local(handler):
    return LocalAnalysisProvider("http://llm/v1", "m", 5, "", httpx.MockTransport(handler))


def reply(content):
    return lambda req: httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


def boom(req):
    raise httpx.ConnectTimeout("timeout")


@pytest.mark.parametrize("f", FIXTURES, ids=lambda f: f["subject"])
def test_mock_fixtures(tmp_path, f):
    r = client(tmp_path, MockAnalysisProvider()).post(
        "/api/analyze", json={"subject": f["subject"], "text": f["text"]}
    )
    body = r.json()
    assert r.status_code == 200
    assert body["analysis"]["category"] == f["expected_category"]
    assert body["analysis"]["priority"] == f["expected_priority"]
    assert body["requires_review"] is True
    text = (body["analysis"]["summary"] + body["analysis"]["next_action"]).lower()
    assert not any(w in text for w in FORBIDDEN)


@pytest.mark.parametrize("subject,text", [
    ("ab", "valid request text"), ("a" * 101, "valid request text"),
    ("Valid", "short"), ("Valid", "x" * 4001),
])
def test_invalid_input(tmp_path, subject, text):
    c = client(tmp_path, MockAnalysisProvider())
    assert c.post("/api/analyze", json={"subject": subject, "text": text}).status_code == 422


@pytest.mark.parametrize("handler,status", [
    (boom, 503),
    (reply("not json"), 502),
    (reply(GOOD.replace("leave", "benefits")), 502),
    (reply(GOOD.replace("low", "urgent")), 502),
])
def test_failures_are_controlled_and_not_saved(tmp_path, handler, status):
    c = client(tmp_path, local(handler))
    r = c.post("/api/analyze", json={"subject": "Holiday", "text": "I want to book a holiday."})
    assert r.status_code == status
    assert c.get("/api/history").json() == []


def test_valid_local_output_saved(tmp_path):
    c = client(tmp_path, local(reply(GOOD)))
    r = c.post("/api/analyze", json={"subject": "Holiday", "text": "I want to book a holiday."})
    assert r.status_code == 200 and r.json()["requires_review"] is True
    assert len(c.get("/api/history").json()) == 1

def test_request_has_token_limit_and_finite_timeout(tmp_path, monkeypatch):
    seen = {}

    def handler(req):
        seen["body"] = json.loads(req.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": GOOD}}]})

    provider = LocalAnalysisProvider("http://llm/v1", "m", 5, "", httpx.MockTransport(handler), 123)
    r = client(tmp_path, provider).post(
        "/api/analyze", json={"subject": "Holiday", "text": "I want to book a holiday."}
    )
    assert r.status_code == 200
    assert seen["body"]["max_tokens"] == 123
    assert provider.timeout == 5


def test_max_tokens_read_from_environment(tmp_path, monkeypatch):
    captured = {}

    class Spy(LocalAnalysisProvider):
        def __init__(self, *args, **kwargs):
            captured.update(kwargs)
            super().__init__(*args, **kwargs)

    monkeypatch.setenv("LLM_PROVIDER", "local")
    monkeypatch.setenv("LLM_MAX_TOKENS", "77")
    monkeypatch.setattr("ticket_app.api.LocalAnalysisProvider", Spy)
    create_app(policy=POLICY, db_path=str(tmp_path / "t.db"))
    assert captured["max_tokens"] == 77
