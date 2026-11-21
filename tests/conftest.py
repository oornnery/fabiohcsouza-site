import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import ROOT, Settings
from app.main import create_app

P_ORIGIN = "http://portfolio.localhost:8000"
B_ORIGIN = "http://blog.localhost:8000"

# the real content/ plus the sample posts of tests/sample/: production ships no posts until there are real ones
CONTENT = Path(tempfile.mkdtemp(prefix="content-"))
shutil.copytree(ROOT / "content", CONTENT, dirs_exist_ok=True)
shutil.copytree(Path(__file__).parent / "sample", CONTENT, dirs_exist_ok=True)


def make_settings(**more) -> Settings:  # noqa: ANN003
    """Settings for a test: no .env (a developer's real keys never leak in), the test content, the blog linked."""
    return Settings.model_validate({"content_dir": CONTENT, "blog": True, **more})


@pytest.fixture
def settings(tmp_path) -> Settings:
    # _env_file=None: a developer's .env (real e-mail keys, DEMO_POSTS…) never leaks into the tests
    return make_settings(database_url=f"sqlite:///{tmp_path / 'test.sqlite'}", form_limit=5)


@pytest.fixture
def app(settings):
    return create_app(settings)


@pytest.fixture
def portfolio(app) -> TestClient:
    return TestClient(app, base_url=P_ORIGIN)


@pytest.fixture
def blog(app) -> TestClient:
    return TestClient(app, base_url=B_ORIGIN)


@pytest.fixture
def engine(app):
    return app.state.engine
