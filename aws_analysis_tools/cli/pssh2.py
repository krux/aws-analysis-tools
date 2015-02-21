#!/usr/bin/env kaws-python
"""Parallel SSH to a list of nodes, returned from search-ec2-tags.py
(must be in your path).

Usage:
  pssh.py -h | --help
  pssh.py (--query=ec2_tag | --hosts=<hosts>) [--no-color] [--keep-ssh-warnings]
      [--connect-timeout] [--timeout=<timeout>] [--chunk-size=<chunk-size>]
      [--no-line-buf] <command>

Options:
  -h --help                   show this help message and exit
  --query=<query>             the string to pass search-ec2-tags.py
  --hosts=<hosts>             comma-sep list of hosts to ssh to
  --no-color                  disable or enable color
  --keep-ssh-warnings         disable the removing of SSH warnings from stderr output
  --connect-timeout           ssh ConnectTimeout option
  --timeout=<timeout>         amount of time to wait, before killing the ssh
  --chunk-size=<chunk-size>   Number of ssh commands to run in parallel [default: 10]
                              (0 means run all at once)
  --no-line-buf               Do not use automatic line buffering magic
"""

import sys
import time
import select
import subprocess

from docopt import docopt
import greenhouse
import greenhouse.pool


### Nasty hack to get around the fact that search-ec2-tags has dashes in the name
from aws_analysis_tools.cli.search_ec2_tags import parse_query, search_tags


def chunked(iterable, chunk_size):
    out = []
    for item in iterable:
        out.append(item)
        if len(out) == chunk_size:
            yield out
            out = []
    if out:
        yield out


def hilite(string, args, color='white', bold=False):
    if args['--no-color']:
        return string

    attr = []
    if color == 'green':
        attr.append('32')  # green
    elif color == 'red':
        attr.append('41')  # red
    else:
        attr.append('37')  # white
    if bold:
        attr.append('1')
    return '\x1b[%sm%s\x1b[0m' % (';'.join(attr), string)


def remove_ssh_warnings(stderr, args):
    if args['--keep-ssh-warnings']:
        return stderr

    output = str(stderr).splitlines()
    if len(output) == 0:
        return None
    if len(output) == 1:
        return output[0]

    if stderr[0].startswith('@'):
        # 8 lines for a DNS spoofing warning
        if 'POSSIBLE DNS SPOOFING' in output[1]:
            output = output[8:]
        # 13 lines for a remote host identification changed warning
        if 'REMOTE HOST IDENTIFICATION' in output[1]:
            output = output[13:]
    if len(output) == 0:
        return None
    if len(output) == 1:
        return output[0]

    return '\n'.join(output)


def query(string):
    parsed_query, parsed_regions = parse_query(string)
    response = search_tags(parsed_query, passed_regions=parsed_regions)
    print 'Matched the following hosts: %s' % ', '.join(response)
    return response


def main():
    args = docopt(__doc__)

    procs = []
    command = args['<command>']
    query = args['--query']
    timeout = int(args['--timeout'])

    if args['--hosts'] and query:
        print hilite('You can use only one of --query and --hosts', args, 'red')
        sys.exit(1)

    hosts = []
    if query:
        hosts = query(query)
        if len(hosts) > 0 and hosts[0].startswith('Error'):
            print hilite('Sorry, search-ec2-tags.py returned an error:\n %s' % (hosts,),
                         args, 'red')
            sys.exit(1)

    if args['--hosts']:
        hosts = [host.strip() for host in args['--hosts'].split(',')]

    if len(hosts) == 0:
        print hilite('Sorry, search-ec2-tags.py returned zero results.', args, 'red')
        sys.exit(1)

    chunk_size = int(args['--chunk-size'])
    if chunk_size == 0:
        chunk_size = len(hosts)
    elif chunk_size < 0:
        print hilite('--chunk-size must be 0 or a positive integer', args, 'red')
        sys.exit(1)

    for chunk in chunked(hosts, chunk_size):
        for host in chunk:
            print host

    for host in hosts:
        proc = subprocess.Popen("ssh -oStrictHostKeyChecking=no -oConnectTimeout=%s %s '%s'" %
                                (args['--connect-timeout'], host, command), shell=True,
                                stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        procs.append(proc)

    index = 0
    ticks = 0
    too_long = False
    while 1:
        # nothing has returned, the first few secs, I bet.
        if ticks < 2:
            time.sleep(1)
        if ticks > 60:
            too_long = True

        host = hosts[index]
        proc = procs[index]

        # has it finished? go ahead and print the host and results.
        if not too_long and proc.poll() is not None:
            stdout, stderr = proc.communicate()
            print '[%s]' % hilite(host, args, bold=True)
            if stdout:
                print 'STDOUT: \n%s' % hilite(stdout, args, 'green', False)

            stderr = remove_ssh_warnings(stderr, args)
            if stderr and len(stderr) > 1:
                print 'STDERR: \n%s' % hilite(stderr, args, 'red', False)
            del procs[index]
            del hosts[index]

        elif not too_long and (ticks > 1) and (ticks % 5 == 0):
            # only print 'waiting still..' every 5 sec.
            print 'waiting on these hosts, still: %s' % ', '.join(hosts)
            time.sleep(1)

        if too_long:
            # it has been too long. print stdout/stderr one line at a time, so people
            # know what's happening, and aren't left waiting for timeout (and
            # then they never see stdout/stderr).
            print '%s (responding slowly - here is the output so far)' % \
                hilite('[' + host + ']', args, bold=True)

            while 1:
                if proc.poll() is not None:
                    break

                if select.select([proc.stdout], [], [], 0)[0]:
                    print 'STDOUT: \n'
                while select.select([proc.stdout], [], [], 0)[0]:
                    stdout = proc.stdout.readline()
                    sys.stdout.write(hilite(stdout, args, 'green', False))

                while select.select([proc.stderr], [], [], 0)[0]:
                    stderr = remove_ssh_warnings(proc.stderr.readline(), args)
                    if stderr is None:
                        break
                    print 'STDERR: \n'
                    sys.stdout.write(hilite(stderr, args, 'red', False))

                if ticks > timeout:
                    break
                elif proc.poll() is not None:
                    break
                else:
                    time.sleep(1)

            # one final time, to flush buffers, if the call won't block (process has exited)
            if proc.poll() is not None:
                stdout = '\n'.join(proc.stdout.readlines())
                if stdout:
                    print 'STDOUT: \n%s' % hilite(stdout, args,
                                                  'green', False)
                stderr = '\n'.join(proc.stderr.readlines())
                if stderr:
                    print 'STDERR: \n%s' % hilite(stderr, args,
                                                  'red', False)

            # remove from queue
            if proc.poll() is not None:
                del procs[index]
                del hosts[index]

        ticks += 1

        if len(procs) > index + 1:
            index += 1
        elif len(procs) == 0:
            break
        else:
            index = 0

        if ticks > timeout:
            [bad.terminate() for bad in procs]
            print hilite('\nSorry, the following hosts took too long, and I gave up: %s\n'
                         % ','.join(hosts), args, 'red')
            break


if __name__ == '__main__':
    main()
