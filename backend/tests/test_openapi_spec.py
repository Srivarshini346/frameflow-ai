import yaml
import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

def test_openapi_specification_matches():
    """
    Verifies that openapi.yaml is up-to-date and matches live /openapi.json schema.
    """
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200, "Failed to retrieve live /openapi.json"
    live_spec = response.json()

    yaml_path = Path(__file__).resolve().parent.parent.parent / "openapi.yaml"
    assert yaml_path.exists(), "openapi.yaml file must exist at project root"

    with open(yaml_path, "r", encoding="utf-8") as f:
        file_spec = yaml.safe_load(f)

    # Verify matching title, version, and paths
    assert file_spec["info"]["title"] == live_spec["info"]["title"], "OpenAPI titles do not match"
    assert file_spec["info"]["version"] == live_spec["info"]["version"], "OpenAPI versions do not match"

    live_paths = set(live_spec.get("paths", {}).keys())
    file_paths = set(file_spec.get("paths", {}).keys())
    missing_in_file = live_paths - file_paths
    assert not missing_in_file, f"openapi.yaml is missing live paths: {missing_in_file}"
