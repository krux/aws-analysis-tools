#!/usr/bin/env python
"""
Usage:
    test_provision.py -h | --help
    test_provision.py <ubuntu_codename>

Options:
    -h --help          show this help message and exit
    <ubuntu_codename>  lucid or trusty
"""
import logging
import os
import subprocess
import sys
import time

import boto.ec2
from docopt import docopt
from reversefold.util import multiproc


FINISHED_STATUSES = ['bootstrap_complete', 'bootstrap_failed']
TIMEOUT = 30 * 60  # 30 minutes

AMIS = {
    'lucid':  'ami-3662265e',
    'trusty': 'ami-56d6ea3e',
}


def main(ubuntu_codename):
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s')
    if ubuntu_codename not in AMIS:
        logging.error('ubuntu codename %r not understood', ubuntu_codename)
        sys.exit(1)
    ami = AMIS[ubuntu_codename]
    build_number = os.environ.get('BUILD_NUMBER', time.time())
    hostname = 'bootstrap-test-lucid-%i.krxd.net' % (build_number,)
    logging.info('Starting instance %s', hostname)
    proc = subprocess.Popen(
        '/bin/bash',
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    proc.stdin.write(
        'start_instance.py -t c3.large -H %s -s krux-ops-dev %s s_basic' % (hostname, ami))
    proc.stdin.close()
    multiproc.run_subproc(proc=proc, prefix='[start_instance.py] ', output_func=logging.info)
    if proc.returncode != 0:
        logging.error('Starting instance failed! See above for details')
        sys.exit(1)
    ec2_conn = boto.ec2.connect_to_region('us-east-1')
    reservations = ec2_conn.get_all_instances(filters={'tag:Name': hostname})
    if len(reservations) == 0 or len(reservations[0].instances) == 0:
        logging.error(
            'Something has gone horribly wrong and we can\'t find the instance we just started')
        sys.exit(1)
    instance = reservations[0].instances[0]
    start = time.time()
    while instance.tags.get('krux-status') not in FINISHED_STATUSES:
        if time.time() - start > TIMEOUT:
            logging.error(
                'Instance [%s] bootstrap failed to complete in %r seconds. Current status is %r.',
                instance.id, TIMEOUT, instance.tags.get('krux-status'))
            sys.exit(1)
        logging.info('Waiting on instance %s, current status: %r',
                     instance.id, instance.tags.get('krux-status'))
        time.sleep(5)
        instance.update()
    if instance.tags['krux-status'] == 'bootstrap_failed':
        logging.error('Bootstrap failed, log into %s [%s] to debug, then terminate it.',
                      hostname, instance.id)
        sys.exit(1)
    logging.info('Bootstrap completed successfully in %rs.', time.time() - start)
    logging.info('Terminating test instance %s [%s].', hostname, instance.id)
    proc = subprocess.Popen(
        '/bin/bash',
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    proc.stdin.write(
        'delete_instance.py -y %s' % (hostname,))
    proc.stdin.close()
    multiproc.run_subproc(proc=proc, prefix='[delete_instance.py] ', output_func=logging.info)
    if proc.returncode != 0:
        logging.error('Terminating instance failed! See above for details')
        sys.exit(1)
    logging.info('Instance terminated.')


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args['<ubuntu_codename>'])
