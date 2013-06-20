#!/bin/bash -x

EMAIL=msherry@gmail.com

./bollinger.py ^VIX > out.txt

tail -1 out.txt | grep -q -E ", (\+|-)"
if [[ ( $? == 0 ) ]];
then
    # Send status email
    (cat <<EOF; uuencode output.png output.png ) | /usr/sbin/sendmail -oi -t -f $EMAIL
From: $EMAIL
To: $EMAIL
Subject: Here is a graph

EOF
else
    (cat <<EOF; tail -1 out.txt) | /usr/sbin/sendmail -oi -t -f $EMAIL
From: $EMAIL
To: $EMAIL
Subject: Nothing to report

EOF
fi
