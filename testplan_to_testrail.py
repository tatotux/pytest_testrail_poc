import os
import json
import docx
import re
from typing import Dict, List
from utils.testrail_client import RailClient
from docx.text.paragraph import Paragraph
from docx.document import Document
from docx.table import _Cell, Table
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl

GROUP_IDS = {
    "Business": 784,
    "Performance": 785,
    "Risk Management/Safety": 786,
    "Functional": 787,
    "Installation and Servicing": 788,
    "Labeling": 789
}

MILESTONE_MAP = {
    "1.4": 5,
    "1.6": 6,
    "2.0": 7,
    "2.1": 8
}

TEST_SET_MAP = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5,
    "F": 6, "G": 7, "H": 8, "I": 9, "J": 10,
    "K": 11, "L": 12, "M": 13, "N": 14, "O": 15
}

def find_docx_files() -> List[str]:
    """Find all .docx files in current directory and let user select one."""
    docx_files = [f for f in os.listdir('.') if f.endswith('.docx')]
    
    if not docx_files:
        print("No .docx files found in current directory")
        return None
        
    print("\nAvailable documents:")
    for idx, filename in enumerate(docx_files, 1):
        print(f"{idx}- {filename}")
        
    while True:
        try:
            selection = input("\nSelect document number to process: ")
            file_idx = int(selection) - 1
            if 0 <= file_idx < len(docx_files):
                return docx_files[file_idx]
            else:
                print(f"Please select a number between 1 and {len(docx_files)}")
        except ValueError:
            print("Please enter a valid number")

