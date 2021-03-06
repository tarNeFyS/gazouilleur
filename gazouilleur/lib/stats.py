#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, time
from json import dump as write_json
from twisted.internet.defer import inlineCallbacks, returnValue
from datetime import datetime
from gazouilleur import config
from gazouilleur.lib.mongo import find_stats, sortasc, sortdesc
from gazouilleur.lib.log import loggerr
from gazouilleur.lib.utils import *

class Stats(object):

    def __init__(self, user):
        self.now = timestamp_hour(datetime.today())
        self.user = user
        try:
            self.url = '%s/' % config.URL_STATS.rstrip('/')
        except:
            self.url = None

    @inlineCallbacks
    def print_last(self):
        since = self.now - timedelta(days=30)
        stats = yield find_stats({'user': self.user, 'timestamp': {'$gte': since}}, filter=sortdesc('timestamp'))
        if not len(stats):
            returnValue("%s %s %s" % (self.user, self.now, since))
        stat = stats[0]
        rts = 0
        fols = 0
        twts = 0
        delays = {1: 'hour', 6: '6 hours', 24: 'day', 7*24: 'week', 30*24: 'month'}
        order = delays.keys()
        order.sort()
        olds = {'tweets': {}, 'followers': {}, 'rts': {}}
        for s in stats:
            d = self.now - s['timestamp']
            delay = d.seconds / 3600 + d.days * 24
            fols = stat['followers'] - s['followers']
            twts = stat['tweets'] - s['tweets']
            for i in order:
                if delay == i:
                    if 'stats%sH' % i not in olds['tweets']:
                        olds['tweets']['stats%sH' % i] = twts if twts not in olds['tweets'].values() else 0
                    if 'stats%sH' % i not in olds['followers']:
                        olds['followers']['stats%sH' % i] = fols if fols not in olds['followers'].values() else 0
                    if 'stats%sH' % i not in olds['rts']:
                        olds['rts']['stats%sH' % i] = rts if rts not in olds['rts'].values() else 0
            rts += s['rts_last_hour']
        olds['rts']['stats1H'] = stat['rts_last_hour']
        for i in order:
            if rts and 'stats%sH' % i not in olds['rts'] and rts not in olds['rts'].values():
                olds['rts']['stats%sH' % i] = rts
                rts = 0
            if fols and 'stats%sH' % i not in olds['followers']  and fols not in olds['followers'].values():
                olds['followers']['stats%sH' % i] = fols
                fols = 0
            if twts and 'stats%sH' % i not in olds['tweets'] and twts not in olds['tweets'].values():
                olds['tweets']['stats%sH' % i] = twts
                twts = 0
        res = []
        if stat['tweets']:
            res.append("Tweets: %d total" % stat['tweets'] + " ; ".join([""]+["%d last %s" %  (olds['tweets']['stats%sH' % i], delays[i]) for i in order if 'stats%sH' % i in olds['tweets'] and olds['tweets']['stats%sH' % i]]))
        if stat['followers']:
            res.append("Followers: %d total" % stat['followers'] + " ; ".join([""]+["%+d last %s" %  (olds['followers']['stats%sH' % i], delays[i]) for i in order if 'stats%sH' % i in olds['followers'] and olds['followers']['stats%sH' % i]]))
        textrts = ["%d last %s" % (olds['rts']['stats%sH' % i], delays[i]) for i in order if 'stats%sH' % i in olds['rts'] and olds['rts']['stats%sH' % i]]
        if textrts:
            res.append("RTs: " + " ; ".join(textrts))
        if self.url and res:
            res.append("More details: %sstatic_stats_%s.html" % (self.url, self.user))
        returnValue([(True, "[Stats] %s" % m) for m in res])

    @inlineCallbacks
    def dump_data(self):
        if not self.url:
            returnValue(False)
        stats = yield find_stats({'user': self.user}, filter=sortasc('timestamp'))
        dates = [s['timestamp'] for s in stats]
        tweets = [s['tweets'] for s in stats]
        tweets_diff = [a - b for a, b in zip(tweets[1:],tweets[:-1])]
        followers = [s['followers'] for s in stats]
        followers_diff = [a - b for a, b in zip(followers[1:], followers[:-1])]
        rts_diff = [s['rts_last_hour'] for s in stats]
        rts = []
        n = 0
        for a in rts_diff:
            n += a
            rts.append(n)

        jsondata = {}
        imax = len(dates) - 1
        for i, date in enumerate(dates):
            ts = int(time.mktime(date.timetuple()))
            jsondata[ts] = { 'tweets': tweets[i], 'followers': followers[i], 'rts': rts[i] }
            if i < imax:
                jsondata[ts].update({ 'tweets_diff': tweets_diff[i], 'followers_diff': followers_diff[i], 'rts_diff': rts_diff[i+1] })

        try:
            jsondir = os.path.join('web', 'data')
            if not os.path.exists(jsondir):
                os.makedirs(jsondir)
            with open(os.path.join(jsondir, 'stats_%s.json' % self.user), 'w') as outfile:
                write_json(jsondata, outfile)
        except IOError as e:
            loggerr("Could not write web/data/stats_%s.json : %s" % (self.user, e), action="stats")

        try:
            from plots import CumulativeCurve, DailyHistogram, WeekPunchCard
            imgdir = os.path.join('web', 'img')
            if not os.path.exists(imgdir):
                os.makedirs(imgdir)
            CumulativeCurve(dates, tweets, 'Total tweets', imgdir, 'tweets_%s' % self.user)
            CumulativeCurve(dates, followers, 'Total followers', imgdir, 'followers_%s' % self.user)
            CumulativeCurve(dates, rts, 'Total RTs since %s' % dates[0], imgdir, 'rts_%s' % self.user)
            DailyHistogram(dates[:-1], tweets_diff, 'New tweets', imgdir, 'new_tweets_%s' % self.user)
            DailyHistogram(dates[:-1], followers_diff, 'New followers', imgdir, 'new_followers_%s' % self.user)
            DailyHistogram(dates[:-1], rts_diff[1:], 'New RTs', imgdir, 'new_rts_%s' % self.user)
            WeekPunchCard(dates[:-1], tweets_diff, 'Tweets punchcard', imgdir, 'tweets_card_%s' % self.user)
            WeekPunchCard(dates[:-1], followers_diff, 'Followers punchcard', imgdir, 'followers_card_%s' % self.user)
            WeekPunchCard(dates[:-1], rts_diff[1:], 'RTs punchcard', imgdir, 'rts_card_%s' % self.user)
        except Exception as e:
            loggerr("Could not write images in web/img for %s : %s" % (self.user, e), action="stats")

        self.render_template(os.path.join("web", "templates"), "static_stats.html")
        returnValue(True)

    def render_template(self, path, filename):
        data = {'user': self.user, 'url': self.url}
        outfile = filename.replace('.html', '_%s.html' % self.user)
        try:
            import pystache
            from contextlib import nested
            with nested(open(os.path.join(path, filename), "r"), open(os.path.join("web", outfile), "w")) as (template, generated):
                generated.write(pystache.render(template.read(), data))
        except IOError as e:
            loggerr("Could not write web/%s from %s/%s : %s" % (outfile, path, filename, e), action="stats")

