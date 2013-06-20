#!/bin/bash -x
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
#
# !!!IMPORTANT!!!
# Edit this file and change this next line to your own email address:
#

export EMAIL=msherry@gmail.com

cd bollinger
git pull
./driver.sh

# Give the email some time to be queued and delivered
sleep 120 # 2 minutes

# This will stop the EBS boot instance, stopping the hourly charges.
# Have Auto Scaling terminate it, stopping the storage charges.
shutdown -h now

exit 0

########################################################################
#
# For more information about this code, please read:
#
#   Running EC2 Instances on a Recurring Schedule with Auto Scaling
#   http://alestic.com/2011/11/ec2-schedule-instance
#
# The code and its license are available on github:
#
#   https://github.com/alestic/demo-ec2-schedule-instance
#
########################################################################
