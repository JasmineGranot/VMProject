import unittest
from unittest.mock import patch
from vm_flask_project.vm_project import app, setup_app
from pathlib import Path


class JsonLoadTestCase(unittest.TestCase):

    @patch('vm_flask_project.vm_project.logger.error')
    def test_fail_on_non_existing_json_file(self, mock_logger):
        try:
            setup_app(Path.cwd() / 'unexisting.json')
            self.fail()
        except FileNotFoundError:
            pass
        self.assertTrue(mock_logger.called)

    @patch('vm_flask_project.vm_project.logger.error')
    def test_pass_on_missing_attribute_in_json_file(self, mock_logger):
        try:
            setup_app(Path.cwd() / 'test_missing_data.json')
            self.fail()
        except ValueError:
            pass
        self.assertTrue(mock_logger.called)


class BasicTestCase(unittest.TestCase):
    def setUp(self):
        setup_app(Path.cwd() / 'test.json')

    def test_fail_on_non_existing_vm(self):
        tester = app.test_client(self)
        response = tester.get('/api/v1/attack?vm_id=vm-a211', content_type='html/text')
        self.assertEqual(response.status_code, 404)
        msg_expected = b"Error: Virtual machine with id vm-a211 was not found"
        self.assertEqual(response.data, msg_expected)

    def test_pass_get_attacker_vms(self):
        tester = app.test_client(self)
        response = tester.get('/api/v1/attack?vm_id=vm-a211de', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        expected = ["vm-c7bac01a07"]
        self.assertEqual(response.json, expected)

    def test_fail_attack_with_missing_vm_param(self):
        tester = app.test_client(self)
        response = tester.get('/api/v1/attack', content_type='html/text')
        self.assertEqual(response.status_code, 400)
        msg_expected = b"Error: No virtual machine id was provided. Please specify an vm_id."
        self.assertEqual(response.data, msg_expected)

    def test_pass_clean_stats(self):
        tester = app.test_client(self)
        response = tester.get('/api/v1/stats', content_type='html/text')
        expected = {"average_request_time": 0.0, "request_count": 0, "vm_count": 2}
        self.assertEqual(response.json, expected)

    def test_pass_stats_after_two_queries(self):
        tester = app.test_client(self)
        tester.get('/api/v1/attack?vm_id=vm-a211de', content_type='html/text')
        tester.get('/api/v1/stats', content_type='html/text')
        tester.get('/api/v1/attack?vm_id=vm-a211', content_type='html/text')
        response = tester.get('/api/v1/stats', content_type='html/text')
        expected = {"request_count": 3, "vm_count": 2}
        self.assertEqual(response.json.get('request_count', 0), expected['request_count'])
        self.assertEqual(response.json.get('vm_count', 0), expected['vm_count'])
        self.assertGreaterEqual(response.json.get('average_request_time', 0), 0.0)


if __name__ == '__main__':
    unittest.main()
