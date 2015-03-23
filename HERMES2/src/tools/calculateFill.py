# ramblings on calculating fill ratios over 3 volumes


def precalcRules(rules):
    """
    this routine takes a ruleset and converts it to a new ruleset that 
    calculateOwnerStorageFillRatios() can use.

    rules is a dict with a keys being the names used in requested and values being 3-tuples 
    of whether that key can be stored in freezer, cooler or warm space in the form 
    (True, True, False).

    We do not allow the case where something can be stored in both freezer and warm space 
    (freezer request will be ignored if warm space is requested).

    """
    ret = {}

    for itemType, fcw in rules.items():
        freeze, cool, warm = fcw
        if warm:
            if cool:
                s = "warmCool"
            else:
                s = "warm"
        elif cool:
            if freeze:
                s = "coolFreeze"
            else:
                s = "cool"
        elif freeze:
            s = "freeze"
        else: # nothing was specified, so just call it warm
            s = "warm"
        ret[itemType] = s

    return ret

storeGroups = { 'warm' : ('warm',),
                'cool' : ('cool',),
                'freeze' : ('freeze',),
                'warmCool' : ('warm', 'cool'),
                'coolFreeze' : ('cool', 'freeze'),
                'warmCoolFreeze' : ('warm', 'cool', 'freeze'), # might not support these last two but they
                'warmFreeze' : ('warm', 'freeze') }            # don't hurt us to be here.

def calculateOwnerStorageFillRatios(availSpace, requested, rules):
    """
    availSpace is a tuple of (freezer (-), cooler (+), and warm(w)) space available.
    requested is a list of tuples of [(name1, volume1), (name2, volume2), ...].

    rules is the output of precalcRules()
    """

    
    r = defaultdict(lambda : [])  # holds the list of tuples for each grouping
    v = defaultdict(lambda : 0) # holds the volume requested for each grouping
    
    # group everything into appropriate groups
    for rItem, vol in requested:
        sType = rules[rItem]
        r[sType].append((rItem, vol),)
        v[sType] += vol

    s = {'freeze': availSpace[0], 'cool': availSpace[1], 'warm': availSpace[2]}

    grouping = calc(s, v)
    


def calc(spaces, volumes): # available spaces, requested volumes
    

    totS = sum(spaces.values())
    totV = sum(volumes.values())

    
    baseRatio = totV / totS
    if baseRatio > 1.0:
        baseRatio = 1.0
    baseSpaceFills = defaultdict(lambda : 0)

    # figure out which groups are oversubscribed


    for group,amount in volumes.items():
        locCount = len(storeGroups[group])
        for space in storeGroups[group]:
            baseSpaceFills[space] += amount / locCount * baseRatio
        

            


def xxxshare1(space, volumes):
    " we will assume that all volumes presented can be placed in the type of space available"
    totV = sum(volumes.values())
    if space > totV:
        baseRatio = 1.0
    else:
        baseRatio = (1.0 * space) / totV

    ret = []
    for name,vol in volumes:
        ret.append((name,baseRatio * vol),)

    return ret


def _share1(space, *vols):
    sv = sum(vols)
    if space > sv:
        baseRatio = 1.0
    else:
        baseRatio = (1.0 * space) / sv
    
    ret = [baseRatio]
    for v in vols:
        ret.append(baseRatio * v)
    return ret
    

def d0(a,b):
    try:
        return a/b
    except:
        return 0.0

def share2(space1, space2, vol1, vol2, vol12):
    sv1 = sum(vol1)
    sv2 = sum(vol2)
    sv12 = sum(vol12)
    
    (r1_1, v1_1, r12_1, v12_1,
     r2_2, v2_2, r12_2, v12_2) = _share2(space1, space2, sv1, sv2, sv12)

    
    v1_1 = [v * r1_1 for v in vol1]
    v12_1 = [v * r12_1 for v in vol12]
    v2_2 = [v * r2_2 for v in vol2]
    v12_2 = [v * r12_2 for v in vol12]

    return (r1_1, v1_1, r12_1, v12_1, r2_2, v2_2, r12_2, v12_2)



