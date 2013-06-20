#!/bin/bash -x

./bollinger.py ^VIX | tail -1 | grep -q -E ", (\+|-)"
if [[ ( $? == 0 ) ]];
then
    # Send status email
    (cat <<EOF; uuencode output.png output.png ) | /usr/sbin/sendmail -oi -t -f $EMAIL
From: $EMAIL
To: $EMAIL
Subject: Here is a graph

EOF
fi
