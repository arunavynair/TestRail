import time
from pprint import pprint

from summary.api_client import TestRailBuilder

if __name__ == '__main__':
    test_rail_builder = TestRailBuilder(base_url="https://arungnair.testrail.io/", user="arungn@hotmail.com",
                                        password="XXXX", file_name="summary.json")

    # TODO: Remove below tr..catch after testing completed - delete project before recreating
    try:
        r = test_rail_builder.get_project('NNVM-TESTBENCH')
        if r is not None:
            test_rail_builder.drop_project(r['id'])
    except r:
        pprint(r)

    # add project
    project_result = test_rail_builder.add_project("NNVM-TESTBENCH", "This is project - NNVM-TESTBENCH", 1)
    p_id = project_result['id']
    p_name = project_result['name']

    # add milestone
    milestone_result = test_rail_builder.add_milestone(project_id=p_id, name="rel26",
                                                       description="This is release 26 - milestone",
                                                       due_on=int(time.time()))
    milestone_id = milestone_result['id']

    # add suite
    suites_response = test_rail_builder.get_suites(p_id)
    suit_id = suites_response[0]['id']

    # add section
    section_result = test_rail_builder.add_section(project_id=p_id, suite_id=suit_id, name="automation")
    section_id = section_result['id']

    # add case under section
    case_details = test_rail_builder.add_cases(sect_id=section_id, milestone_id=milestone_id)
    # pprint(case_details)

    # add test run
    run_result = test_rail_builder.add_run(project_id=p_id, suite_id=1, name="NNVM-TESTBENCH-12",
                                           description="This is NNVM-TESTBENCH-12", milestone_id=milestone_id)
    run_id = run_result['id']

    # add test results for case
    test_rail_builder.add_results_for_cases(run_id=run_id, case_details=case_details)
