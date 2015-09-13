import os
from StringIO import StringIO

from fabric.api import cd, put, local, sudo, task, run, require, prefix
from fabric.contrib.files import exists, append
from fabric.state import env
from fabric.utils import abort

from gitric.api import git_seed, git_reset, allow_dirty, force_push, swap_bluegreen

"""
env.hosts = ['HOST1', 'HOST2']  # cmd: fab -H HOST1,HOST2

# cmd: fab --set LIVE_SERVER_URL=example.com,NEXT_SERVER_URL=next.example.com
env.LIVE_SERVER_URL = 'example.com'
env.NEXT_SERVER_URL = 'next.example.com'
"""
env.user = 'admin'

# from http://strikeawe.com/blog/2011/08/install-nodejs-npm-and-less-non-interactively
CMD_INSTALL_NODE_AND_PACKAGES = """export skipclean=1
curl -sL https://deb.nodesource.com/setup_0.12 | sudo -E bash -
apt-get install -y nodejs
npm install -g less -g bower"""


def nginx(action):
    # pty=False, here's why: http://www.fabfile.org/faq.html#init-scripts-don-t-work
    sudo('/etc/init.d/nginx %s' % action, pty=False)


def install_requirements():
    """
    1. Install packages
    2. Install nodejs & npm packages (bower and less)
    3. Update pip
    4. Install virtualenv from pip

    NOTE: For Ubuntu Server: (untested)
        1. Add 'nodejs' to linux_packages
        2. Comment out sudo(CMD_INSTALL_NODE_PACKAGES)
        3. Add line: `sudo('export skipclean=1')`
        4. Add line: `sudo('npm install -g less -g bower')`
    """
    linux_packages = ['python', 'python-pip', 'nginx', 'git', 'curl']
    sudo('apt-get install -y ' + ' '.join(linux_packages))
    sudo(CMD_INSTALL_NODE_AND_PACKAGES)
    sudo('pip install --upgrade pip')
    sudo('pip install virtualenv')


def configure_nginx():
    """
    1. Remove default nginx config file
    2. Create new config file
    3. Setup new symbolic link
    4. Copy local config to remote config
    5. Make directories and empty config files for /live and /next config.
    6. Restart nginx
    """
    # End step 1
    nginx('start')
    sudo('rm -rf /etc/nginx/sites-enabled/default')
    sudo('touch /etc/nginx/sites-available/flask_site')
    sudo('ln -s /etc/nginx/sites-available/flask_site /etc/nginx/sites-enabled/flask_site')
    with cd('/etc/nginx/sites-available/'):
        with open(os.path.join('deploy', 'nginx.conf')) as f:  # Get local nginx config script
            put(StringIO(f.read() % env), './flask_site', use_sudo=True)
    # Step 5
    run('mkdir -p /home/%(user)s/blue-green/live/etc/' % env)
    run('mkdir -p /home/%(user)s/blue-green/next/etc/' % env)
    run('touch /home/%(user)s/blue-green/live/etc/nginx.conf' % env)
    run('touch /home/%(user)s/blue-green/next/etc/nginx.conf' % env)
    sudo('chown -R %(user)s:%(user)s /home/%(user)s/blue-green' % env)  # Shouldn't be necessary, but just in case.
    # End step 5
    nginx('restart')


def configure_flask():
    run('mkdir -p %(config_path)s' % env)
    with cd('%(config_path)s' % env):
        with open(os.path.join('flask_site', 'config', 'config.yml')) as f:  # Get local flask config.yml
            put(StringIO(f.read()), 'config.yml')


@task
def setup_machine():
    install_requirements()
    configure_nginx()
    configure_flask()