def _share2(space1, space2, vol1, vol2, vol12):
    """
    returns (vol1 ratio going into space1,
             vol1 amount going into space1,
             vol12 ratio going into space1,
             vol12 amount going into space1,
             vol2 ratio going into space2,
             vol2 amount going into space2,
             vol12 ratio going into space2,
             vol12 amount going into space2)

    """
    totS = space1 + space2
    totV = vol1 + vol2 + vol12

    if totS >= totV:
        baseRatio = 1.0
    else:
        baseRatio = (1.0 * totS) / totV

    if vol1 * baseRatio > space1:
        r2, v2, v12 = _share1(space2, vol2, vol12)
        r1 = d0(1.0 * space1, vol1)
        v1 = 1.0 * space1

        return (r1, v1, 0.0, 0.0,
                r2, v2, r2, v12)

    if vol2 * baseRatio > space2:
        r1, v1, v12 = _share1(space1, vol1, vol12)
        r2 = d0(1.0 * space2, vol2)
        v2 = 1.0 * space2
        
        return (r1, v1, r1, v12,
                r2, v2, 0.0, 0.0)

    v1 = vol1 * baseRatio
    v2 = vol2 * baseRatio
    v12_1 = space1 - v1
    if v12_1 > vol12:
        v12_1 = 1.0 * vol12
    v12_2 = space2 - v2
    if v12_2 > vol12 - v12_1:
        v12_2 = 1.0 * vol12 - v12_1
    r12_1 = d0(v12_1, vol12)
    r12_2 = d0(v12_2, vol12)

    return (baseRatio, v1, r12_1, v12_1,
            baseRatio, v2, r12_2, v12_2)


        

def _share3(space1, space2, space3, vol1, vol2, vol3, vol12, vol23, vol123):
    """
    returns (vol1 ratio going into space1,
             vol1 amount going into space1,
             vol12 ratio going into space1,
             vol12 amount going into space1,
             vol123 ratio going into space1,
             vol123 amount going into space1,

             vol2 ratio going into space2,
             vol2 amount going into space2,
             vol12 ratio going into space2,
             vol12 amount going into space2,
             vol23 ratio going into space2,
             vol23 amount going into space2,
             vol123 ratio going into space2,
             vol123 amount going into space2,

             vol3 ratio going into space3,
             vol3 amount going into space3,
             vol23 ratio going into space3,
             vol23 amount going into space3,
             vol123 ratio going into space3,
             vol123 amount going into space3)
    """
            
    totS = space1 + space2 + space3
    totV = vol1 + vol2 + vol3 + vol12 + vol23 + vol123

    if totS >= totV:
        baseRatio = 1.0
    else:
        baseRatio = (1.0 * totS) / totV

    # find where we're constrained
    cv1 = vol1 * baseRatio > space1
    cv2 = vol2 * baseRatio > space2
    cv3 = vol3 * baseRatio > space3
    cv12 = (vol1 + vol12 + vol2) * baseRatio > space1 + space2
    cv23 = (vol3 + vol23 + vol2) * baseRatio > space3 + space2
    cv13 = vol1 * baseRatio > space1 and vol3 * baseRatio > space3
    

    if cv1 and not (cv12 or cv13): # see if only space1 is constrained
        print "case4"
        (r2_2, (v2_2, v12_2), r23_2, (v23_2, v123_2), 
         r3_3, (v3_3,), 
         r23_3, (v23_3, v123_3)) = share2(space2, space3, 
                                          (vol2,vol12), (vol3,), (vol23,vol123))

        (r1_1, v1_1) = _share1(space1, vol1)
        return (r1_1, v1_1, 0.0, 0.0, 0.0, 0.0,
                r2_2, v2_2, r2_2, v12_2, r23_2, v23_2, r23_2, v123_2,
                r3_3, v3_3, r23_3, v23_3, r23_3, v123_3)

        
    if cv3 and not(cv23 or cv13): # see if space3 is constrained
        print "case5"
        (r1_1, (v1_1,), r12_1, (v12_1, v123_1),
         r2_2, (v2_2, v23_2), 
         r12_2, (v12_2, v123_2)) = share2(space1, space2,
                                          (vol1,), (vol2, vol23), (vol12, vol123))
        (r3_3, v3_3) = _share1(space3, vol3)
        return (r1_1, v1_1, r12_1, v12_1, r12_1, v123_1,
                r2_2, v2_2, r12_2, v12_2, r2_2, v23_2, r12_2, v123_2,
                r3_3, v3_3, 0.0, 0.0, 0.0, 0.0)

    if cv2 and not(cv12 or cv23): # see if space2 is constrained
        print "case6"
        (r1_1, (v1_1, v12_1), r123_1, (v123_1, ),
         r3_3, (v3_3, v23_3), 
         r123_3, (v123_3, )) = share2(space1, space3, 
                                      (vol1, vol12), (vol3, vol23), (vol123,))
        (r2_2, v2_2) = _share1(space2, vol2)
        return (r1_1, v1_1, r1_1, v12_1, r123_1, v123_1,
                r2_2, v2_2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                r3_3, v3_3, r3_3, v23_3, r123_3, v123_3)

    # check if we are constrained on two spaces
    if cv12:
        print "case1"
        # if here we have our excess of space in space3 only
        (r1_1, v1_1, r12_1, v12_1, 
         r2_2, v2_2, r12_2, v12_2) = _share2(space1, space2, vol1, vol2, vol12)
        (r3_3, v3_3, v23_3, v123_3) = _share1(space3, vol3, vol23, vol123)
        return (r1_1, v1_1, r12_1, v12_1, 0.0, 0.0,
                r2_2, v2_2, r12_2, v12_2, 0.0, 0.0, 0.0, 0.0,
                r3_3, v3_3, r3_3, v23_3, r3_3, v123_3)

    if cv23:
        print "case2"
        # if here we have our excess of space in space 1 only
        (r1_1, v1_1, v12_1, v123_1) = _share1(space1, vol1, vol12, vol123)
        (r2_2, v2_2, r23_2, v23_2,
         r3_3, v3_3, r23_3, v23_3) = _share2(space2, space3, vol2, vol3, vol23)
        return (r1_1, v1_1, r1_1, v12_1, r1_1, v123_1,
                r2_2, v2_2, 0.0, 0.0, r23_2, v23_2, 0.0, 0.0,
                r3_3, v3_3, r23_3, v23_3, 0.0, 0.0)


    if cv13:
        print "case3"
        # excess in space 2 only
        (r1_1, v1_1) = _share1(space1, vol1)
        (r3_3, v3_3) = _share1(space3, vol3)
        (r2, v2_2, v12_2, v23_2, v123_2) = _share1(space2, vol2, vol12, vol23, vol123)
        return (r1_1, v1_1, 0.0, 0.0, 0.0, 0.0,
                r2, v2_2, r2, v12_2, r2, v23_2, r2, v123_2,
                r3_3, v3_3, 0.0, 0.0, 0.0, 0.0)

    print "case7"

    # if we're here we should be able to place all volumes at baseRatio
    br = baseRatio
    vol1 *= br
    vol2 *= br
    vol3 *= br
    v12 = br * vol12
    v23 = br * vol23
    v123 = br * vol123
    # we know where vol1-vol3 goes without issue
    space1 -= vol1
    space2 -= vol2
    space3 -= vol3

    if v12 >= space1:
        v12_1 = space1
        space1 = 0.0
        v12_2 = v12 - v12_1
        space2 -= v12_2
    else:
        v12_1 = v12
        space1 -= v12_1
        v12_2 = 0.0

    if v23 > space2:
        v23_2 = space2
        space2 = 0.0
        v23_3 = v23 - v23_2
        space3 -= v23_3
    else:
        v23_2 = v23
        space2 -= v23_2
        v23_3 = 0.0

    # we don't need to do accounting for the spaces on this last volume
    if v123 >= space1:
        v123_1 = space1
        #space1 = 0.0
        v123 -= v123_1

        if v123 >= space2:
            v123_2 = space2
            #space2 = 0.0
            v123_3 = v123 - v123_2
            #space3 -= v123_3
        else:
            v123_2 = v123
            #space2 -= v123_2
            v123_3 = 0.0
    else:
        v123_1 = v123
        #space1 -= v123_1
        v123_2 = 0.0
        v123_3 = 0.0

    return (br, vol1, d0(v12_1, vol12), v12_1, d0(v123_1, vol123), v123_1,
            br, vol2, d0(v12_2, vol12), v12_2, 
            d0(v23_2, vol23), v23_2, d0(v123_2, vol123), v123_2,
            br, vol3, d0(v23_3, vol23), v23_3, d0(v123_3, vol123), v123_3)


        
        

