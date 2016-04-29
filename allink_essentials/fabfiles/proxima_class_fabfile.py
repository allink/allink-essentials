# -*- coding: utf-8 -*-
import os
import random

from fabric.api import run, execute, env, cd, prefix, hide, local as run_local, require
from fabric.contrib import console
from fabric.contrib.files import append, exists
from fabric.colors import green, magenta, red, yellow
from fabric import state
from fabric import utils

if "VIRTUAL_ENV" not in os.environ:
    raise Exception("$VIRTUAL_ENV not found.")

state.output['running'] = False
state.output['stdout'] = False


def _setup_path():
    env.project_root = os.path.join(env.root, env.project)
    env.virtualenv_root = os.path.join(env.project_root, 'env')
    env.settings = '%(project)s.settings.%(environment)s' % env
    env.forward_agent = True
    env.is_local = False


def verbose():
    """enables running and stdout output"""
    state.output['running'] = True
    state.output['stdout'] = True

# ===============
# Public Commands
# ===============


def bootstrap():
    """ initialize remote host environment (virtualenv, deploy, update) """
    require('virtualenv_root', provided_by=env.deployments)

    print magenta("Cloning Repository")
    with cd(env.root):
        run("git clone %s %s" % (env.git_repository, env.project))

    print magenta("Create .env file")
    # add DJANGO_SETTINGS_MODULE to .env
    _add_to_dotenv('DJANGO_SETTINGS_MODULE', '%s.settings.%s' % (env.project_python, env.environment))

    # generate SECRET_KEY
    allowed_chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@$%^&*(-_=+)'
    secret_key = ''.join(random.choice(allowed_chars) for i in range(50)).replace('!', '\\!').replace('&', '\\&').replace('$', '\\$')
    _add_to_dotenv('SECRET_KEY', secret_key)

    # add cache to dotenv
    _add_to_dotenv('CACHE_URL', 'hiredis://127.0.0.1:6379/1/%s' % env.unique_identifier)
    _add_to_dotenv('SESSION_CACHE_URL', 'hiredis://127.0.0.1:6379/2/%s' % env.unique_identifier)

    # some one time setup things
    with cd(env.project_root):
        if env.git_branch != 'master':
            run('git checkout %s' % (env.git_branch,))
        run('mkdir static')
        run('mkdir media')
        run('mkdir tmp')

    # create virtualenv and install all the requirements
    execute('update_requirements')

    execute('create_database')

    execute('migrate')

    print magenta("Load initial data")
    with cd(env.project_root), prefix('source env/bin/activate'):
        run('./manage.py loaddata allink_user.json')

    # only compile messages if locale folder is present
    if os.path.isdir('locale'):
        execute('compilemessages')

    execute('update_js_requirements')
    execute('collectstatic')
    execute('create_monit_file')


def delete_pyc():
    print magenta("Delete *.pyc files")
    command = 'find . -name \*.pyc -print0 | xargs -0 rm'
    if env.is_local:
        run_local(command)
    else:
        with cd(env.project_root):
            run(command)


def migrate():
    """migrates all apps on the remote host"""
    require('virtualenv_root', provided_by=env.deployments)
    print magenta("Migrate database")
    with cd(env.project_root), prefix('source env/bin/activate'):
        run('./manage.py migrate --noinput')


def deploy():
    """ updates code base on remote host and restarts server process """
    if not env.is_stage:
        if not console.confirm(red('Are you sure you want to deploy production?', bold=True),
                               default=False):
            utils.abort('Production deployment aborted.')
    with cd(env.project_root):
        run('git status', quiet=True)
        result = run('git diff-index --name-only HEAD --', quiet=True)
    if result != '':
        utils.abort(red('There are local changes'))
        utils.abort('end')
    execute('git_pull')
    execute('update_requirements')
    execute('delete_pyc')
    execute('migrate')
    # only compile messages if locale folder is present
    if os.path.isdir(os.path.join(os.path.dirname(__file__), 'locale')):
        execute('compilemessages')
    execute('collectstatic')
    execute('restart_webapp')
    execute('restart_celery')


def dotenv(**kwargs):
    """ adds a key value pair to the .env file on a server """
    require('root', provided_by=env.deployments)
    if not len(kwargs):
        utils.abort('missing variable. usage: fab production dotenv:MYVAR=myvalue')
    for key, value in kwargs.items():
        _add_to_dotenv(key, value)


