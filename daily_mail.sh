#!/bin/bash
# Send by email logs of an IRC chan
#
# v0.1 : 2010-10-18 ; teymour for supybot
# v0.2 : 2012-08-25 ; Roux for gazouilleur
#
# To be set in a crontab 
# 30 03 * * * bash /home/gazouilleur2/gazouilleur/daily_mail.sh

LOGPATH=$(echo $0 | sed 's/[^\/]*$//')/log/${botnick}_${chan}.log
EMAILDEST=$email
MAX_CHAR=150

NBLINE=$(wc -l $LOGPATH | sed 's/ .*//')
BEGINLINE=$(grep -n ^$(date -d 'yesterday' '+%Y-%m-%d') $LOGPATH | head -n 1 | sed 's/:.*//')
TAILLINE=$(( $NBLINE - $BEGINLINE ))
tail -n $TAILLINE $LOGPATH > /tmp/email_log.txt
echo "" >> /tmp/email_log.txt
echo "--" >> /tmp/email_log.txt
echo "Envoyé par $0 via la crontab de l'utilisateur gazouilleur" >> /tmp/email_log.txt
#cat /tmp/email_log.txt
cat /tmp/email_log.txt | iconv -c -f UTF-8 -t ISO-8859-1 | mail -s "[Regards Citoyens] IRC log $(date -d 'yesterday' '+%Y-%m-%d')" $EMAILDEST

