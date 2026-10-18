import logging

import pytest


@pytest.fixture(autouse=True)
def _clean_root_logger():
    yield
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()
