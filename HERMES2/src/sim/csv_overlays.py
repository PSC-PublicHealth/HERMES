#! /usr/bin/env python


_hermes_svn_id_="$Id: csv_overlays.py 826 2012-02-16 23:14:57Z welling $"

import csv_tools
import util

import re

# For the moment I'm going to only maintain one overlay key.
# This will preclude being able to overlay the routes file.  
# It should be easy to change if we really want
def parseOverlayCSV(keys, recs, overlayKeys, overlayFiles, secondaryKeys=None):
    overlayFiles = util.listify(overlayFiles)
    overlayKeys = util.listify(overlayKeys)
    secondaryKeys = util.listify(secondaryKeys)

    # make a shallow copy of the recs into a list
    with util.logContext("preprocessing input file for overlay files"):
        rCopy = []
        for rec in recs:
            strKeys = {}
            for overlayKey in overlayKeys:
                try:
                    strKey = str(rec[overlayKey])
                except:
                    util.logWarning("found record lacking key in field %s"%overlayKey)
                    # with secondary keys it _might_ make sense to allow something without 
                    # all of the primary keys but I'm not going to allow it.
                    continue

                # hmm, values in key fields can change so we shouldn't cache them unless we want to deal
                # with that bit of pain.
            rCopy.append(rec)
        recs = rCopy

    for ovlFile in overlayFiles:
        with util.logContext("processing overlay file %s"%ovlFile):
            # slurp in an overlay csv file
            with util.openFileOrHandle(ovlFile) as f:
                (ovlKeys, ovlRecs) = csv_tools.parseCSV(f)
            
            # go through the overlay records
            for r in ovlRecs:
                useSecondaryKeys = True
                keyRegExs = []
                keyList = []

                for key in overlayKeys:
                    try: 
                        curKey = str(r[key])
                        if curKey == '':
                            continue
                    except:
                        continue
                
                    curKey = "^" + curKey + "$"
                    try:
                        pre = re.compile(curKey)
                    except:
                        util.raiseRuntimeError("'%s' is an invalid regex"%curKey)
                    keyRegExs.append((key, pre))
                    keyList.append(key)
                    useSecondaryKeys = False

                if useSecondaryKeys:
                    for key in secondaryKeys:
                        try:
                            curKey = str(r[key])
                            if curKey == '':
                                continue
                        except:
                            continue
                    
                        curKey = "^" + curKey + "$"
                        try:
                            pre = re.compile(curKey)
                        except:
                            util.raiseRuntimeError("'%s' is an invalid regex"%curKey)
                        keyRegExs.append((key, pre))
                        keyList.append(key)

                if len(keyRegExs) == 0:
                    util.logWarning("overlay record found with no primary or secondary keys")
                    continue

                used = False
                for rec in recs:
                    keysMatch = False
                    for (keyField,pre) in keyRegExs:
                        try:
                            key = str(rec[keyField])
                        except:
                            break

                        if not pre.match(key):
                            break
                    else:
                        # since python doesn't have labeled loops we do this dance.
                        # at least for loops have an else clause.  If it had the 
                        # opposite of an else clause, I could mostly make do without
                        # these games.
                        keysMatch = True

                    if not keysMatch:
                        continue
                    
                    used = True
                    for (k,v) in r.items():
                        if k in keyList:
                            continue

                        vstr = str(v)
                        if len(vstr) == 0:
                            continue

                        if vstr == '_remove_':
                            rec[k] = ''
                            continue

                        if vstr[0] == '+':
                            try:
                                v_add = vstr[1:]
                                try:
                                    v_add = float(vstr[1:])
                                    try:  v_add = int(vstr[1:])
                                    except: pass
                                except:
                                    pass
                                if k in rec:
                                    try: rec[k] += v_add
                                    except:  continue
                            except:
                                util.raiseRuntimeError("error processing %s in field %s for id %s"%\
                                                           (v, k, key))
                            continue

                        if vstr[0] == '*':
                            try:
                                v_mul = vstr[1:]
                                try:
                                    v_mul = float(vstr[1:])
                                    try:  v_mul = int(vstr[1:])
                                    except:  pass
                                except:
                                    pass
                                if k in rec:
                                    try: rec[k] = rec[k] * v_mul
                                    except: continue
                            except:
                                util.raiseRuntimeError("error processing %s in field %s for id %s"%\
                                                           (v, k, key))
                            continue

                        rec[k] = v

                if not used:
                    util.logWarning("no matching key found for overlay record %s."%curKey)

            # append any new keys in the overlay file
            for k in ovlKeys:
                if k not in keys:
                    keys.append(k)

    return keys, recs


        
            
