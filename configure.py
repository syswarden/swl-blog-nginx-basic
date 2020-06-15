import os
import shutil
import shlex
import argparse
import fileinput
import platform
import subprocess

# option definitions

class Option:
    def __init__(self, name, help, default, switch, replace):
        self.name = name
        self.help = help
        self.default = default
        self.switch = switch
        self.replace = replace
        self.arg_name = '--{}'.format(name.replace('_','-'))
        self.replace_name = '{{{{{}}}}}'.format(name)

options = [
    Option('ssh_port', '', '22', False, True),
    Option('control_port', '', '8040', False, True),
    Option('automate_ip', 'automate internal ip', '10.1.1.1', False, True),
    Option('whitelist_ip', 'external whitelist ip', '1.1.1.1', False, True),
    Option('ssl_domain', 'syswarden.com', 'syswarden.com', False, True),
    Option('site_domain', 'example.syswarden.com', 'example.syswarden.com', False, True),
    Option('notify_email', 'ssl cert notification', 'example@syswarden.com', False, True),
    Option('cloudflare_email', 'example@syswarden.com', 'example@syswarden.com', False, True),
    Option('cloudflare_apikey', 'aAbBcCdDeEfFgGhHiIjJkKlLmMnNoOpP', 'aAbBcCdDeEfFgGhHiIjJkKlLmMnNoOpP', False, True),
    Option('apply_all', 'applies everything, overrides any individual options', None, True, False),
    Option('apply_nginx', 'installs and configures nginx', None, True, False),
    Option('skip_dhparam', 'skips dhparam generation while applying nginx configs', None, None, False),
    Option('apply_iptables', 'applies persistent iptable configs and removes ufw', None, True, False),
    Option('apply_external_ssl', 'installs letsencrypt certbot and generates a wildcard certificate', None, True, False),
    Option('apply_internal_ssl', 'generates an internal certificate for the automate server', None, True, False)
]

aptenv = {
    'DEBIAN_FRONTEND':'noninteractive', 
    'ACCEPT_EULA':'Y'
}

# helper functions

def get_input_args():
    parser = argparse.ArgumentParser()
    for option in options:
        if option.switch:
            parser.add_argument(option.arg_name, help=option.help, action='store_true')
        else:
            parser.add_argument(option.arg_name, help=option.help, default=option.default)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--create-config', action='store_true')
    group.add_argument('--apply-config', action='store_true')
    return parser.parse_args()

def get_replace_args(args):
    rargs = dict()
    dargs = vars(args)
    for option in options:
        if option.replace:
            rargs[option.replace_name] = '' if dargs[option.name] is None else dargs[option.name]
    return rargs

def get_file_paths(srcpath):
    filepaths = list()
    for (dirpath, dirnames, filenames) in os.walk(srcpath):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            filepaths.append(filepath)
    return filepaths

def clone_source_path(srcpath, destpath):
    if not os.path.exists(srcpath):
        raise Exception('missing: {}'.format(srcpath))
    if os.path.exists(destpath):
        shutil.rmtree(destpath)
    shutil.copytree(srcpath, destpath)

def replace_in_file(filepath, kvp):
    filedata = None
    with open(filepath, 'r') as file:
        filedata = file.read()
    for key, value in kvp.items():
        filedata = filedata.replace(key, value)
    with open(filepath, 'w') as file:       
        file.write(filedata)

def shell_execute(command, env=None):
    cenv = os.environ
    if not env is None:
        cenv = { **os.environ, **env }
    cargs = shlex.split(command)
    subprocess.Popen(cargs, env=cenv)

# application functions

def apply_iptables(genpath):
    iptables_path = os.path.join(genpath, 'etc/iptables/')
    shell_execute('ufw reset --force')
    shell_execute('ufw disable')
    shell_execute('apt remove ufw -y', aptenv )
    shell_execute('apt install iptables-persistent -y', aptenv )
    shell_execute('rsync -rvi "{}" /etc/iptables/'.format(iptables_path))
    
def apply_external_ssl(genpath):
    print('apply_external_ssl')

def apply_internal_ssl(genpath):
    print('apply_internal_ssl')

def apply_nginx(genpath):
    print('apply_nginx')

# setup variables

args = get_input_args()
rargs = get_replace_args(args)
basepath = os.path.dirname(os.path.realpath(__file__))
tmppath = os.path.join(basepath, 'templates')
genpath = os.path.join(basepath, 'generated')

# config creation

if args.create_config:
    if not os.path.exists(tmppath):
        raise Exception('template configs not found: {}'.format(tmppath))
    clone_source_path(tmppath, genpath)
    filepaths = get_file_paths(genpath)
    for filepath in filepaths:
        replace_in_file(filepath, rargs)

# config application

if args.apply_config:
    if not platform.system() == 'Linux':
        raise Exception('this tool can only apply configs on ubuntu')
    if not os.path.exists(genpath):
        raise Exception('generated configs not found: {}'.format(genpath))
    if args.apply_iptables or args.apply_all:
        apply_iptables(genpath)
    if args.apply_external_ssl or args.apply_all:
        apply_external_ssl(genpath)
    if args.apply_internal_ssl or args.apply_all:
        apply_internal_ssl(genpath)
    if args.apply_nginx or args.apply_all:
        apply_nginx(genpath)