def create_monit_file():
    require('virtualenv_root', provided_by=env.deployments)
    print magenta("Create Monit File")
    with cd('/home/www-data/etc/monit.d/'):
        run('echo "check process %s_gunicorn with pidfile /home/www-data/projects/%s/tmp/gunicorn.pid" > %s_gunicorn' % (env.unique_identifier, env.project, env.unique_identifier))
        run('echo "\t#!/bin/sh" >> %s_gunicorn' % env.unique_identifier)
        run("echo '\t%s' >> %s_gunicorn" % ('start program = "/home/www-data/projects/%s/startstop.sh start gunicorn"' % env.project, env.unique_identifier))
        run("echo '\t%s' >> %s_gunicorn" % ('stop program = "/home/www-data/projects/%s/startstop.sh stop gunicorn"' % env.project, env.unique_identifier))
        run('echo "\t%s" >> %s_gunicorn' % ("if failed unixsocket /home/www-data/projects/%s/tmp/gunicorn.sock then restart" % env.project, env.unique_identifier))
        run('echo "\tif 5 restarts within 5 cycles then timeout" >> %s_gunicorn' % env.unique_identifier)
        run('echo "\tif totalmemory > 200.0 MB for 5 cycles then alert" >> %s_gunicorn' % env.unique_identifier)
        run('echo "\tif totalmemory > 210.0 MB for 10 cycles then restart" >> %s_gunicorn' % env.unique_identifier)
        run('echo "\tif totalcpu > 50%% for 5 cycles then alert" >> %s_gunicorn' % env.unique_identifier)
        run('echo "\tif totalcpu > 50%% for 10 cycles then restart" >> %s_gunicorn' % env.unique_identifier)
        run('monit reload')


def git_pull():
    "Updates the repository."
    print magenta("Fetch newest version")
    with cd(env.project_root):
        run("git pull")


def update_requirements():
    """update external dependencies on remote host """
    require('root', provided_by=('local',) + env.deployments)
    print magenta("Update requirements")
    if env.is_local:
        run_local('pip install --requirement REQUIREMENTS_LOCAL')
    else:
        _update_requirements_remote()


def compilemessages():
    """compiles all translations"""
    print magenta("Compile messages")
    if env.is_local:
        run_local('./manage.py compilemessages')
    else:
        with cd(env.project_root), prefix('source env/bin/activate'):
            run('./manage.py compilemessages')


def collectstatic():
    """runs collectstatic on the remote host"""
    print magenta("Collect static files")
    with cd(env.project_root), prefix('source env/bin/activate'):
        run('./manage.py collectstatic --noinput')


def _update_requirements_remote():
    with cd(env.project_root):
        result = run('sha1sum --check REQUIREMENTS.sha1', quiet=True)
        if result.return_code is 0:
            print green("No need to update virtualenv.")
            return
        print yellow("Need to create a new virtualenv")
        virtualenv_existed = exists('env')
        if virtualenv_existed:
            # virtualenv exists, build wheels for the new requirements
            with prefix('source env/bin/activate'):
                run('pip install -U pip')
                run('pip install wheel')
                run('pip wheel --requirement REQUIREMENTS_SERVER')
            run('rm -r env_old', quiet=True)
            run('mv env env_old')

        # create new virtualenv
        run('virtualenv env --prompt="(%s)"' % env.project)
        with prefix('source env/bin/activate'):
            run('pip install -U pip')
            run('pip install %s --requirement REQUIREMENTS_SERVER' % ('--no-index' if virtualenv_existed else '',))
        # create new hash file
        run('sha1sum --tag REQUIREMENTS REQUIREMENTS_SERVER > REQUIREMENTS.sha1')


def update_js_requirements():
    """ update external javascript dependencies on remote host """
    require('root', provided_by=('local',) + env.deployments)
    print magenta("Install javascript requirements")
    if env.is_local:
        run_local('npm install')
    else:
        with cd(env.project_root):
                run('npm install')


def create_database():
    database_name = env.unique_identifier
    print magenta("Create database")
    if env.is_local:
        run_local('psql -U $PGUSER -d postgres -c "CREATE DATABASE %s;"' % database_name)
    else:
        user = env.unique_identifier
        database = env.unique_identifier
        allowed_chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
        password = ''.join(random.choice(allowed_chars) for i in range(10))
        run('psql -U $PGUSER -d postgres -c "CREATE USER %s WITH PASSWORD \'%s\';"' % (user, password))
        run('psql -U $PGUSER -d postgres -c "CREATE DATABASE %s;"' % database)
        run('psql -U $PGUSER -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE %s to %s;"' % (database, user))
        run('psql -U $PGUSER -d postgres -c "GRANT %s to $PGUSER;"' % user)
        _add_to_dotenv('DATABASE_URL', 'postgres://%s:%s@localhost/%s' % (user, password, database))


def restart_webapp():
    """ touch wsgi file to trigger reload """
    require('virtualenv_root', provided_by=env.deployments)
    print magenta("Restart webapp")
    with cd(env.project_root):
        run('./startstop.sh restart gunicorn')


