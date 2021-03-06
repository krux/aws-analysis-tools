#!/usr/bin/env kaws-python

"""
Updates EC2 tags using a new scheme to get around the 255 character limit that
AWS imposes on tags, and emits stats via krux.cli fanciness.
"""

######################
# Standard Libraries #
######################
from __future__ import absolute_import
import platform

##################
# Krux Libraries #
##################
import krux.cli
import krux_boto

from krux_boto import add_boto_cli_arguments


class Application(krux_boto.Application):

    def __init__(self):
        # Call superclass to get krux-stdlib
        super(Application, self).__init__(name='update-ec2-tags')

        self.instance_id = self.args.instance_id
        self.ec2_region = self.args.ec2_region
        self.environment = self.args.environment
        self.cluster_name = self.args.cluster_name
        self.classes = self.args.classes
        self.lts = self.args.lts
        self.architecture = self.args.architecture
        self.kernel_version = self.args.kernel_version
        self.dry_run = self.args.dry_run

    def add_cli_arguments(self, parser):

        add_boto_cli_arguments(parser)

        group = krux.cli.get_group(parser, self.name)

        group.add_argument(
            '--instance-id',
            help=("The instance id of the instance. Example: 'i-27459bcc' "
                  "(output of `facter ec2_instance_id`)")
        )

        group.add_argument(
            '--ec2-region',
            required=True,
            help=("EC2 region to use. Example: 'us-east-1'. "
                  "NB: This is the *region*, not the *availability zone*.")
        )

        group.add_argument(
            '--environment',
            default='dev',
            help="The environment to set. (default: %(default)s)."
        )

        group.add_argument(
            '--cluster-name',
            required=True,
            help="The cluster name to set. Example: 'apiservices-a'"
        )

        group.add_argument(
            '--classes',
            nargs="*",
            default=[],
            help=("Specify class to tag with (can be used multiple times). "
                  "(default: %(default)s)")
        )

        group.add_argument(
            '--lts', '--release',
            # Let's make sure to tag this for now
            # TODO: Pull out the code to deduce this from krux-manage-instance and use it here.
            required=True,
            help=("The name of the ubuntu release to set. Example: 'trusty'"),
        )

        group.add_argument(
            '--architecture',
            # TODO: Pull out the code to deduce this from krux-manage-instance and use it here.
            help=("The architecture of this instance to set. Example: 'amd64'")
        )

        group.add_argument(
            '--kernel-version',
            help=("The kernel version of this instance to set. Example: '3.13.0-137-generic' "
                  "(default: `uname -r`)")
        )

        group.add_argument(
            '--dry-run',
            default=False,
            action='store_true',
            help=("Do a dry run; find the tags, but do not update them "
                  "in EC2. (default: %(default)s)")
        )

    def update_tags(
        self,
        ec2_region=None,
        instance_id=None,
        classes=None,
        environment=None,
        cluster_name=None,
        lts=None,
        architecture=None,
        kernel_version=None,
        dry_run=False,
    ):
        log = self.logger
        stats = self.stats

        # from cli or passed explicitly?
        ec2_region = ec2_region if ec2_region is not None else self.ec2_region
        instance_id = instance_id if instance_id is not None else self.instance_id
        classes = classes if classes is not None else self.classes
        dry_run = dry_run if dry_run is not None else self.dry_run
        environment = environment if environment is not None else self.environment
        cluster_name = cluster_name if cluster_name is not None else self.cluster_name
        lts = lts if lts is not None else self.lts
        architecture = architecture if architecture is not None else self.architecture
        kernel_version = kernel_version or self.kernel_version or platform.release()

        with stats.timing('update_tags'):

            # without region or instance id, we can't proceed
            if ec2_region is None or instance_id is None:
                self.raise_critical_error(
                    'Could not determine instance_id ({instance_id}) and/or ec2_region ({region})'.format(
                        instance_id=instance_id,
                        region=ec2_region,
                    )
                )

            # many places the info can come from, so let us know here what we found
            log.info(
                'Proceeding with instance id: %s - region: %s - classes: %s',
                instance_id, ec2_region, ' '.join(classes)
            )

            #
            # Set up the tags we want to use
            #
            tags_dict = {
                'environment': environment,
                'cluster_name': cluster_name,
                's_classes': ",".join(classes),
                'lts': lts,
                'architecture': architecture,
                'kernel_version': kernel_version,
            }

            # quick dump of what we're about to do send.
            for k, v in tags_dict.items():
                log.info('Setting tag "%s" to: %s', k, v)

            #
            # Now do the actual update, if desired
            #
            if dry_run:
                log.info('Dry run - not updating instance in EC2')

            else:
                log.info('Updating instance %s in region %s', instance_id, ec2_region)
                region_obj = self.boto.ec2.get_region(ec2_region)
                ec2 = self.boto.connect_ec2(region=region_obj)

                # ec2 calls throw exceptions when they fail
                try:
                    ec2.create_tags([instance_id], tags_dict)
                    stats.incr('ec2_tag_update')
                    log.info('Update completed successfully')

                # no matter what happens, we want to catch it and make sure
                # log it appropriately before we re-raise
                except Exception:
                    stats.incr('error.ec2_tag_update')
                    raise


def main():
    app = Application()
    with app.context():
        app.update_tags()


if __name__ == '__main__':
    main()
