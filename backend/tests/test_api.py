def test_create_location(client):
    res = client.post("/api/nodes", json={"level": "location", "name": "Test Loc", "parent_id": None})
    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "Test Loc"
    assert body["level"] == "location"
    assert body["parent_id"] is None


def test_create_subcategory_without_parent_rejected(client):
    res = client.post("/api/nodes", json={"level": "subcategory", "name": "Bad", "parent_id": None})
    assert res.status_code == 400


def test_create_child_with_wrong_parent_level_rejected(client):
    loc = client.post("/api/nodes", json={"level": "location", "name": "L1", "parent_id": None}).json()
    res = client.post("/api/nodes", json={"level": "category", "name": "C1", "parent_id": loc["id"]})
    assert res.status_code == 400


def test_full_hierarchy_and_tree(client):
    loc = client.post("/api/nodes", json={"level": "location", "name": "L1", "parent_id": None}).json()
    dept = client.post(
        "/api/nodes", json={"level": "department", "name": "D1", "parent_id": loc["id"]}
    ).json()
    cat = client.post(
        "/api/nodes", json={"level": "category", "name": "C1", "parent_id": dept["id"]}
    ).json()
    client.post("/api/nodes", json={"level": "subcategory", "name": "S1", "parent_id": cat["id"]})

    tree = client.get("/api/tree").json()
    assert len(tree) == 1
    assert tree[0]["name"] == "L1"
    assert tree[0]["children"][0]["name"] == "D1"
    assert tree[0]["children"][0]["children"][0]["name"] == "C1"
    assert tree[0]["children"][0]["children"][0]["children"][0]["name"] == "S1"


def test_update_node_name(client):
    loc = client.post("/api/nodes", json={"level": "location", "name": "Old", "parent_id": None}).json()
    res = client.put(f"/api/nodes/{loc['id']}", json={"name": "New"})
    assert res.status_code == 200
    assert res.json()["name"] == "New"


def test_update_missing_node_404(client):
    res = client.put("/api/nodes/9999", json={"name": "x"})
    assert res.status_code == 404


def test_delete_node_cascades(client):
    loc = client.post("/api/nodes", json={"level": "location", "name": "L1", "parent_id": None}).json()
    dept = client.post(
        "/api/nodes", json={"level": "department", "name": "D1", "parent_id": loc["id"]}
    ).json()

    res = client.delete(f"/api/nodes/{loc['id']}")
    assert res.status_code == 204

    assert client.get(f"/api/nodes/{loc['id']}").status_code == 404
    assert client.get(f"/api/nodes/{dept['id']}").status_code == 404


def test_delete_missing_node_404(client):
    res = client.delete("/api/nodes/9999")
    assert res.status_code == 404


def test_list_nodes_filter_by_level(client):
    client.post("/api/nodes", json={"level": "location", "name": "L1", "parent_id": None})
    client.post("/api/nodes", json={"level": "location", "name": "L2", "parent_id": None})
    res = client.get("/api/nodes", params={"level": "location"})
    names = {n["name"] for n in res.json()}
    assert names == {"L1", "L2"}
