from utils.testrail_client import RailClient
from utils.test_case_generator import TestCaseGenerator

# Load test cases from TestRail Data
testrail_client = RailClient()
test_cases = testrail_client.get_test_cases()

# Generate test functions
test_functions = TestCaseGenerator.generate_test_module(test_cases)

# Add test functions to global namespace
globals().update(test_functions)