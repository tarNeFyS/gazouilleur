#!/bin/bash
# Send by email logs of an IRC chan
#
# v0.1 : 2010-10-18 ; teymour for supybot
# v0.2 : 2012-08-25 ; Roux for gazouilleur
#
# Set below which <CHAN>'s log will be sent to <EMAILDEST>
# To be set in a crontab 
# 30 03 * * * bash /home/gazouilleur/gazouilleur2/bin/daily_mail.sh
# @reboot     bash /home/gazouilleur/gazouilleur2/bin/gazouilleur start --nologs

# Set the appropriate info below
BOT="gazouilleur2"
CHAN="#regardscitoyens"
EMAILDEST="contact@regardscitoyens.org"

LOGPATH=$(echo $0 | sed 's/[^\/]*$//')../log/${BOT}_${CHAN}.log
TMPPATH="/tmp/$BOT-$CHAN.tmp"
if test -f "$LOGPATH.1"; then
  cat "$LOGPATH.1" "$LOGPATH" > "$TMPPATH"
  LOGPATH="$TMPPATH"
fi

MAX_CHAR=150

NBLINE=$(wc -l $LOGPATH | sed 's/ .*//')
BEGINLINE=$(grep -n ^$(date -d 'yesterday' '+%Y-%m-%d') $LOGPATH | head -n 1 | sed 's/:.*//')
TAILLINE=$(( $NBLINE - $BEGINLINE + 5))
tail -n $TAILLINE $LOGPATH | sed 's/^/ /' | fold -w $MAX_CHAR -s | sed 's/^\([^ ]\)/                   \1/' > /tmp/email_log.txt
echo "" >> /tmp/email_log.txt
echo "--" >> /tmp/email_log.txt
echo "Envoyé par $0 via la crontab de l'utilisateur gazouilleur" >> /tmp/email_log.txt
#DEBUG
#cat /tmp/email_log.txt
cat /tmp/email_log.txt | iconv -c -f UTF-8 -t ISO-8859-1 | mail -s "[Regards Citoyens] IRC log $(date -d 'yesterday' '+%Y-%m-%d')" $EMAILDEST

rm -f "$TMPPATH"
