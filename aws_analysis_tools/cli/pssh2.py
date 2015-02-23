#!/usr/bin/env kaws-python
"""Parallel SSH to a list of nodes, returned from search-ec2-tags.py
(must be in your path).

Usage:
  pssh.py -h | --help
  pssh.py (--query=ec2_tag | --hosts=<hosts>) [--connect-timeout]
      [--timeout=<timeout>] [--concurrency=<concurrency>] [--force-line-buf]
      <command>

Options:
  -h --help                   show this help message and exit
  --query=<query>             the string to pass search-ec2-tags.py
  --hosts=<hosts>             comma-sep list of hosts to ssh to
  --connect-timeout           ssh ConnectTimeout option
  --concurrency=<N>           Number of ssh commands to run in parallel [default: 10]
                              (0 means run all at once)
  --force-line-buf            Use automatic line buffering magic on the server.
                              NOTE: This is known to cause issues with some commands,
                               such as apt-get. If you get hanging output or strange
                               IO errors, don't use this option for that command.
"""

import multiprocessing.pool
import sys
import traceback

from colorama import Fore
from docopt import docopt

from reversefold.util import ssh

### Nasty hack to get around the fact that search-ec2-tags has dashes in the name
from aws_analysis_tools.cli.search_ec2_tags import parse_query, search_tags


def _query(string):
    parsed_query, parsed_regions = parse_query(string)
    response = search_tags(parsed_query, passed_regions=parsed_regions)
    print 'Matched the following hosts: %s' % ', '.join(response)
    return response


def main():
    args = docopt(__doc__)

    command = args['<command>']
    query = args['--query']

    if args['--hosts'] and query:
        print Fore.RED + 'You can use only one of --query and --hosts' + Fore.RESET
        sys.exit(1)

    hosts = []
    if query:
        hosts = _query(query)
        if len(hosts) > 0 and hosts[0].startswith('Error'):
            print '%sSorry, search-ec2-tags.py returned an error:\n %s%s' % (
                Fore.RED, hosts, Fore.RESET)
            sys.exit(1)

    if args['--hosts']:
        hosts = [host.strip() for host in args['--hosts'].split(',')]

    if len(hosts) == 0:
        print Fore.RED + 'Sorry, search-ec2-tags.py returned zero results.' + Fore.RESET
        sys.exit(1)

    concurrency = int(args['--concurrency'])
    if concurrency == 0:
        concurrency = len(hosts)
    elif concurrency < 0:
        print Fore.RED + '--concurrency must be 0 or a positive integer' + Fore.RESET
        sys.exit(1)

    ppl = max(len(host) for host in hosts) + 3

    ### This creates a library that automatically makes stdout line-buffered to try to enforece the
    ### commands run to output a line to us as soon as one is ready. Since this library is injected
    ### through LD_PRELOAD it affects all commands run, including subcommands if the environment is
    ### passed through. If any command expects non-text output (such as when piping binary output)
    ### this may cause the command to hang or behave in strange ways. It's still handy, though, for
    ### long-running or output heavy commands for which you want to see output immediately.
    if args['--force-line-buf']:
        command = ('mkdir -p $HOME/lib; [ -e $HOME/lib/line-buffer.so ] '
                   '|| echo "__attribute__((constructor))void f(){setvbuf(stdout,NULL,_IOLBF,0);}"'
                   ' | gcc -s -include stdio.h -x c - -fPIC -shared -o "$HOME/lib/line-buffer.so";'
                   ' export LD_PRELOAD="$HOME/lib/line-buffer.so"; ' + command)

    def do_ssh(host):
        try:
            ssh.SSHHost(host, prefix_pad_length=ppl,
                        connect_timeout=int(args['--connect-timeout'])).run(command)
        except ssh.SSHException:
            traceback.print_exc()

    pool = multiprocessing.pool.ThreadPool(concurrency)
    pool.map(do_ssh, hosts)


if __name__ == '__main__':
    main()