def test3(s1, s2, s3, v1, v2, v3, v12, v23, v123):
    (r1_1, v1_1, r12_1, v12_1, r123_1, v123_1,
     r2_2, v2_2, r12_2, v12_2, r23_2, v23_2, r123_2, v123_2,
     r3_3, v3_3, r23_3, v23_3, r123_3, v123_3) = _share3(s1, s2, s3, v1, v2, v3, v12, v23, v123)

    print "space1: %s of %s"%(v1_1 + v12_1 + v123_1, s1)
    print "space2: %s of %s"%(v2_2 + v12_2 + v23_2 + v123_2, s2)
    print "space3: %s of %s"%(v3_3 + v23_3 + v123_3, s3)
    print "vol1: %s of %s (%s)"%(v1_1, v1, d0(v1_1, v1))
    print "vol2: %s of %s (%s)"%(v2_2, v2, d0(v2_2, v2))
    print "vol3: %s of %s (%s)"%(v3_3, v3, d0(v3_3, v3))
    print "vol12: %s (%s, %s) of %s (%s)"%(v12_1 + v12_2, v12_1, v12_2, v12, d0(v12_1+v12_2, v12))
    print "vol23: %s (%s, %s) of %s (%s)"%(v23_2 + v23_3, v23_2, v23_3, v23, d0(v23_2+v23_3, v23))
    print "vol123: %s (%s, %s, %s) of %s (%s)"%(v123_1 + v123_2 + v123_3, v123_1, v123_2, v123_3, v123, d0(v123_1+v123_2+v123_3, v123))
    




    
            


        
        
