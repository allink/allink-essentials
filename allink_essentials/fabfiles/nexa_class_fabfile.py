import os
from importlib import import_module

from fabric.api import run, execute, env, cd, hide, prefix, local as run_local, require
from fabric.contrib import console
from fabric import utils
from fabric import state
from fabric.colors import magenta, red

__all__ = ('local', 'verbose', 'bootstrap', 'delete_pyc', 'create_virtualenv',
           'deploy', 'git_pull', 'update_requirements', 'compilemessages',
           'collectstatic', 'create_database', 'restart_webapp',
           'restart_celery', 'syncdb', 'migrate', 'setup_celery',
           'dump_database', 'dump_media', 'create_local_symlinks', 'env')

if "VIRTUAL_ENV" not in os.environ:
    raise Exception("$VIRTUAL_ENV not found.")

state.output['running'] = False
state.output['stdout'] = False


def _setup_path(name):
    import sys
    sys.path.insert(0, '.')
    settings = import_module('%s.settings_%s' % (env.project_python, name))
    env.django_settings = settings
    env.environment = name
    for key, value in settings.DEPLOYMENT.items():
        setattr(env, key, value)

    env.project_root = os.path.join(env.root, env.project)
    env.code_root = os.path.join(env.project_root, env.project_python)
    env.settings = '%(project)s.settings_%(environment)s' % env
    env.forward_agent = True
    env.is_local = False


def local():
    env.is_local = True
    import sys
    sys.path.insert(0, '.')
    settings = import_module('%s.settings_development' % env.project_python)
    env.django_settings = settings
    env.project_root = ''
    env.code_root = ''
    env.root = '.'
    env.environment = 'development'

env.deployments = ('production',)


def verbose():
    """enables running and stdout output"""
    state.output['running'] = True
    state.output['stdout'] = True

# ===============
# Public Commands
# ===============


def bootstrap():
    """ initialize remote host environment (virtualenv, deploy, update) """
    require('root', provided_by=env.deployments)

    print magenta("Cloning Repository")
    with cd(env.root):
        run("git clone %s" % env.git_repository)

    # some one time setup things
    with cd(env.project_root):
        if env.git_branch != 'master':
            run('git checkout %s' % (env.git_branch,))
        run('mkdir static')
        run('mkdir media')

    with cd(env.code_root):
        run('ln -sf settings_%s.py settings.py' % env.environment)

    # create virtualenv and install all the requirements
    execute('create_virtualenv')
    execute('update_requirements')
    execute('create_database')
    execute('syncdb')
    execute('migrate')

    print magenta("Load initial data")
    with cd(env.project_root), prefix('source env/bin/activate'):
        run('./manage.py loaddata allink_user.json')

    # only compile messages if locale folder is present
    if os.path.isdir('locale'):
        execute('compilemessages')

    execute('collectstatic')


def delete_pyc():
    print magenta("Delete *.pyc files")
    command = 'find . -name \*.pyc -print0 | xargs -0 rm'
    if env.is_local:
        run_local(command)
    else:
        with cd(env.project_root):
            run(command)


def create_virtualenv():
    """ setup virtualenv on remote host """
    require('project_root', provided_by=env.deployments)
    run('virtualenv --setuptools --prompt="(%s)" %s' % (env.project, os.path.join(env.project_root, 'env')))


def deploy():
    """ updates code base on remote host and restarts server process """
    if not env.is_stage:
        if not console.confirm(red('Are you sure you want to deploy production?', bold=True),
                               default=False):
            utils.abort('Production deployment aborted.')
    with cd(env.project_root):
        result = run('git status', quiet=True)
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


def git_pull():
    "Updates the repository."
    print magenta("Fetch newest version")
    with cd(env.code_root):
        run("git pull")


def update_requirements():
    """ update external dependencies on remote host """
    require('project_root', provided_by=('local',) + env.deployments)
    print magenta("Update requirements")
    if env.is_local:
        run_local('pip install --requirement REQUIREMENTS_LOCAL')
    else:
        with cd(env.project_root):
            with prefix('source env/bin/activate'):
                run('pip install -U pip')
                run('pip install --requirement REQUIREMENTS_SERVER')


def compilemessages():
    """compiles all translations"""
    print magenta("Compile messages")
    with cd(env.project_root):
        with prefix('source env/bin/activate'):
            run('./manage.py compilemessages')


