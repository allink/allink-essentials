import os
import sys
import random
from importlib import import_module

from fabric.api import run, execute, env, cd, prefix, local as run_local, require
from fabric.contrib import console
from fabric.contrib.files import append
from fabric import utils

if "VIRTUAL_ENV" not in os.environ:
    raise Exception("$VIRTUAL_ENV not found.")


def _setup_path(name):
    sys.path.insert(0, '.')
    settings = import_module('%s.settings_%s' % (env.project_python, name))
    env.django_settings = settings
    env.environment = name
    for key, value in settings.DEPLOYMENT.items():
        setattr(env, key, value)

    env.project_root = os.path.join(env.root, env.project)
    env.virtualenv_root = os.path.join(env.project_root, 'env')
    env.settings = '%(project)s.settings_%(environment)s' % env
    env.forward_agent = True
    env.is_local = False

# =================
# Local Environment
# =================


def local():
    sys.path.insert(0, '.')
    env.is_local = True
    env.root = os.path.dirname(__file__)
    settings = import_module('%s.settings_development' % env.project_python)
    env.django_settings = settings
    env.environment = 'development'

# ===============
# Public Commands
# ===============


def bootstrap():
    """ initialize remote host environment (virtualenv, deploy, update) """
    require('virtualenv_root', provided_by=env.deployments)

    with cd(env.root):
        run("git clone %s %s" % (env.git_repository, env.project))

    # add DJANGO_SETTINGS_MODULE to .env
    _add_to_dotenv('DJANGO_SETTINGS_MODULE', '%s.settings_%s' % (env.project_python, env.environment))

    # generate SECRET_KEY
    allowed_chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    secret_key = ''.join(random.choice(allowed_chars) for i in range(50)).replace('!', '\\!').replace('&', '\\&').replace('$', '\\$')
    _add_to_dotenv('SECRET_KEY', secret_key)

    # create virtualenv
    with cd(env.project_root):
        if env.git_branch != 'master':
            run('git checkout %s' % (env.git_branch,))
        run('virtualenv %s' % env.virtualenv_root)
        run('mkdir static/')
    execute('update_requirements')

    execute('create_database')

    execute('migrate')

    with cd(env.project_root), prefix('source env/bin/activate'):
        run('./manage.py loaddata allink_user.json')

    execute('_compilemessages')


def delete_pyc():
    if env.is_local:
        run_local('find . -name \*.pyc | xargs rm')
    else:
        with cd(env.project_root):
            run('find . -name \*.pyc | xargs rm')


def migrate():
    """migrates all apps on the remote host"""
    require('virtualenv_root', provided_by=env.deployments)
    with cd(env.project_root), prefix('source env/bin/activate'):
        run('./manage.py migrate --noinput')


def deploy():
    """ updates code base on remote host and restarts server process """
    if not env.is_stage:
        if not console.confirm('Are you sure you want to deploy production?',
                               default=False):
            utils.abort('Production deployment aborted.')
    execute('git_pull')
    execute('migrate')
    execute('compilemessages')
    execute('collectstatic')
    execute('restart_webapp')
    execute('restart_celery')

def git_pull():
    "Updates the repository."
    with cd(env.project_root):
        run("git pull")


def compilemessages():
    """compiles all translations"""
    with cd(env.project_root), prefix('source env/bin/activate'):
        run('./manage.py compilemessages')


def collectstatic():
    """runs collectstatic on the remote host"""
    with cd(env.project_root), prefix('source env/bin/activate'):
        run('./manage.py collectstatic --noinput')


def update_requirements():
    """ update external dependencies on remote host """
    require('root', provided_by=('local',) + env.deployments)
    if env.is_local:
        run_local('pip install --requirement REQUIREMENTS_LOCAL')
    else:
        with cd(env.project_root), prefix('source env/bin/activate'):
                run('pip install --requirement REQUIREMENTS_SERVER')


