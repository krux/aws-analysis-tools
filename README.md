aws-analysis-tools
==================
instances.py

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


To make a new release follow standard development procedures (branch, develop, review, merge to master), then update the VERSION in setup.py, and finally merge master to release. When code is pushed to release, a Jenkins job should automatically build, package, and upload the new version. See: http://ci.krxd.net/job/aws-analysis-tools/
