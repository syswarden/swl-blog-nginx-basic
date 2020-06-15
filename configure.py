import os
import shutil
import argparse

# option definitions

class Option:
    def __init__(self, name):
        self.name = name
        self.help = help
        self.arg = '--{}'.format(name.replace('_','-'))
        self.replace = '{{{{{}}}}}'.format(name)

options = [
    Option('ssh_port'),
    Option('control_port'),
    Option('automate_ip'),
    Option('whitelist_ip'),
    Option('ssl_domain'),
    Option('site_domain'),
    Option('notify_email'),
    Option('cloudflare_email'),
    Option('cloudflare_apikey'),
]

# helper functions

def get_input_args():
    parser = argparse.ArgumentParser()
    for option in options:
        parser.add_argument(option.arg, required=True)
    return parser.parse_args()

def get_replace_args(args):
    rargs = dict()
    dargs = vars(args)
    for option in options:
        option_value = '' if dargs[option.name] is None else dargs[option.name]
        rargs[option.replace] = option_value
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

# setup variables

args = get_input_args()
rargs = get_replace_args(args)
basepath = os.path.dirname(os.path.realpath(__file__))
tmppath = os.path.join(basepath, 'templates')
genpath = os.path.join(basepath, 'generated')

# fail if no templates are found

if not os.path.exists(tmppath):
    raise Exception('template configs not found: {}'.format(tmppath))

# remove previous generated folder and clone templates

clone_source_path(tmppath, genpath)

# get the file paths for the cloned template files

filepaths = get_file_paths(genpath)

# replace the variables in the files

for filepath in filepaths:
    replace_in_file(filepath, rargs)
