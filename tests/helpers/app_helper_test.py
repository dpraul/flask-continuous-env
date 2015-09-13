from tests.base_test import BaseTest
from flask_site.helpers import create_app, create_routes, load_class, compile_assets, check_and_compile_bundle
from nose.tools import raises, ok_, eq_
from flask import Flask
from flask.ext.assets import Bundle
from flask_site.errors import ConfigNotFoundError, HTTPMethodNotImplementedError, ControllerNotFoundError


class AppHelperTest(BaseTest):

    def test_load_class_success(self):
        full_str = "flask_site.errors.BaseSiteError"

        cls = load_class(full_str)

        eq_(cls.__name__, 'BaseSiteError', msg="Class loader did not load class correctly.")

    @raises(AttributeError)
    def test_load_class_raises_attribute_error(self):
        full_str = "flask_site.errors.SomeClass"
        load_class(full_str)

    def test_create_app(self):
        app = create_app()
        ok_(isinstance(app, Flask), msg='The app must be a Flask instance')

    @raises(ConfigNotFoundError)
    def test_create_app_no_env_should_raises_error(self):
        create_app(env=None)

    @raises(ConfigNotFoundError)
    def test_create_app_no_config_should_raises_error(self):
        create_app(config=None)

    def test_create_routes(self):
        app = Flask(__name__)
        create_routes(app)

        count = 0
        for _ in app.url_map.iter_rules():  # Must be looped over, iterator doesn't have len()
            count += 1

        ok_(count > 1, msg='Routes are not implemented')

    @raises(ConfigNotFoundError)
    def test_create_routes_empty_should_raises_error(self):
        app = Flask(__name__)
        create_routes(app, app_routes=None)

    @raises(ControllerNotFoundError)
    def test_create_routes_empty_controller_should_raises_error(self):
        app = Flask(__name__)

        test_routes = {
            'error': {
                'uri': '/__error/',
                'methods': ['GET'],
                'controller': '_ERROR'
            }
        }

        create_routes(app, app_routes=test_routes)

    @raises(HTTPMethodNotImplementedError)
    def test_create_routes_with_unimplemented_http_method_should_raises_error(self):
        app = Flask(__name__)

        from flask_site.helpers import routes_config

        routes_config['index']['methods'].append('POST')

        create_routes(app, app_routes=routes_config)

    @raises(ConfigNotFoundError)
    def test_compile_assets_with_empty_config_should_raises_error(self):
        app = Flask(__name__)
        compile_assets(app=app, bundle_config=None)

    @raises(ValueError)
    def test_compile_assets_with_0_length_name_should_raises_error(self):
        check_and_compile_bundle(name='', settings=None)

    @raises(ValueError)
    def test_compile_assets_with_non_string_type_should_raises_error(self):
        check_and_compile_bundle('test', {
            'type': 4,
            'filters': None,
            'files': [
                'scripts/main.js'
            ]
        })

    @raises(ValueError)
    def test_compile_assets_with_0_length_type_should_raises_error(self):
        check_and_compile_bundle('test', {
            'type': '',
            'filters': None,
            'files': [
                'scripts/main.js'
            ]
        })

    @raises(ValueError)
    def test_compile_assets_with_no_files_should_raises_error(self):
        check_and_compile_bundle('test', {
            'type': 'js',
            'filters': None,
            'files': []
        })

    @raises(IOError)
    def test_compile_assets_with_bad_file_should_raises_error(self):
        check_and_compile_bundle('test', {
            'type': 'js',
            'filters': None,
            'files': [
                'scripts/main.js',
                'ERROR__'
            ]
        })

    def test_compile_assets_with_specified_output(self):
        bundle = check_and_compile_bundle('test', {
            'type': 'js',
            'output': 'x.out',
            'filters': None,
            'files': [
                'scripts/main.js'
            ]
        })

        ok_(isinstance(bundle, Bundle), msg='Must return an instance of Bundle')

    def test_compile_asset(self):
        bundle = check_and_compile_bundle('test', {
            'type': 'js',
            'filters': None,
            'files': [
                'scripts/main.js'
            ]
        })

        ok_(isinstance(bundle, Bundle), msg='Must return an instance of Bundle')