def collectstatic():
    """runs collectstatic on the remote host"""
    print magenta("Collect static files")
    with cd(env.project_root), prefix('source env/bin/activate'):
        run('./manage.py collectstatic --noinput')


def create_database():
    database_name = env.django_settings.UNIQUE_PREFIX
    print magenta("Create database")
    if env.is_local:
        run_local('mysql --user=$MYSQL_USER -p$MYSQL_PASSWORD -e "CREATE DATABASE %s;"' % database_name)
    else:
        database = env.django_settings.UNIQUE_PREFIX
        run('mysql --user=$MYSQL_USER -p$MYSQL_PASSWORD -e "CREATE DATABASE db_%s;"' % database)


def restart_webapp():
    """ touch wsgi file to trigger reload """
    require('project_root', provided_by=env.deployments)
    print magenta("Restart webapp")
    with cd(env.project_root):
        run('touch apache.wsgi')


def restart_celery():
    """restarts the celery worker"""
    require('project_root', provided_by=env.deployments)
    print magenta("Restart celery")
    run('nine-supervisorctl restart %s' % env.celery_worker)


def syncdb():
    """runs syncdb on the remote host"""
    require('project_root', provided_by=env.deployments)
    print magenta("Syncronize database")
    with cd(env.project_root):
        with prefix('source env/bin/activate'):
            run('./manage.py syncdb --noinput')


def migrate():
    """migrates all apps on remote host"""
    require('project_root', provided_by=env.deployments)
    print magenta("Migrate database")
    with cd(env.project_root), prefix('source env/bin/activate'):
        run('./manage.py migrate')


def setup_celery():
    """create a rabbitmq vhost and user"""
    require('project_root', provided_by=env.deployments)
    run('sudo rabbitmqctl add_user %(rabbitmq_username)s %(rabbitmq_password)s' % env.django_settings.DEPLOYMENT)
    run('sudo rabbitmqctl add_vhost %(rabbitmq_vhost)s' % env.django_settings.DEPLOYMENT)
    run('sudo rabbitmqctl set_permissions -p %(rabbitmq_vhost)s %(rabbitmq_username)s ".*" ".*" ".*"' % env.django_settings.DEPLOYMENT)


# ==============
# Local Commands
# ==============

def dump_database():
    """ resets the local database to the database on the server """
    local_settings = import_module('%s.settings_development' % env.project_python)
    require('project_root', provided_by=env.deployments)
    if not console.confirm(red('Are you sure you want to replace the local database with the %s database data?'
                           % env.environment, bold=True), default=False):
        utils.abort('Reset local database aborted.')
    try:
        with hide('output'):
            run_local('mysql --user=$MYSQL_USER -p$MYSQL_PASSWORD -e "DROP DATABASE %s;"' % (local_settings.UNIQUE_PREFIX))
    except:
        pass
    with hide('output'):
        run_local('mysql --user=$MYSQL_USER -p$MYSQL_PASSWORD -e "CREATE DATABASE %s;"' % (local_settings.UNIQUE_PREFIX))
        run_local('ssh %s@%s "source ~/.profile; mysqldump -u \$MYSQL_USER -p\$MYSQL_PASSWORD db_%s | gzip" | gunzip | mysql -u $MYSQL_USER -p$MYSQL_PASSWORD %s' % (env.django_settings.DEPLOYMENT['user'], env.django_settings.DEPLOYMENT['hosts'][0], env.django_settings.UNIQUE_PREFIX, local_settings.UNIQUE_PREFIX))


def dump_media():
    """ Reset local media from remote host """
    require('project_root', provided_by=env.deployments)
    if not console.confirm(red('Are you sure you want to replace the local media with the %s media data?'
                               % env.environment, bold=True), default=False):
        utils.abort('Reset local media aborted.')
    remote_media = os.path.join(env.project_root, 'media',)
    local_media = os.path.join(os.getcwd(), 'media')
    run_local('rsync --delete --exclude=".gitignore" -rvaz %s@%s:%s/ %s' % (env.user, env.hosts[0], remote_media, local_media))


def create_local_symlinks():
    """creates the local symlinks to settings files and pre-commit hook"""
    if not os.path.isdir("media"):
        os.mkdir("media")
    if not os.path.islink("%s/settings.py" % env.project_python) and os.path.isfile("%s/settings_development.py" % env.project_python):
        os.symlink("settings_development.py", "%s/settings.py" % env.project_python)
    if not os.path.isfile(".git/hooks/pre-commit"):
        os.symlink("../../pre-commit", ".git/hooks/pre-commit")


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
