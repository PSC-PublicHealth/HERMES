_hermes_svn_id_="$Id$"

from binary_packing import *
import sys


def parseMonitorsCompressed(data):
    i = [0]
    vaxIn = {}

    while(1):
        wh = decodeString(data, i)
        if 0 == len(wh):
            break
        print "warehouse: %s"%wh

        ts = decodeIntList(data, i)
        ts = diffUnpack(diffUnpack(ts))
        ts = map((lambda t: float(t) / 256), ts)
        print "    time series: %s"%ts
        
        while(1):
            vaxId = signedBerDecode(data, i)
            if 0 == vaxId:
                break
            if vaxId not in vaxIn:
                vaxIn[vaxId] = decodeString(data, i)
            vc = decodeIntList(data,i)
            vc = diffUnpack(vc)
            print "    %s: %s"%(vaxIn[vaxId], vc)
            

def main():
    with open(sys.argv[1], "rb") as f:
        bits = f.read()
    parseMonitorsCompressed(bits)

if __name__=="__main__":
    main()
