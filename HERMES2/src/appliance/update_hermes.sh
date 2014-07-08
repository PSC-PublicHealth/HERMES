#!/bin/sh
#echo "Ping" `ping -c 1 redmine.hindsight.psc.edu`
if [ "x`ping -c 1 redmine.hindsight.psc.edu`" !=  "x" ]; then
   cd ~/HERMES2
   svn update
   python alembic_upgrade.py 
else
   xmessage "No Internet Connection - Please connect to the intenet and try again" 
fi
echo "$pingvar"