# evtl ersetzen durch setup celery -> monit config erstellen
def setup_celery():
    require('virtualenv_root', provided_by=env.deployments)
    user = env.unique_identifier
    vhost = env.unique_identifier
    allowed_chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    password = ''.join(random.choice(allowed_chars) for i in range(10))
    _add_to_dotenv('BROKER_URL', 'amqp://%s:%s@localhost:5672/%s' % (user, password, vhost))
    _add_to_dotenv('CELERY_RESULT_BACKEND', 'redis://localhost/0')

    print magenta("Create Monit File")
    with cd('/home/www-data/etc/monit.d/'):
        run('echo "check process %s_celery with pidfile /home/www-data/projects/%s/tmp/celery.pid" > %s_celery' % (env.unique_identifier, env.project, env.unique_identifier))
        run('echo "\t#!/bin/sh" >> %s_celery' % env.unique_identifier)
        run("echo '\t%s' >> %s_celery" % ('start program = "/home/www-data/projects/%s/startstop.sh start celery"' % env.project, env.unique_identifier))
        run("echo '\t%s' >> %s_celery" % ('stop program = "/home/www-data/projects/%s/startstop.sh stop celery"' % env.project, env.unique_identifier))
        run('echo "\tif 5 restarts within 5 cycles then timeout" >> %s_celery' % env.unique_identifier)
        run('echo "\tif totalmemory > 30000 kb for 5 cycles then alert" >> %s_celery' % env.unique_identifier)
        run('echo "\tif totalmemory > 210.0 MB for 10 cycles then restart" >> %s_celery' % env.unique_identifier)
        run('echo "\tif totalcpu > 50%% for 5 cycles then alert" >> %s_celery' % env.unique_identifier)
        run('echo "\tif totalcpu > 50%% for 10 cycles then restart" >> %s_celery' % env.unique_identifier)

    print yellow("Create a rabbitmq user and a rabbitmq vhost in Web GUI (Tip:Lastpass)")
    print yellow("username: %s" % user)
    print yellow("pw: %s" % password)
    print yellow("vhost: %s" % vhost)
    print yellow("Give user (%s) all permissions for vhost (%s)" % (user, vhost))
    print yellow("On server: monit reload")


def restart_celery():
    """restarts the celery worker"""
    require('virtualenv_root', provided_by=env.deployments)
    print magenta("Restart celery")
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
    require('virtualenv_root', provided_by=env.deployments)
    if not console.confirm(red('Are you sure you want to replace the local database with the %s database data?'
                           % env.environment, bold=True), default=False):
        utils.abort('Reset local database aborted.')
    save_ok_ret_codes = env.ok_ret_codes
    env.ok_ret_codes.append(1)
    with hide('output'):
        run_local('psql -U $PGUSER -d postgres -c "DROP DATABASE %s;"' % (env.project_python,))
    env.ok_ret_codes = save_ok_ret_codes
    run_local('psql -U $PGUSER -d postgres -c "CREATE DATABASE %s;"' % (env.project_python,))
    run_local('ssh %s@%s "source ~/.profile; pg_dump -U\$PGUSER --no-privileges --no-owner --no-reconnect %s | gzip" | gunzip |psql --quiet -U$PGUSER %s' % (env.user, env.hosts[0], env.unique_identifier, env.project_python))


def dump_media():
    """ Reset local media from remote host """
    require('virtualenv_root', provided_by=env.deployments)
    if not console.confirm(red('Are you sure you want to replace the local media with the %s media data?'
                               % env.environment, bold=True), default=False):
        utils.abort('Reset local media aborted.')
    remote_media = os.path.join(env.project_root, 'media',)
    local_media = os.path.join(os.getcwd(), 'media')
    run_local('rsync --delete --exclude=".gitignore" -rvaz %s@%s:%s/ %s' % (env.user, env.hosts[0], remote_media, local_media))


# sollte zb django>=1.6,<1.7 nicht zerstoeren
# def freeze_requirements():
#     with open("REQUIREMENTS") as file:
#         for line in file:
#             if line.lower().startswith('-e') or line.lower().startswith('http'):
#                 os.system("echo '" + line.rstrip() + "' >> REQUIREMENTS_frozen")
#             else:
#                 pkg = line.rstrip().split('==')[0]
#                 os.system("pip freeze | grep -i ^" + pkg + "== >> REQUIREMENTS_frozen")
#     os.system("mv REQUIREMENTS_frozen REQUIREMENTS")


def makemessages(**kwargs):
    """pulls out all strings marked for translation"""
    require('root', provided_by=('local',))
    if not env.is_local:
        utils.abort('runs on local env only. usage: fab local makemessages:lang=fr')
    if 'lang' in kwargs:
        utils.abort('missing language. usage: fab local makemessages:lang=fr')
    print magenta("Make messages")
    cmd = './manage.py makemessages --domain=%s --locale=%s --ignore=env/* --ignore=node_modules/*'
    run_local(cmd % ('django', kwargs['lang']))
    utils.puts('If you have javascript translations, don\'t forget to run:')
    utils.puts(cmd % ('djangojs', kwargs['lang']))
