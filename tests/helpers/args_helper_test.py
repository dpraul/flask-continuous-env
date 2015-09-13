from tests.base_test import BaseTest
from flask_site.helpers import read_env
from nose.tools import eq_
import sys


class ArgHelperTest(BaseTest):

    def test_read_env_dev(self):
        old_argv = sys.argv

        sys.argv = ['./start.py', 'development']
        eq_(read_env(), 'development',
            msg='The command "start development" should return development env')

        sys.argv = ['./start.py', 'dev']
        eq_(read_env(), 'development',
            msg='The command "start dev" should return development env')

        sys.argv = ['./start.py', 'debug']
        eq_(read_env(), 'development',
            msg='The command "start debug" should return development env')

    def test_read_env_prod(self):
        old_argv = sys.argv

        sys.argv = ['./start.py', 'prod']
        eq_(read_env(), 'production',
            msg='The command "start prod" should return production env')

        sys.argv = ['./start.py', 'production']
        eq_(read_env(), 'production',
            msg='The command "start production" should return production env')

        sys.argv = ['./start.py']
        eq_(read_env(), 'production',
            msg='The command "start" should return production env')

        sys.argv = ['./start.py', 'waku']
        eq_(read_env(), 'production',
            msg='The command "start *" should return production env')
