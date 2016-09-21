import unittest
import httpretty
from json import loads
from datetime import datetime, timedelta
import server.tests.utils as test_utils
import server.web.utils as web_utils
import server.services.demos as demo_service
import server.services.users as user_service
from server.exceptions import ResourceDoesNotExistException

def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(CreateUserTestCase('test_user_create_success'))
    test_suite.addTest(CreateUserTestCase('test_user_create_invalid_inputs'))
    test_suite.addTest(UserLoginTestCase('test_user_login_success'))
    test_suite.addTest(UserLoginTestCase('test_user_login_invalid_inputs'))
    # test_suite.addTest(UserLogoutTestCase('test_user_logout_success'))
    # test_suite.addTest(UserLogoutTestCase('test_user_logout_invalid_token'))
    # test_suite.addTest(TokenizeTestCase('test_tokenize_and_detokenize'))
    return test_suite


###########################
#        Unit Tests       #
###########################

class CreateUserTestCase(unittest.TestCase):
    """Tests for `services/users.py - create_user()`."""

    def setUp(self):
        # Create demo
        test_utils.mock_with_file(httpretty.POST,
            "http://0.0.0.0:3000/api/v1/Demos",
            "server/tests/mocks/POST_api_v1_Demos_200.json", 200)

        test_utils.mock_with_file(httpretty.GET,
            "http://0.0.0.0:3000/api/v1/Demos/DemoGUID/retailers",
            "server/tests/mocks/GET_api_v1_Demos_DemoGUID_retailers_200.json", 200)

        self.demo = test_utils.create_demo()
        self.retailers = demo_service.get_demo_retailers(loads(self.demo).get('guid'))

    def test_user_create_success(self):
        """With correct values, is a valid user returned?"""
        # Create new user assigned to the first retailer
        test_utils.mock_with_file(httpretty.POST,
            "http://0.0.0.0:3000/api/v1/Demos/DemoGUID/createUser",
            "server/tests/mocks/POST_api_v1_Demos_DemoGUID_createUser_200.json", 200)

        user = user_service.create_user(loads(self.demo).get('guid'),
                                        loads(self.retailers)[0].get('id'))

        # TODO: Update to use assertIsInstance(a,b)
        # Check all expected object values are present
        user_json = loads(user)
        self.assertTrue(user_json.get('id'))
        self.assertTrue(user_json.get('demoId'))
        self.assertTrue(user_json.get('email'))
        self.assertTrue(user_json.get('username'))

    def test_user_create_invalid_inputs(self):
        """With invalid inputs, are correct errors thrown?"""

        # Attempt to create user with invalid inputs
        # Invalid demo guid
        test_utils.mock_with_file(httpretty.POST,
            "http://0.0.0.0:3000/api/v1/Demos/123321/createUser",
            "server/tests/mocks/POST_api_v1_Demos_123321_createUser_404.json", 404)
        self.assertRaises(ResourceDoesNotExistException,
                          user_service.create_user,
                          '123321', loads(self.retailers)[0].get('id'))
        # Invalid retailer id
        test_utils.mock_with_file(httpretty.POST,
            "http://0.0.0.0:3000/api/v1/Demos/DemoGUID/createUser",
            "server/tests/mocks/POST_api_v1_Demos_DemoGUID_createUser_404.json", 404)
        self.assertRaises(ResourceDoesNotExistException,
                          user_service.create_user,
                          loads(self.demo).get('guid'), '123321')

    def tearDown(self):
        test_utils.mock_with_file(httpretty.DELETE,
            "http://0.0.0.0:3000/api/v1/Demos/DemoGUID",
            "server/tests/mocks/DELETE_api_v1_Demos_DemoGUID_204.json", 204)
        test_utils.delete_demo(loads(self.demo).get('guid'))


