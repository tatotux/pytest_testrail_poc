import pytest
import logging
from utils.testrail_client import RailClient

def pytest_configure(config):
    logging.basicConfig(level=logging.INFO)

@pytest.fixture(scope="session")
def testrail_client():
    return RailClient()
