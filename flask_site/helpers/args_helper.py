import sys


def read_env():

    args = sys.argv

    if 'nose' in args[0]:  # Detect nosetests
        return 'test'

    if len(args) == 1:
        return 'production'

    if sys.argv[1] == 'development' or sys.argv[1] == 'dev' or sys.argv[1] == 'debug':
        return 'development'

    if sys.argv[1] == 'production' or sys.argv[1] == 'prod':
        return 'production'

    return 'production'
