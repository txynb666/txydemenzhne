"""Keep regression tests away from the user's live database."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))


@pytest.fixture(scope="session", autouse=True)
def isolated_database(tmp_path_factory):
    from app.core import config
    from app.repositories import admin_db, agent_trace, schema
    from app.services import tools
    patch = pytest.MonkeyPatch()
    path = tmp_path_factory.mktemp("database") / "clinic.db"
    for module in (config, admin_db, agent_trace, schema, tools):
        patch.setattr(module, "DB_PATH", str(path))
    schema.init_all()
    yield
    patch.undo()
