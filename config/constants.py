import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
TEST_SETS_PATH = PROJECT_ROOT / "test_sets"
OUTPUT_PATH = PROJECT_ROOT / "output"

# TestRail configuration
TESTRAIL_URL = os.getenv("TESTRAIL_URL", "https://COMPANY_NAME.testrail.io")
TESTRAIL_USER = os.getenv("TESTRAIL_USER", "eduardo@COMPANY_NAME.com")
TESTRAIL_PASSWORD = os.getenv("TESTRAIL_PASSWORD", "API_KEY")
TESTRAIL_PROJECT_ID = 4

TESTRAIL_MILESTONE_MAP = {
    'v2.0': 3,
    'v1.4': 1,
    'v1.6': 4,
    'v2.1': 5
}

TESTRAIL_PROJECT_MAP = {
    'project_name': 1,
}

# Test artifacts
LONG_JSON = OUTPUT_PATH / "long.json"
SHORT_JSON = OUTPUT_PATH / "short.json"
TEST_LOG = OUTPUT_PATH / "test.log"
VIEWS_JSON = OUTPUT_PATH / "views.json" 