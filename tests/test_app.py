"""Functional tests: what the service is supposed to do."""


def test_health(anon):
    resp = anon.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_enrichment_changes_outcome(client, samples):
    bad = client.post("/ingest", json=samples["intel_match"]).get_json()
    clean = client.post("/ingest", json=samples["clean"]).get_json()

    assert "threat.indicator.matched" in bad["tags"]
    assert bad["risk_score"] > clean["risk_score"]
    assert bad["threat"]["indicator"]["ip"] == "203.0.113.66"

    assert "threat.indicator.matched" not in clean["tags"]
    assert "threat" not in clean
    assert clean["risk_score"] == 10


def test_normalized_shape(client, samples):
    doc = client.post("/ingest", json=samples["clean"]).get_json()
    assert doc["source"]["ip"] == "192.0.2.10"
    assert doc["destination"]["ip"] == "192.0.2.20"
    assert doc["user"]["name"] == "alice"
    assert doc["event"]["id"] >= 1


def test_rule_r001_positive_and_negative(client, samples):
    hit = client.post("/ingest", json=samples["r001_positive"]).get_json()
    miss = client.post("/ingest", json=samples["r001_negative"]).get_json()
    assert "rule:R-001" in hit["tags"]
    assert "rule:R-001" not in miss["tags"]


def test_rule_r002_positive_and_negative(client, samples):
    hit = client.post("/ingest", json=samples["r002_positive"]).get_json()
    miss = client.post("/ingest", json=samples["r002_negative"]).get_json()
    assert "rule:R-002" in hit["tags"]
    assert "rule:R-002" not in miss["tags"]


def test_search_by_user(client, samples):
    client.post("/ingest", json=samples["clean"])
    client.post("/ingest", json=samples["r001_positive"])
    results = client.get("/events/search?user=alice").get_json()["results"]
    assert len(results) == 1
    assert results[0]["user"]["name"] == "alice"


def test_report_download(client):
    resp = client.get("/reports/daily-summary.txt")
    assert resp.status_code == 200
    assert b"Sentinel-Lite summary" in resp.data


def test_intel_check(client):
    assert client.get("/intel/check?ip=198.51.100.23").get_json()["matched"] is True
    assert client.get("/intel/check?ip=192.0.2.10").get_json()["matched"] is False
    assert client.get("/intel/check?ip=not-an-ip").status_code == 400


def test_rules_reload(client):
    resp = client.post("/admin/rules/reload")
    assert resp.status_code == 200
    assert resp.get_json()["ids"] == ["R-001", "R-002"]


def test_invalid_json_rejected(client):
    resp = client.post("/ingest", data="{not json", content_type="application/json")
    assert resp.status_code == 400
