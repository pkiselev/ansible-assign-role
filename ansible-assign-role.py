#!/usr/bin/env python

# Ansible ad-hoc role assignment
# Most of the parts is just a copy/paste from:
# https://github.com/mikeputnam/misc/talks/ansible-talk/example_api_use_play.py
# http://docs.ansible.com/ansible/developing_api.html#python-api-2-0
#
# Some usefull info can be found at:
# https://serversforhackers.com/running-ansible-programmatically
# https://serversforhackers.com/running-ansible-2-programmatically
#
# Usage example: ansible-assign-role.py -i INVENTORY -u USER -b -kK [ROLE ...]


import logging
import argparse
import getpass
import os.path
from collections import namedtuple

from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory import Inventory
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.utils.display import Display
from ansible.plugins.callback.default import CallbackModule
from ansible.vars import VariableManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

Options = namedtuple('Options', [
    'connection',
    'module_path',
    'forks',
    'become',
    'become_method',
    'become_user',
    'check',
    'remote_user',
    'private_key_file',
    'ssh_common_args',
    'sftp_extra_args',
    'scp_extra_args',
    'ssh_extra_args',
    'verbosity',
])


def prepare_parser(parser):
    ''' Add all of the arguments needed to mimic usual ansible behavior '''
    user = getpass.getuser()
    parser.add_argument("-b", "--become",
                        help="run operations with become (nopasswd implied)",
                        action='store_true', default=False)
    parser.add_argument("--become-method",
                        help="privilege escalation method to use \
                              (default=sudo)",
                        dest="become_method",
                        choices=["sudo", "su", "pbrun", "pfexec", "runas"],
                        type=str,
                        default='sudo')
    parser.add_argument("--become-user",
                        help="run operations as this user (default=None)",
                        dest="become_user",
                        type=str,
                        default="root")
    parser.add_argument("-c", "--connection",
                        help="connection type to use (default=smart)",
                        type=str,
                        dest="connection",
                        required=False,
                        metavar="CONNECTION",
                        default="smart")
    parser.add_argument("-C", "--check",
                        help="don't make any changes",
                        action='store_true', default=False)
    parser.add_argument("-f", "--forks",
                        help="specify number of parallel processes to use",
                        metavar="FORKS", type=int, default=5)
    parser.add_argument("--private-key",
                        help="use this file to authenticate the connection \
                              default (smart)",
                        type=str,
                        dest="private_key_file",
                        required=False,
                        metavar="PRIVATE_KEY_FILE",
                        default=None)
    parser.add_argument("-i", "--inventory-file",
                        help="specify inventory host file",
                        type=str,
                        dest="inventory",
                        required=True, metavar="INVENTORY")
    parser.add_argument("-k", "--ask-pass",
                        dest="askpass",
                        help="ask for SSH password",
                        action='store_true')
    parser.add_argument("-K", "--ask-become-pass",
                        dest="ask_become_pass",
                        help="ask for privilege escalation password",
                        action='store_true')
    parser.add_argument("-M", "--module-path",
                        dest="module_path",
                        help="specify path(s) to module library (default=None)",
                        metavar="MODULE_PATH",
                        type=str, default="/usr/share/ansible")
    parser.add_argument("roles",
                        help="roles to apply",
                        nargs="+",
                        type=str)
    parser.add_argument("-u", "--user",
                        help="connect as this user (default=%s)" % user,
                        dest="remote_user",
                        required=False,
                        metavar="REMOTE_USER",
                        default=user)
    parser.add_argument("-v", "--verbose",
                        help="verbose mode (-vvv for more, -vvvv to enable"
                        "connection debugging)",
                        action='count', default=0)


def main():
    variable_manager = VariableManager()
    loader = DataLoader()
    passwd = None
    become_passwd = None
    display = Display()

    parser = argparse.ArgumentParser()
    prepare_parser(parser)
    args = parser.parse_args()
    if args.askpass:
        passwd = getpass.getpass("SSH password:")
    if args.ask_become_pass:
        become_passwd = getpass.getpass("BECOME password "
                                        "[defaults to SSH password]:")
        if become_passwd == "":
            become_passwd = passwd

    options = Options(
        connection=args.connection,
        module_path=args.module_path,
        forks=args.forks,
        become=args.become,
        become_method=args.become_method,
        become_user=args.become_user,
        check=args.check,
        remote_user=args.remote_user,
        private_key_file=args.private_key_file,
        ssh_common_args=None,
        sftp_extra_args=None,
        scp_extra_args=None,
        ssh_extra_args=None,
        verbosity=args.verbose
    )

    display.verbosity = args.verbose
    cb = CallbackModule(display)
    if not os.path.isfile(args.inventory):
        exit("ERROR! Can't open host list")

    inventory = Inventory(
        loader=loader,
        variable_manager=variable_manager,
        host_list=args.inventory
    )

    play_source = dict(
        name="Assign roles %s" % args.roles,
        hosts='all',
        gather_facts='no',
        roles=args.roles)

    variable_manager.set_inventory(inventory)
    play = Play().load(
        play_source,
        variable_manager=variable_manager,
        loader=loader
    )

    tqm = None
    try:
        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            options=options,
            passwords={'conn_pass': passwd, 'become_pass': become_passwd},
            stdout_callback=cb
        )
        tqm.run(play)
    finally:
        if tqm is not None:
            tqm.cleanup()


if __name__ == "__main__":
    main()
