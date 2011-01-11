#!/usr/bin/env python

import sys
import os
import urllib, urllib2
import re
import subprocess
from datetime import datetime
import socket


REPO_HOST = "codegrove.org"
COMMIT_URL = r'http://example.com/commit/%s'

EMAIL_RE = re.compile("^(.*) <(.*)>$")


IRCCAT_HOST = "localhost"
IRCCAT_TCP_PORT = 3011



class Irccat(object):
    """
    dead simple bridge to irccat
    http://irccat.rubyforge.org/use.html
    """

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def say(self, msg):
        """say something to irc"""
        print "saying to irc %s"  % msg
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.send(msg)
        s.close()


def get_revisions(old, new):
    git = subprocess.Popen(['git', 'rev-list', '--pretty=medium', '%s..%s' % (old, new)], stdout=subprocess.PIPE)
    sections = git.stdout.read().split('\n\n')[:-1]

    revisions = []
    s = 0
    while s < len(sections):
        lines = sections[s].split('\n')

        # first line is 'commit HASH\n'
        props = {'id': lines[0].strip().split(' ')[1]}

        # read the header
        for l in lines[1:]:
            key, val = l.split(' ', 1)
            props[key[:-1].lower()] = val.strip()

        # read the commit message
        props['message'] = sections[s+1]

        # use github time format
        basetime = datetime.strptime(props['date'][:-6], "%a %b %d %H:%M:%S %Y")
        tzstr = props['date'][-5:]
        props['date'] = basetime.strftime('%Y-%m-%dT%H:%M:%S') + tzstr

        # split up author
        m = EMAIL_RE.match(props['author'])
        if m:
            props['name'] = m.group(1)
            props['email'] = m.group(2)
        else:
            props['name'] = 'unknown'
            props['email'] = 'unknown'
        del props['author']

        revisions.append(props)
        s += 2

    return revisions

def get_commits(old, new, ref):

    revisions = get_revisions(old, new)
    commits = []
    for r in revisions:
        commits.append({
                'id': r['id'],
                'author': {'name': r['name'], 'email': r['email']},
                'url': COMMIT_URL % r['id'],
                'message': r['message'],
                'timestamp': r['date']
            })
    return commits


def make_irc_friendly(commit_msg):
    first_line = (commit_msg or "").split("\n")[0]
    return first_line.strip()

def main():
    irc = Irccat(IRCCAT_HOST, IRCCAT_TCP_PORT)
    for line in sys.stdin.xreadlines():
        old, new, ref = line.strip().split(' ')

        for commit in  get_commits(old, new, ref):
            irc.say("%s commited '%s' to ssh://%s:%s" % (
                commit['author']['name'],
                make_irc_friendly(commit['message']),
                REPO_HOST,
                os.getcwd(),
            ))

if __name__ == '__main__':
    main()
