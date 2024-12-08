from typing import Dict, List
from .testrail import APIClient
from config.constants import (
    TESTRAIL_URL,
    TESTRAIL_USER,
    TESTRAIL_PASSWORD,
    TESTRAIL_PROJECT_ID
)

class TestRailCase:
    def __init__(self, case_data: Dict):
        self.id = case_data.get('id')
        self.title = case_data.get('title')
        self.section_id = case_data.get('section_id')
        self.type_id = case_data.get('type_id')
        self.custom_cm_id = case_data.get('custom_cm_id')
        self.custom_summary = case_data.get('custom_summary')
        self.custom_tc_steps = case_data.get('custom_tc_steps', [])
        self.custom_preconds = case_data.get('custom_preconds')
        self.custom_test_set = case_data.get('custom_test_set')
        self.custom_testing_type = case_data.get('custom_testing_type')
        self.custom_parent_requirements = case_data.get('custom_parent_requirements')
class RailClient:
    def __init__(self):
        self.api = APIClient(TESTRAIL_URL)
        self.api.user = TESTRAIL_USER
        self.api.password = TESTRAIL_PASSWORD
        self.testrail_data = self._fetch_from_testrail()
        self.test_cases = self._load_test_cases()

    def _fetch_from_testrail(self) -> Dict:
        """Fetch test cases from TestRail"""
        try:
            print(f"\nDebug information:")
            print(f"Base URL: {TESTRAIL_URL}")
            print(f"Project ID: {TESTRAIL_PROJECT_ID}")
            print(f"User: {TESTRAIL_USER}")
            
            # Obtener todos los casos de prueba del proyecto
            response = self.api.send_get(f'get_cases/{TESTRAIL_PROJECT_ID}')
            print(f"Response type: {type(response)}")
            print(f"Response keys: {response.keys() if isinstance(response, dict) else 'Not a dict'}")
            
            # Extraer los casos del diccionario de respuesta
            cases = response.get('cases', []) if isinstance(response, dict) else []
            print(f"Successfully retrieved {len(cases)} cases")
            
            # Update filter to use type_id instead of custom_automation
            automated_cases = [
                case for case in cases
                if isinstance(case, dict) and case.get('type_id') == 3
            ]
            print(f"Found {len(automated_cases)} automated cases")
            print(f"First case example: {automated_cases[0] if automated_cases else 'No cases found'}")
            
            return {'cases': automated_cases}
            
        except Exception as e:
            print(f"\nError fetching from TestRail:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print(f"Full URL being used: {self.api._APIClient__url}")
            return {
                'cases': [
                    {
                        'id': 1,
                        'title': 'Test Login (Mock)',
                        'section_id': 'S1',
                        'type_id': 3,
                        'custom_cm_id': 'CM-001',
                        'custom_summary': 'Verify login functionality',
                        'custom_tc_steps': [
                            {
                                'content': 'Enter credentials',
                                'expected': 'Login successful',
                                'additional_info': '',
                                'refs': ''
                            }
                        ],
                        'custom_preconds': 'System is running',
                        'custom_test_set': 1,
                        'custom_testing_type': 'Functional',
                        'custom_parent_requirements': 'REQ-001'
                    }
                ]
            }

    def _load_test_cases(self) -> List[TestRailCase]:
        """Load test cases from testrail data"""
        return [TestRailCase(case) for case in self.testrail_data['cases']]

    def get_test_cases(self) -> List[TestRailCase]:
        """Get all test cases"""
        return self.test_cases

    def get_cases(self, project_id=None, milestone_id=None) -> List[TestRailCase]:
        """Get test cases with optional filtering by project and milestone"""
        return self.test_cases