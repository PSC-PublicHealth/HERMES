#! /usr/bin/env python

###################################################################################
# Copyright   2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
# =============================================================================== #
#                                                                                 #
# Permission to use, copy, and modify this software and its documentation without # 
# fee for personal use within your organization is hereby granted, provided that  #
# the above copyright notice is preserved in all copies and that the copyright    # 
# and this permission notice appear in supporting documentation.  All other       #
# restrictions and obligations are defined in the GNU Affero General Public       #
# License v3 (AGPL-3.0) located at http://www.gnu.org/licenses/agpl-3.0.html  A   #
# copy of the license is also provided in the top level of the source directory,  #
# in the file LICENSE.txt.                                                        #
#                                                                                 #
###################################################################################
"""
This program takes a directory as its single argument.  First it traverses downward 
from the given directory, searching all .py files looking for lines beginning with 
@bottle.route, which define urls.  It collects all the urls and produces regular
expressions to match them.

It then re-traverses downward from the same starting directory, looking for files
of type .tpl .  For each, it finds lines that appear to contain one of the urls found
in the first pass and outputs those lines.
"""

import re, sys, os, os.path

routeRegex = re.compile('^\s*@bottle.route\(')
urlStripRegex = re.compile(r'^\s*@bottle.route\(\s*((\'(?P<url1>[^\']+)\')|("(?P<url2>[^"]+)"))')


def getURL(line):
    """Strip out the URL part of a @bottle.route line"""
    m = urlStripRegex.match(line)
    if m:
        if m.group('url1'):
            return m.group('url1')
        else:
            return m.group('url2')
    else:
        return None


def cleanURL(url):
    assert url.startswith('/'), 'Found an un-rooted URL: %s' % url
    url = url[1:]
    parts = url.split('/')
    for offset, p in enumerate(parts):
        if p.startswith(':') or (p.startswith('<') and p.endswith('>')):
            parts = parts[:offset]
            break
    return '/'.join(parts)

def removeDups(urlList):
    l = urlList[:]
    l.sort()
    noDupsList = []
    prev = None
    for url in l:
        if url != prev:
            noDupsList.append(url)
        prev = url
    return noDupsList

urlList = []
startingDir = sys.argv[1]
for root, dirs, files in os.walk(startingDir):
    for fname in files:
        if fname.endswith('.py'):
            with open(os.path.join(root, fname), 'rU') as f:
                for line in f.readlines():
                    if routeRegex.match(line.strip()):
                        urlList.append(cleanURL(getURL(line)))

urlList = removeDups(urlList)
reList = [(url, re.compile(url)) for url in urlList]

for root, dirs, files in os.walk(startingDir):
    for fname in files:
        if fname.endswith('.tpl'):
            fullName = os.path.join(root, fname)
            with open(fullName, 'rU') as f:
                for offset, line in enumerate(f.readlines()):
                    for url, regex in reList:
                        if regex.search(line):
                            # print 'matches %s :' % url
                            print '%s(%s): %s' % (fullName, offset+1, line.strip())

