import os
import datetime
from importlib import import_module
import subprocess

from fabric import utils
from fabric.api import run, env, cd, prefix, local as run_local, require
from fabric.context_managers import lcd
from fabric.contrib import console
from fabric.operations import get

if "VIRTUAL_ENV" not in os.environ:
    raise Exception("$VIRTUAL_ENV not found.")


def _setup_path(name):
    import sys
    sys.path.insert(0, '.')
    settings = import_module('settings_%s' % name)
    env.django_settings = settings
    env.environment = name
    for key, value in settings.DEPLOYMENT.items():
        setattr(env, key, value)

    env.project_root = os.path.join(env.root, env.project)
    env.code_root = os.path.join(env.project_root, env.project_python)
    env.virtualenv_root = os.path.join(env.project_root, 'env')
    env.settings = 'settings_%(environment)s' % env
    env.forward_agent = True


def bootstrap():
    """ initialize remote host environment (virtualenv, deploy, update) """
    require('root', provided_by=('staging', 'production'))
    git_clone()
    git_checkout_branch()
    create_virtualenv()
    create_library_symlinks()
    update_requirements()
    create_symlinks()


def create_virtualenv():
    """ setup virtualenv on remote host """
    require('virtualenv_root', provided_by=('staging', 'production'))
    args = '--setuptools'
    run('virtualenv %s %s' % (args, env.virtualenv_root))


def git_pull():
    "Updates the repository."
    require('code_root', provided_by=('staging', 'production'))
    with cd(env.code_root):
        run("git pull")


def git_clone():
    "Updates the repository."
    require('root', provided_by=('staging', 'production'))
    with cd(env.root):
        run("git clone %s %s" % (env.git_repository, env.project))


def git_checkout_branch():
    "Checks out the correct branch."
    require('root', provided_by=('staging', 'production'))
    if env.git_branch != 'master':
        with cd(env.project_root):
            run('git checkout %s' % (env.git_branch,))


def git_reset():
    "Resets the repository to specified version."
    run("cd ~/git/$(repo)/; git reset --hard $(hash)")


def deploy():
    """ updates code base on remote host and restarts server process """
    if not env.is_stage:
        if not console.confirm('Are you sure you want to deploy production?',
                               default=False):
            utils.abort('Production deployment aborted.')
    git_pull()
    touch()


def deployfull():
    """ updates code base on remote host and restarts server process """
    if not env.is_stage:
        if not console.confirm('Are you sure you want to deploy production?',
                               default=False):
            utils.abort('Production deployment aborted.')
    git_pull()
    migrate()
    collectstatic()
    touch()


def update_requirements():
    """ update external dependencies on remote host """
    require('code_root', provided_by=('staging', 'production'))
    with cd(env.project_root):
        with prefix('source env/bin/activate'):
            run('pip install --requirement %s/REQUIREMENTS_SERVER' % env.project_python)


def manage(command):
    """runs manage.py <command> on the remote host"""
    require('code_root', provided_by=('staging', 'production'))
    with cd(env.code_root):
        with prefix('source ../env/bin/activate'):
            run('./manage.py %s' % (manage, command))


def syncdb():
    """runs syncdb on the remote host"""
    require('code_root', provided_by=('staging', 'production'))
    with cd(env.code_root):
        with prefix('source ../env/bin/activate'):
            run('./manage.py syncdb --noinput')


def migrate():
    """migrates all apps on the remote host"""
    require('code_root', provided_by=('staging', 'production'))
    with cd(env.code_root):
        with prefix('source ../env/bin/activate'):
            run('./manage.py migrate')


def compilemessages():
    """compiles all translations"""
    require('code_root', provided_by=('staging', 'production'))
    with cd(env.code_root):
        with prefix('source ../env/bin/activate'):
            run('./manage.py compilemessages')


def create_symlinks():
    """ create settings feincms and admin media links"""
    require('code_root', provided_by=('staging', 'production'))
    with cd(env.project_root):
        run('mkdir static/')
    with cd(env.code_root):
        run('ln -sf settings_%s.py settings.py' % env.environment)


def touch():
    """ touch wsgi file to trigger reload """
    require('code_root', provided_by=('staging', 'production'))
    with cd(env.project_root):
        run('touch apache.wsgi')


def collectstatic():
    """runs collectstatic on the remote host"""
    require('code_root', provided_by=('staging', 'production'))
    with cd(env.code_root):
        with prefix('source ../env/bin/activate'):
            run('./manage.py collectstatic --noinput')


def reset_local_database():
    """ resets the local database to the database on the server """
    require('code_root', provided_by=('staging', 'production'))
    if not console.confirm('Are you sure you want to replace the local database with the %s database data?'
                           % env.environment, default=False):
        utils.abort('Reset local database aborted.')
    filename = "tmp_dump%d_%d_%d.json" % datetime.datetime.now().isocalendar()
    require('code_root', provided_by=('staging', 'production'))
    server_data = os.path.join(env.project_root, filename)
    local_manage = os.path.join(os.getcwd(), 'manage.py')
    local_data = os.path.join(os.getcwd(), filename)
    with cd(env.code_root):
        with prefix('source ../env/bin/activate'):
            run('./manage.py dumpdata > %s' % (server_data,))
        get(server_data, local_data)
        run('rm %s' % server_data)
    with lcd(os.path.dirname(__file__)):
        run_local('%s sqlflush | %s dbshell' % (local_manage, local_manage))
        run_local('%s loaddata %s' % (local_manage, local_data,))
        run_local('rm %s' % local_data)


def reset_local_media():
    """ Reset local media from remote host """
    require('root', provided_by=('staging', 'production'))
    if not console.confirm('Are you sure you want to replace the local media with the %s media data?'
                           % env.environment, default=False):
        utils.abort('Reset local media aborted.')
    remote_media = os.path.join(env.code_root, 'media',)
    local_media = os.path.join(os.getcwd(), 'media/')
    run_local('rsync --delete --exclude=".gitignore" -rvaz %s@%s:%s/ %s' % (env.user, env.hosts[0], remote_media, local_media))


def create_local_symlinks():
    """creates the local symlinks to settings files and pre-commit hook"""
    if not os.path.isdir("media"):
        os.mkdir("media")
    if not os.path.islink("%s/settings.py" % env.project_python) and os.path.isfile("%s/settings_development.py" % env.project_python):
        os.symlink("settings_development.py", "%s/settings.py" % env.project_python)


def create_library_symlinks():
    """used on ubuntu servers to compile pil"""
    require('root', provided_by='production')
    with cd(env.project_root):
        for library in ('libfreetype.so', 'libjpeg.so', 'libz.so'):
            run("ln -s /usr/lib/`uname -i`-linux-gnu/%s env/lib/" % library)


def update_local_requirements():
    """installs local requirements"""
    subprocess.call(["pip", "install", "--requirement", "REQUIREMENTS_LOCAL"])


def freeze_requirements():
    with open("REQUIREMENTS") as file:
        for line in file:
            if line.lower().startswith('-e') or line.lower().startswith('http'):
                os.system("echo '" + line.rstrip() + "' >> REQUIREMENTS_frozen")
            else:
                pkg = line.rstrip().split('==')[0]
                os.system("pip freeze | grep -i ^" + pkg + "== >> REQUIREMENTS_frozen")
    os.system("mv REQUIREMENTS_frozen REQUIREMENTS")