def extract_test_case_from_docx(doc_path: str, test_id: str, milestone_id: int) -> Dict:
    """
    Extract test case information from Word document.
    Args:
        doc_path: Path to the Word document
        test_id: Test case ID to extract
        milestone_id: ID of the milestone selected by user
    """
    doc = docx.Document(doc_path)
    test_cases = []
    test_case = []
    flag = False
    
    print(f"\nDebug: Processing test case {test_id}")
    
    for block in iter_block_items(doc):
        text = block.text.strip()
        
        if text.startswith("ANG-TCS-"):
            if flag:
                test_cases.append(test_case)
                test_case = []
                test_case.append(text)
            else:
                flag = True
                test_case.append(text)
        elif flag:
            test_case.append(text)
    
    if test_case:
        test_cases.append(test_case)
    
    # Debug: Imprimir todos los test cases encontrados
    print("\nDebug: Found test cases:")
    for i, tc in enumerate(test_cases):
        print(f"\nTest Case {i + 1}:")
        for j, line in enumerate(tc):
            print(f"[{j}] '{line}'")
    
    # Buscar el test case específico
    for test_case in test_cases:
        testrail_cm_id = test_case[0].split(" ")[0].strip()
        print(f"\nDebug: Comparing '{testrail_cm_id}' with '{test_id}'")
        
        if testrail_cm_id == test_id:
            print("\nDebug: Found matching test case. Content:")
            for i, line in enumerate(test_case):
                print(f"[{i}] '{line}'")
                
            try:
                # Extract title
                title_line = test_case[0]
                # Buscamos el texto después del ID y el guión
                title = title_line.split(" - ", 1)[1].strip() if " - " in title_line else title_line
                
                # Determine group from CM ID
                group_type = test_id.split("-")[2]  # BUS, PERF, etc.
                group_map = {
                    "BUS": "Business",
                    "PERF": "Performance",
                    "RMS": "Risk Management/Safety",
                    "FNCT": "Functional",
                    "IS": "Installation and Servicing",
                    "LBL": "Labeling"
                }
                section_id = GROUP_IDS[group_map[group_type]]
                
                # Encontrar los índices de las secciones
                sections = {
                    "summary": next(i for i, text in enumerate(test_case) if text == "Summary"),
                    "scenario": next(i for i, text in enumerate(test_case) if text == "Test Case Scenario"),
                    "acceptance": next(i for i, text in enumerate(test_case) if text == "Acceptance Criteria"),
                    "type": next(i for i, text in enumerate(test_case) if "Type of Testing" in text),
                    "parent": next(i for i, text in enumerate(test_case) if text == "Parent Requirements and Specifications")
                }
                
                # Process sections
                summary = test_case[sections["summary"] + 1:sections["scenario"]]
                summary = '\n'.join(map(str, [i for i in summary if i]))
                
                # Extract preconditions and steps
                scenario = test_case[sections["scenario"] + 1:sections["acceptance"]]
                preconds = []
                steps = []
                
                # Flag para saber si ya pasamos la línea "The operator follows the following steps:"
                found_operator_line = False
                
                for line in scenario:
                    line = line.strip()
                    if not line:
                        continue
                        
                    if "The operator follows the following steps:" in line:
                        found_operator_line = True
                        preconds.append(line)
                    elif not found_operator_line:
                        # Todo antes de "The operator follows..." va en preconds
                        preconds.append(line)
                    else:
                        # Todo después de "The operator follows..." va en steps
                        if any(keyword in line.lower() for keyword in ["use test set", "download"]):
                            preconds.append(line)
                        else:
                            steps.append(line)
                
                # Extract acceptance criteria
                acceptance = test_case[sections["acceptance"] + 1:sections["type"]]
                acceptance = [a for a in acceptance if a.strip()]
                
                # Extract testing type (extraer de la misma línea después de los dos puntos)
                type_line = test_case[sections["type"]]
                testing_type = type_line.split("Type of Testing:", 1)[1].strip() if "Type of Testing:" in type_line else type_line.split("Type of Testing", 1)[1].strip()
                
                # Extract parent requirements
                parent_reqs = test_case[sections["parent"] + 1:]
                
                valid_prefixes = ("ANG-PR-", "ANG-SRS-", "ANG-SDS-")
                filtered_reqs = [
                    req.strip() 
                    for req in parent_reqs 
                    if req.strip() and req.strip().startswith(valid_prefixes)
                ]
                parent_reqs = '\r\n'.join(filtered_reqs)
                
                # Create steps with matching expectations
                tc_steps = []
                for i, step in enumerate(steps):
                    if step.strip():  # Solo incluir pasos no vacíos
                        tc_steps.append({
                            "content": step,
                            "expected": acceptance[i] if i < len(acceptance) else "",
                            "additional_info": "",
                            "refs": ""
                        })
                
                # Extract test set from preconditions
                test_set_match = re.search(r"Test Set ([A-O])", '\n'.join(preconds))
                if test_set_match:
                    test_set_letter = test_set_match.group(1)
                    test_set_id = TEST_SET_MAP.get(test_set_letter)
                else:
                    print(f"Warning: Could not find test set in preconditions for {test_id}")
                    test_set_id = None

                return {
                    "title": title,
                    "section_id": section_id,
                    "template_id": 2,
                    "type_id": 3,
                    "priority_id": 2,
                    "milestone_id": milestone_id,
                    "custom_cm_id": test_id,
                    "custom_test_set": test_set_id,
                    "custom_summary": summary,
                    "custom_preconds": '\r\n'.join(preconds),
                    "custom_tc_steps": tc_steps,
                    "custom_testing_type": testing_type,
                    "custom_parent_requirements": parent_reqs
                }
            except Exception as e:
                print(f"Error processing test case {test_id}: {str(e)}")
                return None
    
    return None

def compare_and_prompt(doc_case: Dict, testrail_case: Dict = None) -> Dict:
    """Compare test cases and ask user for confirmation on differences."""
    # For existing test case comparison
    updates = {}
    
    required_fields = {
        "title",
        "section_id",
        "template_id",
        "type_id",
        "priority_id",
        "milestone_id",
        "custom_cm_id",
        "custom_test_set",
        "custom_summary",
        "custom_preconds",
        "custom_tc_steps",
        "custom_testing_type",
        "custom_parent_requirements"
    }
    
    for field in required_fields:
        if field in doc_case:
            updates[field] = doc_case[field]
        else:
            print(f"Warning: Required field '{field}' not found in document case")
    
    updates.update({
        "type_id": 3,
        "template_id": 2,
        "priority_id": 2,
        "section_id": doc_case["section_id"],
        "custom_cm_id": doc_case["custom_cm_id"]
    })
    
    if updates:
        print("\nProposed updates:")
        print(json.dumps(updates, indent=2))
        
        response = input("\nApply these updates to TestRail? (y/n): ").lower()
        if response == 'y':
            return updates
    else:
        print("\nNo differences found")
    
    return None

