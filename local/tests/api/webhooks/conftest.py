import pytest


@pytest.fixture()
def prepare_test():
    """Override root conftest's prepare_test — no DB operations needed."""

    async def prepare():
        pass

    return prepare


@pytest.fixture()
def teardown_test():
    """Override root conftest's teardown_test — no DB operations needed."""

    async def teardown():
        pass

    return teardown


@pytest.fixture(autouse=True)
async def process_test(prepare_test, teardown_test):
    """Override root conftest's autouse process_test to skip DB setup/teardown."""
    await prepare_test()
    yield
    await teardown_test()
