"""Test that CLI utilities function correctly."""
import pytest

from pacsanini.cli import utils


@pytest.mark.cli
def test_is_db_uri():
    """Test that database URIs are correctly picked up."""
    db_uris = [
        "postgresql://foo:bar@localhost/mydatabase",
        "postgresql+psycopg2://foo:bar@localhost/mydatabase",
        "postgresql+pg8000://foo:bar@localhost/mydatabase",
        "mysql://foo:bar@localhost/foo",
        "mysql+mysqldb://foo:bar@localhost/foo",
        "oracle://foo:bar@127.0.0.1:1521/mydb",
        "sqlite:///foo.db",
    ]
    for uri in db_uris:
        assert utils.is_db_uri(uri) is True

    non_db_uris = ["/data/foo/bar.json", "sqlite.csv"]
    for uri in non_db_uris:
        assert utils.is_db_uri(uri) is False