def init_bluegreen():  # Taken from gitric.api, but modified so it uses linux-style path separators
    require('bluegreen_root', 'bluegreen_ports')
    env.green_path = env.bluegreen_root + '/green'
    env.blue_path = env.bluegreen_root + '/blue'
    env.next_path_abs = env.bluegreen_root + '/next'
    env.live_path_abs = env.bluegreen_root + '/live'
    run('mkdir -p %(bluegreen_root)s %(blue_path)s %(green_path)s '
        '%(blue_path)s/etc %(green_path)s/etc' % env)
    if not exists(env.live_path_abs):
        run('ln -s %(blue_path)s %(live_path_abs)s' % env)
    if not exists(env.next_path_abs):
        run('ln -s %(green_path)s %(next_path_abs)s' % env)
    env.next_path = run('readlink -f %(next_path_abs)s' % env)
    env.live_path = run('readlink -f %(live_path_abs)s' % env)
    env.virtualenv_path = env.next_path + '/env'
    env.pidfile = env.next_path + '/etc/app.pid'
    env.nginx_conf = env.next_path + '/etc/nginx.conf'
    env.color = os.path.basename(env.next_path)
    env.bluegreen_port = env.bluegreen_ports.get(env.color)


@task
def prod():
    if 'TRAVIS' in env and env.TRAVIS and env.TRAVIS_BRANCH != 'master':
        abort("Don't deploy from Travis unless it's from the master branch.")
    env.virtualenv_path = 'env'
    env.bluegreen_root = '/home/%(user)s/blue-green' % env
    env.config_path = env.bluegreen_root + '/config'
    env.bluegreen_ports = {'blue': '8888', 'green': '8889'}
    init_bluegreen()


def launch():
    run('kill $(cat %(pidfile)s) || true' % env)
    run('rm -rf %(virtualenv_path)s' % env)  # Clear out old virtualenv for new one.
    run('virtualenv %(virtualenv_path)s' % env)
    put(StringIO('proxy_pass http://127.0.0.1:%(bluegreen_port)s/;' % env), env.nginx_conf)
    run('cp %(config_path)s/config.yml %(repo_path)s/flask_site/config/config.yml' % env)
    with prefix('. %(virtualenv_path)s/bin/activate' % env), cd('%(repo_path)s' % env):
        run('pip install -r requirements.txt')
        run('pip install --ignore-installed gunicorn')
        run('bower install')
        # pty=False for last command since pseudo-terminals can't spawn daemons
        run('gunicorn -D -b 127.0.0.1:%(bluegreen_port)s -p %(pidfile)s '
            '--access-logfile access.log --error-logfile error.log flask_site:app' % env, pty=False)


@task
def deploy(commit=None):
    if commit is None:
        commit = local('git rev-parse HEAD', capture=True)
    env.repo_path = env.next_path + '/repo'
    insert_public_key()  # Done so that git push can operate without asking for password
    git_seed(env.repo_path, commit)
    git_reset(env.repo_path, commit)
    launch()
    remove_public_key()  # Security reasons


@task
def deploy_from_travis():
    env.repo_path = env.next_path + '/repo'
    run('rm -rf %(repo_path)s' % env)
    run('mkdir %(repo_path)s' % env)
    archive_name = 'deploy.tgz'
    local_archive_path = pack(archive_name)  # Create tgz from local files
    put(local_archive_path, env.repo_path)  # Upload to deployment server
    with cd(env.repo_path):
        run('tar xzf %s' % archive_name)  # Untar them to /repo
    launch()


def pack(archive_name):
    """
    Method to package a directory for deployment, returns local path of archive.
    """
    archive_path = 'tmp/' + archive_name
    local('mkdir tmp')
    local('tar czf %s --exclude=tmp .' % archive_path)
    return archive_path


def insert_public_key():
    if 'SSH_PUB_KEY' in env:
        public_key = env.PUB_KEY
    elif 'SSH_PUB_KEY_FILE' in env:
        with open(env.SSH_PUB_KEY_FILE) as f:
            public_key = f.read()
    else:
        public_key = ''  # Will prompt for git pass on push.
    if not exists('~/.ssh/authorized_keys'):
        run('mkdir -p ~/.ssh/')
        run('touch ~/.ssh/authorized_keys')
        run('chmod 600 ~/.ssh/authorized_keys')
    run('cp -a ~/.ssh/authorized_keys ~/.ssh/authorized_keys.tmp')
    append('~/.ssh/authorized_keys', public_key)


def remove_public_key():
    run('mv ~/.ssh/authorized_keys.tmp ~/.ssh/authorized_keys')


@task
def cutover():
    swap_bluegreen()
    nginx('reload')