def create_database():
    database_name = env.django_settings.UNIQUE_PREFIX
    if env.is_local:
        run_local('psql -U $PGUSER -d postgres -c "CREATE DATABASE %s;"' % database_name)
    else:
        user = env.django_settings.UNIQUE_PREFIX
        database = env.django_settings.UNIQUE_PREFIX
        allowed_chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
        password = ''.join(random.choice(allowed_chars) for i in range(10))
        run ('psql -U $PGUSER -d postgres -c "CREATE USER %s WITH PASSWORD \'%s\';"' % (user, password))
        run('psql -U $PGUSER -d postgres -c "CREATE DATABASE %s;"' % database)
        run('psql -U $PGUSER -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE %s to %s;"' % (database, user))
        _add_to_dotenv('DATABASE_URL', 'postgres://%s:%s@localhost/%s' % (user, password, database))


def restart_webapp():
    """ touch wsgi file to trigger reload """
    require('virtualenv_root', provided_by=env.deployments)
    with cd(env.project_root):
        run('./startstop.sh restart gunicorn')


# evtl ersetzen durch setup celery -> monit config erstellen
def setup_celery():
    """create a rabbitmq vhost and user"""
    require('virtualenv_root', provided_by=env.deployments)
    run('sudo rabbitmqctl add_user %(rabbitmq_username)s %(rabbitmq_password)s' % env.django_settings.DEPLOYMENT)
    run('sudo rabbitmqctl add_vhost %(rabbitmq_vhost)s' % env.django_settings.DEPLOYMENT)
    run('sudo rabbitmqctl set_permissions -p %(rabbitmq_vhost)s %(rabbitmq_username)s ".*" ".*" ".*"' % env.django_settings.DEPLOYMENT)


def restart_celery():
    """restarts the celery worker"""
    require('virtualenv_root', provided_by=env.deployments)
    with cd(env.project_root):
        run('./startstop.sh restart celery')


# ================
# Private Commands
# ================
def _add_to_dotenv(key, value):
    if isinstance(value, str):
        value = '"%s"' % value
    append(os.path.join(env.project_root, '.env'), '%s=%s' % (key, value))


# ==============
# Local Commands
# ==============
def dump_database():
    local_settings = import_module('settings_development')
    require('virtualenv_root', provided_by=env.deployments)
    if not console.confirm('Are you sure you want to replace the local database with the %s database data?'
                           % env.environment, default=False):
        utils.abort('Reset local database aborted.')
    local('psql -U $PGUSER -d postgres -c "DROP DATABASE %s;"' % (local_settings.UNIQUE_PREFIX))
    local('psql -U $PGUSER -d postgres -c "CREATE DATABASE %s;"' % (local_settings.UNIQUE_PREFIX))
    local('ssh %s@%s "source ~/.profile; pg_dump -U \$PGUSER db_%s" | psql -U $PGUSER %s' % (env.django_settings.DEPLOYMENT['user'], env.django_settings.DEPLOYMENT['hosts'][0], env.django_settings.UNIQUE_PREFIX, local_settings.UNIQUE_PREFIX))


def dump_media():
    """ Reset local media from remote host """
    require('virtualenv_root', provided_by=env.deployments)
    if not console.confirm('Are you sure you want to replace the local media with the %s media data?'
                           % env.environment, default=False):
        utils.abort('Reset local media aborted.')
    remote_media = os.path.join(env.project_root, 'media',)
    local_media = os.path.join(os.getcwd(), 'media')
    run_local('rsync --delete --exclude=".gitignore" -rvaz %s@%s:%s/ %s' % (env.user, env.hosts[0], remote_media, local_media))


# sollte zb django>=1.6,<1.7 nicht zerstoeren
def freeze_requirements():
    with open("REQUIREMENTS") as file:
        for line in file:
            if line.lower().startswith('-e') or line.lower().startswith('http'):
                os.system("echo '" + line.rstrip() + "' >> REQUIREMENTS_frozen")
            else:
                pkg = line.rstrip().split('==')[0]
                os.system("pip freeze | grep -i ^" + pkg + "== >> REQUIREMENTS_frozen")
    os.system("mv REQUIREMENTS_frozen REQUIREMENTS")
