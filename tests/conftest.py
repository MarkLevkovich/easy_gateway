import pytest

from easy_gateway.router.router import Router


@pytest.fixture
def router():
    return Router()
