from flask import Flask

from flask.ext.assets import Environment, Bundle

from flask_site.helpers import read_yaml, read_env
from flask_site.errors import HTTPMethodNotImplementedError, ControllerNotFoundError, ConfigNotFoundError

import importlib
import os.path


main_config = read_yaml('flask_site/config/config.yml')
environment = main_config.get(read_env())
flask_config = environment.get('flask') if environment else None  # Get config for this environment, if it exists

routes_config = read_yaml('flask_site/config/routes.yml')
bundles_config = read_yaml('flask_site/config/bundles.yml')


def create_app(config=main_config, env=environment):
    if not config:
        raise ConfigNotFoundError('Config is not available')
    if not env:
        raise ConfigNotFoundError('Environment is not set')

    app = Flask(__name__,
                template_folder=os.path.abspath('templates'),
                static_folder=os.path.abspath('static'))
    
    app.config['DEBUG'] = flask_config.get('debug')
    app.config['ASSETS_DEBUG'] = app.config['DEBUG']

    app.config['SECRET_KEY'] = env['flask'].get('secret_key')
    app.config['ENV'] = env

    create_routes(app)
    compile_assets(app)

    return app


def check_and_compile_bundle(name, settings):
    if len(name) == 0:
        raise ValueError('The bundle name must have a length of more than 0')
    if not isinstance(settings['type'], str):
        raise ValueError('The "%s" bundle must have a string type associated with it' % name)
    if len(settings['type']) == 0:
        raise ValueError('The "%s" bundle type must have a type length of more than 0' % name)
    if len(settings['files']) == 0:
        raise ValueError('The "%s" bundle must have files associated with it' % name)

    # Check each file in bundle to make sure it exists.
    static_abs_path = os.path.abspath('static')
    for filename in settings['files']:
        if not os.path.isfile(os.path.join(static_abs_path, filename)):
            raise IOError('File "%s" in bundle "%s" does not exist.' % (filename, name))

    if settings['filters'] is None:
        filters = None
    else:
        filters = ','.join(settings['filters'])

    if 'output' in settings:
        output = settings['output']
    else:
        output = 'out/' + name + '.%(version)s' + '.' + settings['type']

    return Bundle(*settings['files'], filters=filters, output=output)


def compile_assets(app, bundle_config=bundles_config):
    if not bundle_config:
        raise ConfigNotFoundError('Bundles config is empty')
    assets = Environment(app)

    for name, settings in bundle_config.iteritems():
        bundle = check_and_compile_bundle(name, settings)
        assets.register(name, bundle)


def create_routes(app, app_routes=routes_config):
    if not app_routes:
        raise ConfigNotFoundError('Routes config is empty')

    # Loop over app_routes (probably from a yml file)
    for name, route in app_routes.iteritems():
        # Make sure the route has an associated controller
        try:
            loaded_mod = load_class('flask_site.controllers.%s' % route['controller'])
        except AttributeError:
            raise ControllerNotFoundError('Class %s is not found' % route['controller'])
        # Make sure that the controller implements methods for each defined in the config
        cls_methods = dir(loaded_mod)
        for method in route['methods']:
            method = method.lower()
            if method not in cls_methods:
                raise HTTPMethodNotImplementedError(
                    'Class %s is not implementing method %s' % (route['controller'], method.upper())
                )
        # Finally, add a url rule for this route
        app.add_url_rule(route['uri'],
                         view_func=loaded_mod.as_view('%s_controller' % route['controller']),
                         methods=route['methods'])


def load_class(full_class_string):
    class_data = full_class_string.split(".")
    module_path = ".".join(class_data[:-1])
    class_str = class_data[-1]

    module = importlib.import_module(module_path)
    return getattr(module, class_str)
