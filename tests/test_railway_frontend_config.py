from pathlib import Path
import tomllib


def test_frontend_railway_config_uses_frontend_dockerfile():
    repo_root = Path(__file__).resolve().parents[1]
    config_path = repo_root / "frontend" / "railway.toml"
    dockerfile_path = repo_root / "frontend" / "Dockerfile"

    config = tomllib.loads(config_path.read_text())

    assert dockerfile_path.exists()
    assert config["build"]["dockerfilePath"] == "/frontend/Dockerfile"
