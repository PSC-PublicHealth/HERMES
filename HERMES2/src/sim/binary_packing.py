#!/usr/bin/env python

########################################################################
# Copyright C 2011, Pittsburgh Supercomputing Center (PSC).            #
# =========================================================            #
#                                                                      #
# Permission to use, copy, and modify this software and its            #
# documentation without fee for personal use or non-commercial use     #
# within your organization is hereby granted, provided that the above  #
# copyright notice is preserved in all copies and that the copyright   #
# and this permission notice appear in supporting documentation.       #
# Permission to redistribute this software to other organizations or   #
# individuals is not permitted without the written permission of the   #
# Pittsburgh Supercomputing Center.  PSC makes no representations      #
# about the suitability of this software for any purpose.  It is       #
# provided "as is" without express or implied warranty.                #
#                                                                      #
########################################################################

__doc__="""binary_packing.py
Simple routines to enable saving the monitor data in a fairly compact binary form
"""
_hermes_svn_id_="$Id$"

import types
from util import isiterable

def diffPack(list):
    """
    convert a list of integers to a list of differences between
    subsequent integers.  For certain sequences this will result 
    in better compressability.
    """
    if len(list) == 0:
        return []
    # occasionally we'll get a None fed in... treat it as a 0
    last = list[0]
    if last is None:
        last = 0
    ret = [last]
    for item in list[1:]:
        if item is None:
            item = 0
        ret.append(item - last)
        last = item

    return ret

def diffUnpack(list):
    """
    undo the results of diffpack()
    """
    if len(list) == 0:
        return []
    ret = [list[0]]
    val = list[0]
    for item in list[1:]:
        val = item + val
        ret.append(val)
    return ret

def signedBerEncode(val):
    """
    binary encode an integer using a slight modification to ber encoding
    """
    # okay... right now we're not doing this "properly"
    # we're just going to save abs and a sign bit
    ret=bytearray()

    if val < 0:
        sign = 64
        val = -val
    else:
        sign = 0

    while val > 63:
        byte = val % 128
        val = val / 128
        ret.extend([byte])
    
    byte = val + sign + 128
    ret.extend([val + sign + 128])
    return ret
    
        

def signedBerDecode_consuming(val):
    """
    decode a ber encoded integer.  This version del()'s the integer off
    of the front of the bytearray if a bytearray is presented.
    """
    if not isinstance(val, bytearray):
        val = bytearray(val)

    ret = long(0)
    mult = 1
    if not len(val):
        raise Exception("zero bytes in signedBerDecode()")
    while len(val):
        byte = val[0]
        del val[0]
        if byte > 127:
            break
        ret += byte * mult
        mult *= 128
    
    if byte < 128:
        raise Exception("Insufficient bytes in signedBerDecode()")

    byte -= 128
    if byte > 63:
        sign = 1
        byte -= 64
    else:
        sign = 0

    ret += byte * mult
    if sign:
        ret = -ret

    return ret

def signedBerDecode(val, startlist = 0):
    """
    Decode a ber encoded integer.  Ideally val is a bytearray.  If not
    it will be coerced into one.  startlist provides the index into
    val where we should start decoding.  Ideally startlist is a list.
    In this case startlist[0] will be used for the initial index and
    will be updated with the next byte to decode.  Otherwise either
    startlist or startlist[0] is used for an index (hopefully it's an
    integer type) but it is not updated.
    """
    if not isiterable(startlist):
        startlist = [startlist]
    if not isinstance(startlist, types.ListType):
        startlist = [startlist[0]]

    if not isinstance(val, bytearray):
        val = bytearray(val)

    index = startlist[0]

    ret = long(0)
    mult = 1
    if len(val) <= index:
        raise Exception("zero bytes left in signedBerDecode()")
    while len(val) > index:
        byte = val[index]
        index += 1
        if byte > 127:
            break
        ret += byte * mult
        mult *= 128
    
    if byte < 128:
        raise Exception("Insufficient bytes in signedBerDecode()")

    byte -= 128
    if byte > 63:
        sign = 1
        byte -= 64
    else:
        sign = 0

    ret += byte * mult
    if sign:
        ret = -ret

    startlist[0] = index
    return ret

def encodeIntList(list):
    """
    Use signedBerEncode to encode a list of integers.  Puts an integer
    count at the front of the list so decode knows when to stop.
    """
    ret = bytearray()
    ret.extend(signedBerEncode(len(list)))

    for item in list:
        ret.extend(signedBerEncode(item))
    
    return ret

def decodeIntList(val, startlist = 0):
    """
    Decode a list of ber encoded integers.  Ideally val is a bytearray.  
    If not it will be coerced into one.  startlist provides the index 
    into val where we should start decoding.  Ideally startlist is a 
    list.  In this case startlist[0] will be used for the initial index 
    and will be updated with the next byte to decode.  Otherwise either
    startlist or startlist[0] is used for an index (hopefully it's an
    integer type) but it is not updated.
    """
    if not isiterable(startlist):
        startlist = [startlist]
    if not isinstance(startlist, types.ListType):
        startlist = [startlist[0]]

    if not isinstance(val, bytearray):
        val = bytearray(val)

    ret = []
    count = signedBerDecode(val, startlist)

    for item in xrange(count):
        ret.append(signedBerDecode(val, startlist))

    return ret

def encodeString(string):
    """
    serializes a string to go with the integer serialization tools in this
    package
    """
    s = bytearray(string, 'utf-8')
    l = signedBerEncode(len(s))
    l.extend(s)
    return l

def decodeString(val, startlist = 0):
    """
    decodes a serialized string using the same style encoding and decoding 
    as the integer tools in this package
    """
    if not isiterable(startlist):
        startlist = [startlist]
    if not isinstance(startlist, types.ListType):
        startlist = [startlist[0]]

    if not isinstance(val, bytearray):
        val = bytearray(val)
    
    l = signedBerDecode(val, startlist)
    index = startlist[0]
    s = str(val[index:index+l])
    startlist[0] = index + l

    return s

