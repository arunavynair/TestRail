import base64
import json

import requests


class APIClient:
    def __init__(self, user, password, base_url):
        self.user = user
        self.password = password
        if not base_url.endswith('/'):
            base_url += '/'
        self.__url = base_url + 'index.php?/api/v2/'
        print(self.__url)

    def send_get(self, uri, filepath=None):
        """Issue a GET request (read) against the API.

        Args:
            uri: The API method to call including parameters, e.g. get_case/1.
            filepath: The path and file name for attachment download; used only
                for 'get_attachment/:attachment_id'.

        Returns:
            A dict containing the result of the request.
        """
        return self.__send_request('GET', uri, filepath)

    def send_post(self, uri, data):
        """Issue a POST request (write) against the API.

        Args:
            uri: The API method to call, including parameters, e.g. add_case/1.
            data: The data to submit as part of the request as a dict; strings
                must be UTF-8 encoded. If adding an attachment, must be the
                path to the file.

        Returns:
            A dict containing the result of the request.
        """
        return self.__send_request('POST', uri, data)

    def __send_request(self, method, uri, data):
        url = self.__url + uri

        auth = str(
            base64.b64encode(
                bytes('%s:%s' % (self.user, self.password), 'utf-8')
            ),
            'ascii'
        ).strip()
        headers = {'Authorization': 'Basic ' + auth}

        if method == 'POST':
            if uri[:14] == 'add_attachment':  # add_attachment API method
                files = {'attachment': (open(data, 'rb'))}
                response = requests.post(url, headers=headers, files=files)
                files['attachment'].close()
            else:
                headers['Content-Type'] = 'application/json'
                payload = bytes(json.dumps(data), 'utf-8')
                response = requests.post(url, headers=headers, data=payload)
        else:
            headers['Content-Type'] = 'application/json'
            response = requests.get(url, headers=headers)

        if response.status_code > 201:
            try:
                error = response.json()
            except:  # response.content not formatted as JSON
                error = str(response.content)
            raise APIError('TestRail API returned HTTP %s (%s)' % (response.status_code, error))
        else:
            if uri[:15] == 'get_attachment/':  # Expecting file, not JSON
                try:
                    open(data, 'wb').write(response.content)
                    return (data)
                except:
                    return ("Error saving attachment.")
            else:
                try:
                    return response.json()
                except:  # Nothing to return
                    return {}


class APIError(Exception):
    pass


class TestRailBuilder(object):
    def __init__(self, base_url, user, password, file_name):
        # f_path = abspath(file_name)
        with open(file_name, 'r') as f:
            self.message = json.load(f)
        self.client = APIClient(user=user, password=password, base_url=base_url)
        self.user = user
        self.password = password

    def get_suites(self, project_id):
        suites_uri = 'get_suites/{project_id}'.format(project_id=project_id)
        return self.client.send_get(uri=suites_uri)

    def get_project(self, project_name):
        projects_uri = 'get_projects'
        projects = self.client.send_get(uri=projects_uri)

        for project in projects:
            if project['name'] == project_name:
                return project
        return None

    def get_cases(self, project_id, sect_id=None):
        cases_uri = 'get_cases/{project_id}'.format(project_id=project_id)
        if sect_id:
            cases_uri = '{0}&section_id={section_id}'.format(cases_uri, section_id=sect_id)

        cases_resp = self.client.send_get(cases_uri)
        cases_details = {}
        for i in cases_resp:
            cases_details[i['id']] = i['title']
        return cases_details

    def add_project(self, name, announcement, suite_mode):
        add_project_uri = 'add_project'

        return self.client.send_post(add_project_uri,
                                     {'name': name, 'announcement': announcement, 'show_announcement': True,
                                      'suite_mode': suite_mode})

    def add_suite(self, project_id, name, description=None):
        return self.client.send_post('add_suite/{0}'.format(project_id), dict(name=name, description=description))

    def drop_project(self, project_id):
        project_uri = 'delete_project/{0}'.format(project_id)
        return self.client.send_post(project_uri, {})

    def add_milestone(self, project_id, name, description, due_on, parent_id=None, refs=None, start_on=None):
        add_project_uri = 'add_milestone/{0}'.format(project_id)

        return self.client.send_post(add_project_uri, {'name': name, 'description': description, 'due_on': due_on,
                                                       'parent_id': parent_id, 'refs': refs, 'start_on': start_on})

    def add_run(self, project_id, suite_id, name, description, milestone_id, assignedto_id=None, include_all=True,
                case_ids=None, refs=None):
        project_uri = 'add_run/{0}'.format(project_id)

        return self.client.send_post(project_uri, {'suite_id': suite_id, 'name': name, 'description': description,
                                                   'milestone_id': milestone_id, 'assignedto_id': assignedto_id,
                                                   'include_all': include_all, 'case_ids': case_ids, 'refs': refs})

    def add_section(self, project_id, suite_id, name, parent_id=None):
        return self.client.send_post('add_section/{0}'.format(project_id),
                                     dict(suite_id=suite_id, name=name, description=name, parent_id=parent_id))

    def add_cases(self, sect_id, milestone_id, template_id=None, type_id=None, ):
        project_uri = 'add_case/{0}'.format(sect_id)

        tests = self.message["tests"]

        cases_details = []
        if tests is not None:
            for test in tests.items():
                if test is not None:
                    test_id = test[0]
                    test_name = test[1]['name']
                    response = self.client.send_post(project_uri, dict(title='{0}'.format(test_name),
                                                                       template_id=template_id, refs=test_name,
                                                                       milestone_id=milestone_id, type_id=type_id))
                    res = {'case_id': response['id'], 'name': test_name, 'test_id': test_id}

                    cases_details.append(res)
        return cases_details

    def get_case_types(self):
        return self.client.send_get("get_case_types")

    def add_results_for_cases(self, case_details, run_id=None):
        """

        @type case_details: newly created case details
        """
        tests = self.message["tests"]
        response = []
        if tests is not None:
            for test in tests.items():
                if test is not None:
                    test_id = test[0]

                    # search for test_id and if found read the created case_id from add_case step
                    case_id = None
                    for case_detail in case_details:
                        if case_detail['test_id'] == test_id:
                            case_id = case_detail['case_id']

                    project_uri = 'add_result_for_case/{0}/{1}'.format(run_id, str(case_id))
                    test_details: dict = test[1]

                    run_status = 1 if test_details['result'] == 'PASS' else 5

                    # if error, get error details as well
                    test_details_error: dict = {}
                    if run_status == 5:
                        errors = self.message["errors"]
                        for k, v in errors.items():
                            test_ids = v['test-ids']
                            if test_id in test_ids:
                                test_details_error.update(v)

                    comment = {"results": test_details}
                    if len(test_details_error) > 0:
                        comment["errors"] = test_details_error

                    response.append(self.client.send_post(project_uri,
                                                          {'status_id': run_status,
                                                           'comment': "{0}".format(json.dumps(comment, indent=4))}))
            return response
