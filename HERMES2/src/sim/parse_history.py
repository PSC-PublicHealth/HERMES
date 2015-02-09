#!/usr/bin/env python

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

_hermes_svn_id_="$Id$"

import os,sys

def quoteSplit(line):
    offset= 0
    words= []
    state= 0
    while len(line)>offset:
        if state==0: # unquoted
            if line[offset]==',':
                words.append(line[:offset])
                line= line[offset+1:]
                offset= 0
                line= line.strip()
            elif line[offset]=='"':
                state= 1
                offset += 1
            else:
                offset += 1
        elif state==1:
            if line[offset]=='"':
                state= 0
                offset += 1
            else:
                offset += 1
        else:
            raise RuntimeError("FSM is broken")
    words.append(line)
    return words

def main():
    print '"time","age","event","storage","nVials","groupID"'
    lines= sys.stdin.readlines()
    for line in lines:
        try:
            line= line.strip()
            if len(line)==0: continue
            if line[0]=='#': continue
            if line[0]=='*': continue
            words= quoteSplit(line)
            if len(words)<3: continue
            #print words
            words[1]= words[1][15:-3]
            #print words
            subWords= words[1].split(',')
            #print subWords
            time= float(words[0])
            nVials= int(subWords[0])
            storage= subWords[2]
            groupID= subWords[3]
            age= float(subWords[5])
            event= words[2][1:-1]
            print '%g, %g, "%s", "%s", %d, "%s"'%\
                  (time,age,event,storage,nVials,groupID)
        except IndexError,e:
            print "Index Error: %s"%e
            print words

############
# Main hook
############

if __name__=="__main__":
    main()
