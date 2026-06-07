import os
import yaml

def test_github_actions_workflow_yaml():
    filepath = ".github/workflows/ci.yml"
    assert os.path.exists(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert data["name"] == "OpenSRE CI Pipeline"

def test_gitlab_ci_yaml():
    filepath = ".gitlab-ci.yml"
    assert os.path.exists(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert "stages" in data
