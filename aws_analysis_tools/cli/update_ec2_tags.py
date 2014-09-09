#!/usr/bin/env kaws-python

"""
Updates EC2 tags using a new scheme to get around the 255 character limit that
AWS imposes on tags, and emits stats via krux.cli fanciness.
"""

######################
# Standard Libraries #
######################
from __future__ import absolute_import

##################
# Krux Libraries #
##################
import krux.cli
import krux_boto

from krux_boto import add_boto_cli_arguments


EC2_CLASS_KEY = 's_classes'


class Application(krux_boto.Application):

    def __init__(self):
        ### Call superclass to get krux-stdlib
        super(Application, self).__init__(name = 'update-ec2-tags')

        self.instance_id    = self.args.instance_id
        self.ec2_region     = self.args.ec2_region
        self.environment    = self.args.environment
        self.cluster_name   = self.args.cluster_name
        self.classes        = self.args.classes
        self.dry_run        = self.args.dry_run

    def add_cli_arguments(self, parser):

        add_boto_cli_arguments(parser)

        group = krux.cli.get_group(parser, self.name)

        group.add_argument(
            '--instance-id',
            default = None,
            help    = "Specify the instance id to use. (default: %(default)s)"
        )

        group.add_argument(
            '--ec2-region',
            default = None,
            help    = "Specify the region to use. (default: %(default)s)"
        )

        group.add_argument(
            '--environment',
            default = None,
            help    = "Specify the environment to set. (default: %(default)s)"
        )

        group.add_argument(
            '--cluster-name',
            default = None,
            help    = "Specify the cluster name to set. (default: %(default)s)"
        )

        group.add_argument(
            '--classes',
            nargs   = "*",
            default = None,
            help    = "Specify class to tag with (can be used multiple times). "
                      "(default: %(default)s)"
        )

        group.add_argument(
            '--dry-run',
            default = False,
            action  = 'store_true',
            help    = "Do a dry run; find the tags, but do not update them in EC2. "
                      "(default: %(default)s)"
        )

    def update_tags(self,
        ec2_region      = None,
        instance_id     = None,
        classes         = None,
        environment     = None,
        cluster_name    = None,
        dry_run         = False,
    ):
        log   = self.logger
        stats = self.stats

        ### from cli or passed explicitly?
        ec2_region      = ec2_region    or self.ec2_region
        instance_id     = instance_id   or self.instance_id
        classes         = classes       or self.classes
        dry_run         = dry_run       or self.dry_run
        environment     = environment   or self.environment
        cluster_name    = cluster_name  or self.cluster_name


        with stats.timing('update_tags'):

            ### without region or instance id, we can't proceed
            if not ec2_region or not instance_id:
                self.raise_critical_error(
                    'Could not determine instance_id (%s) and/or ec2_region (%s)' % \
                    (instance_id, ec2_region)
                )

            ### many places the info can come from, so let us know here what we found
            log.info(
                'Proceeding with instance id: %s - region: %s - classes: %s',
                instance_id, ec2_region, ' '.join(classes)
            )

            ###
            ### Set up the tags we want to use
            ###
            tags_dict = {
                'environment':  environment,
                'cluster_name': cluster_name,
                EC2_CLASS_KEY:  ",".join(classes),
            }

            ### quick dump of what we're about to do send.
            for k,v in tags_dict.iteritems():
                log.info('Setting tag "%s" to: %s', k, v)


            ###
            ### Now do the actual update, if desired
            ###
            if dry_run:
                log.info('Dry run - not updating instance in EC2')

            else:
                log.info('Updating instance %s in region %s', instance_id, ec2_region)
                region_obj  = self.boto.ec2.get_region(ec2_region)
                ec2         = self.boto.connect_ec2(region = region_obj)

                ### ec2 calls throw exceptions when they fail
                try:
                    ec2.create_tags([instance_id], tags_dict)
                    stats.incr('ec2_tag_update')
                    log.info('Update completed successfully')

                ### no matter what happens, we want to catch it and make sure
                ### log it appropriately before we re-raise
                except Exception, e:
                    stats.incr('error.ec2_tag_update')
                    self.raise_critical_error('Tag update failed: %s' % e)

def main():
    app = Application()
    app.update_tags()


if __name__ == '__main__':
    main()