class UserLoginTestCase(unittest.TestCase):
    """Tests for `services/users.py - login()`."""

    def setUp(self):
        # Create demo
        test_utils.mock_with_file(httpretty.POST,
            "http://0.0.0.0:3000/api/v1/Demos",
            "server/tests/mocks/POST_api_v1_Demos_200.json", 200)
        self.demo = test_utils.create_demo()

    def test_user_login_success(self):
        """With correct values, is a valid user logged in?"""

        # Log in user
        demo_json = loads(self.demo)
        test_utils.mock_with_file(httpretty.POST,
            "http://0.0.0.0:3000/api/v1/Demos/DemoGUID/loginAs",
            "server/tests/mocks/POST_api_v1_Demos_DemoGUID_loginAs_200.json", 200)
        auth_data = user_service.login(demo_json.get('guid'),
                                       demo_json.get('users')[0].get('id'))

        # TODO: Update to use assertIsInstance(a,b)
        # Check all expected object values are present
        self.assertTrue(auth_data.get('loopback_token'))
        self.assertTrue(auth_data.get('user'))

        user_json = auth_data.get('user')
        self.assertTrue(user_json.get('id'))
        self.assertTrue(user_json.get('demoId'))
        self.assertTrue(user_json.get('username'))
        self.assertTrue(user_json.get('email'))

        if user_json.get('roles'):
            for role_json in user_json.get('roles'):
                self.assertTrue(role_json.get('id'))
                self.assertTrue(role_json.get('name'))
                self.assertTrue(role_json.get('created'))
                self.assertTrue(role_json.get('modified'))

    def test_user_login_invalid_inputs(self):
        """With invalid inputs, are correct errors thrown?"""

        demo_json = loads(self.demo)
        test_utils.mock_with_file(httpretty.POST,
            "http://0.0.0.0:3000/api/v1/Demos/123321/loginAs",
            "server/tests/mocks/POST_api_v1_Demos_123321_loginAs_404.json", 404)
        self.assertRaises(ResourceDoesNotExistException,
                          user_service.login,
                          '123321', demo_json.get('users')[0].get('id'))
        test_utils.mock_with_file(httpretty.POST,
            "http://0.0.0.0:3000/api/v1/Demos/DemoGUID/loginAs",
            "server/tests/mocks/POST_api_v1_Demos_DemoGUID_loginAs_404.json", 404)
        self.assertRaises(ResourceDoesNotExistException,
                          user_service.login,
                          demo_json.get('guid'), '123321')

    def tearDown(self):
        test_utils.mock_with_file(httpretty.DELETE,
            "http://0.0.0.0:3000/api/v1/Demos/DemoGUID",
            "server/tests/mocks/DELETE_api_v1_Demos_DemoGUID_204.json", 204)
        test_utils.delete_demo(loads(self.demo).get('guid'))


class UserLogoutTestCase(unittest.TestCase):
    """Tests for `services/users.py - logout()`."""

    def setUp(self):
        # Create demo
        test_utils.mock_with_file(httpretty.POST,
            "http://0.0.0.0:3000/api/v1/Demos",
            "server/tests/mocks/POST_api_v1_Demos_200.json", 200)
        self.demo = test_utils.create_demo()
        demo_json = loads(self.demo)
        demo_guid = demo_json.get('guid')
        demo_user_id = demo_json.get('users')[0].get('id')

        # Log in user
        auth_data = user_service.login(demo_guid, demo_user_id)
        self.loopback_token = auth_data.get('loopback_token')

    def test_user_logout_success(self):
        """With correct values, is a valid user logged out?"""

        self.assertTrue(user_service.logout(self.loopback_token) is None)

    def test_user_logout_invalid_token(self):
        """With an invalid token, are correct errors thrown?"""

        self.assertRaises(ResourceDoesNotExistException,
                          user_service.logout,
                          test_utils.get_bad_token())

    def tearDown(self):
        test_utils.delete_demo(loads(self.demo).get('guid'))


class TokenizeTestCase(unittest.TestCase):
    """Tests for `services/users.py - get_token_for_user() and get_auth_from_token()`."""

    def test_tokenize_and_detokenize(self):
        """Is auth data correctly tokenized and later detokenized?"""

        # Create demo
        demo = test_utils.create_demo()
        demo_json = loads(demo)
        demo_guid = demo_json.get('guid')
        demo_user_id = demo_json.get('users')[0].get('id')

        # Log in user and tokenize auth data
        auth_data = user_service.login(demo_guid, demo_user_id)
        auth_data['exp'] = datetime.utcnow() + timedelta(days=14)
        token = web_utils.tokenize(auth_data)

        # Detokenize auth data
        decrypted_auth_data = web_utils.detokenize(token)

        # Check that decrypted data is equivalent to auth data
        self.assertTrue(auth_data.get('loopback_token') ==
                        decrypted_auth_data.get('loopback_token'))
        self.assertTrue(auth_data.get('exp') ==
                        decrypted_auth_data.get('exp'))
        self.assertTrue(auth_data.get('user').get('id') ==
                        decrypted_auth_data.get('user').get('id'))

        # Destroy demo
        test_utils.delete_demo(demo_guid)

if __name__ == '__main__':
    unittest.main()
