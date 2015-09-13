from tests.base_test import BaseTest
from flask_site.helpers import read_yaml
from nose.tools import raises, ok_
from flask_site.errors import ConfigNotFoundError


class YamlHelperTest(BaseTest):

    def test_read_yaml(self):
        path = 'flask_site/config/config.yml'
        config = read_yaml(path)

        ok_(isinstance(config, dict), msg='Returned object must be instance of dict')
        ok_(len(config.keys()) > 0, msg='Returned object must not be empty.')

    @raises(ConfigNotFoundError)
    def test_read_yaml_imaginary_file_should_raises_error(self):
        path = '/a/b/c/d/e/f/g/h/__i.yml'
        read_yaml(path)
