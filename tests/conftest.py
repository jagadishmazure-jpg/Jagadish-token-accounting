import pytest

from tokacct import tokenizers


@pytest.fixture(scope="session")
def bpe():
    return tokenizers.scratch_bpe()


@pytest.fixture(scope="session")
def o200k():
    return tokenizers.by_name("o200k_base").count


@pytest.fixture
def words_count():
    return lambda t: len(t.split())
