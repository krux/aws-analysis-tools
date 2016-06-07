aws-analysis-tools
==================
krux-ec2-instances
------------------
Returns all instances that match the search criteria given by the options.

*** WARNING ***
Following options have changed:
- To specify a region, use option --boto-region instead of -r or --region.
- To specify log level, use option --log-level instead of -v or --verbose.

volumes.py

pssh.py
-------
Parallel SSH to a list of nodes.

search-ec2-tags.py
------------------
Returns all hostnames that have the specified ec2 tag.

update-ec2-tags.py
------------------
Updates instance tag in ec2, with puppet classes.

test_provision.py
-----------------
Runs a test provision of an `s_basic` instance for the ubuntu release passed in (lucid/trusty). Will automatically terminate the instance if it comes up cleanly and leave it running if it does not come up cleanly. Meant to be run from a jenkins job for testing of our puppet manifests but runs fine manually as well. For more discussion and explanation please see comments in `test_provision.py`.

To make a new release follow standard development procedures (branch, develop, review, merge to master), then update the VERSION in setup.py, and finally merge master to release. When code is pushed to release, a Jenkins job should automatically build, package, and upload the new version. See: http://ci.krxd.net/job/aws-analysis-tools/
