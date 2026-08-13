def make_prompt(title="Prompt test", content="Contenu de test du prompt"):
    return {
        "title": title,
        "description": "Description courte",
        "content": content,
        "tags": ["python", "llm"],
    }


def test_create_prompt(client, auth_headers):
    resp = client.post("/api/v1/prompts", json=make_prompt(), headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Prompt test"
    assert data["tags"] == ["python", "llm"]
    assert data["vote_score"] == 0
    assert data["author"]["username"] == "tester"


def test_create_prompt_requires_auth(client):
    resp = client.post("/api/v1/prompts", json=make_prompt())
    assert resp.status_code == 401


def test_list_prompts_empty(client):
    resp = client.get("/api/v1/prompts")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_list_prompts_with_search(client, auth_headers):
    client.post("/api/v1/prompts", json=make_prompt(title="Calcul mental"), headers=auth_headers)
    client.post(
        "/api/v1/prompts",
        json=make_prompt(title="Traduction poétique", content="Translate"),
        headers=auth_headers,
    )
    resp = client.get("/api/v1/prompts", params={"search": "traduction"})
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["title"] == "Traduction poétique"


def test_vote_prompt(client, auth_headers):
    created = client.post("/api/v1/prompts", json=make_prompt(), headers=auth_headers).json()
    pid = created["id"]
    resp = client.post(f"/api/v1/prompts/{pid}/vote", json={"value": 1}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["vote_score"] == 1

    resp = client.post(f"/api/v1/prompts/{pid}/vote", json={"value": -1}, headers=auth_headers)
    assert resp.json()["vote_score"] == -1


def test_comment_prompt(client, auth_headers):
    created = client.post("/api/v1/prompts", json=make_prompt(), headers=auth_headers).json()
    pid = created["id"]
    resp = client.post(
        f"/api/v1/prompts/{pid}/comments",
        json={"content": "Très utile !"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["content"] == "Très utile !"

    comments = client.get(f"/api/v1/prompts/{pid}/comments").json()
    assert len(comments) == 1


def test_delete_prompt(client, auth_headers):
    created = client.post("/api/v1/prompts", json=make_prompt(), headers=auth_headers).json()
    resp = client.delete(f"/api/v1/prompts/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204
    resp = client.get(f"/api/v1/prompts/{created['id']}")
    assert resp.status_code == 404


def test_moderation_rejects_content(client, auth_headers):
    resp = client.post(
        "/api/v1/prompts",
        json=make_prompt(content="Ce contenu est idiot"),
        headers=auth_headers,
    )
    assert resp.status_code == 422
