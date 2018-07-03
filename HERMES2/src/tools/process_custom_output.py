
import os.path
import sys

try:
    cwd = os.path.dirname(__file__)
    if cwd not in sys.path:
        sys.path.append(cwd)

    # also need the directory above
    updir = os.path.join(cwd, '..')
    if updir not in sys.path:
        sys.path.append(updir)
except:
    pass


import HermesOutput
import sys
import pickle


import util
import noteholder
import hermes


def main():
    if len(sys.argv) < 3 or sys.argv[1][0] == '-':
        print "%s help:"%sys.argv[0]
        print "process a custom output script against a hermes output file"
        print "usage:"
        print "python %s <outputFile> <customOutputCSV>"%sys.argv[0]
        return

    outputFileName = sys.argv[1]
    outputTemplateFile = sys.argv[2]

    with open(outputFileName, 'r') as f:
        ho = pickle.load(f)

    ho.customOutputs = [outputTemplateFile]
    ho.writeOutputs()




if __name__=="__main__":
    main()
