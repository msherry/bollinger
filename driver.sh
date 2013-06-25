#!/bin/bash -x

EMAIL=msherry@gmail.com

./bollinger.py ^VIX > out.txt

tail -1 out.txt | grep -q -E ", (\+|-)"
if [[ ( $? == 0 ) ]];
then
    # Send status email
    (cat <<EOF; base64 output.png ) | /usr/sbin/sendmail -oi -t -f $EMAIL
From: $EMAIL
To: $EMAIL
Subject: Here is a graph
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary=_frontier

--_frontier
Content-Type: image/png
Content-Transfer-Encoding: base64
EOF
else
    (cat <<EOF; tail -1 out.txt) | /usr/sbin/sendmail -oi -t -f $EMAIL
From: $EMAIL
To: $EMAIL
Subject: Nothing to report

EOF
fi