def update_testrail_case(client: RailClient, case_id: int, updates: Dict):
    """Update test case in TestRail using the API."""
    try:
        print(f"\nSending updates to TestRail for case {case_id}...")
        result = client.api.send_post(
            f'update_case/{case_id}',
            updates
        )
        if result:
            print(f"✅ Successfully updated case {case_id} in TestRail")
            for field in updates.keys():
                print(f"  - Updated: {field}")
        else:
            print(f"❌ Failed to update case {case_id}")
    except Exception as e:
        print(f"❌ Error updating case {case_id}: {str(e)}")
        raise

def select_milestone() -> int:
    """Let user select which milestone to update."""
    print("\nAvailable milestones:")
    for version, milestone_id in sorted(MILESTONE_MAP.items()):
        print(f"{version} (ID: {milestone_id})")
    
    while True:
        version = input("\nSelect milestone version (e.g., 2.0): ").strip()
        if version in MILESTONE_MAP:
            return MILESTONE_MAP[version]
        print("Invalid version. Please try again.")

def extract_test_set_id(text: str) -> int:
    """Extract test set ID from preconditions text."""
    import re
    match = re.search(r"Test Set ([A-O])", text)
    if match:
        test_set = match.group(1)
        return TEST_SET_MAP.get(test_set)
    return None

def extract_test_ids(doc: Document) -> List[str]:
    """
    Extract all test case IDs from the Word document.
    Returns a list of test case IDs (e.g., ['ANG-TCS-BUS-001', 'ANG-TCS-PERF-002']).
    """
    test_ids = []
    
    # Iterate through all blocks in the document
    for block in iter_block_items(doc):
        text = block.text.strip()
        # Look for lines that start with ANG-TCS-
        if text.startswith("ANG-TCS-"):
            # Extract just the ID part (first word in the line)
            test_id = text.split()[0].strip()
            if test_id not in test_ids:  # Avoid duplicates
                test_ids.append(test_id)
    
    if not test_ids:
        print("⚠️  No test case IDs found in document")
    else:
        print(f"Found {len(test_ids)} test cases")
    
    return test_ids

def main():
    # Initialize TestRail client
    client = RailClient()
    print("Connected to TestRail successfully")
    
    # Select milestone
    milestone_id = select_milestone()
    version = next(v for v, m in MILESTONE_MAP.items() if m == milestone_id)
    print(f"\nProcessing milestone: {version} (ID: {milestone_id})")
    
    # Find and select Word document
    selected_doc = find_docx_files()
    if not selected_doc:
        return
        
    print(f"\nProcessing document: {selected_doc}")
    
    # Get test cases from TestRail
    testrail_cases = client.get_cases(milestone_id=milestone_id)
    
    # Create a map of CM IDs to TestRail cases
    testrail_case_map = {case.custom_cm_id: case for case in testrail_cases}
    
    # Process test cases from Word
    doc = docx.Document(selected_doc)
    for test_id in extract_test_ids(doc):
        print(f"\nProcessing test case: {test_id}")
        
        # Extract test case from Word
        doc_case = extract_test_case_from_docx(selected_doc, test_id, milestone_id)
        if not doc_case:
            print(f"⚠️  Failed to extract test case {test_id} from Word document")
            continue
        
        # Get existing case or None if it's new
        testrail_case = testrail_case_map.get(test_id)
        
        # Compare and get updates
        updates = compare_and_prompt(doc_case, testrail_case)
        
        if updates:
            try:
                if testrail_case:
                    # Update existing case
                    update_testrail_case(client, testrail_case.id, updates)
                else:
                    # Create new case
                    section_id = doc_case['section_id']
                    result = client.api.send_post(f'add_case/{section_id}', updates)
                    print(f"✅ Successfully created new test case (ID: {result['id']})")
            except Exception as e:
                print(f"❌ Error updating TestRail: {str(e)}")
                if input("\nContinue with next test case? (y/n): ").lower() != 'y':
                    print("Stopping process...")
                    break
        
        if input("\nContinue to next test case? (y/n): ").lower() != 'y':
            print("Stopping process...")
            break

def iter_block_items(parent):
    """Iterate through all paragraphs and tables in document."""
    if isinstance(parent, Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise ValueError("Error reading block text")

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            table = Table(child, parent)
            for row in table.rows:
                for cell in row.cells:
                    yield from iter_block_items(cell)

if __name__ == "__main__":
    main()
