
import sys
import gv
import random
import math


def addNode(g, parent, size, label):
    n = gv.node(g, '%s'%label)
    gv.setv(n, 'color', 'black')
    gv.setv(n, 'shape', 'oval')
#    gv.setv(n, 'label', label)
    gv.setv(n, 'width', '%3.6f'%(size))
    gv.setv(n, 'height', '%3.6f'%(size))

    if parent is not None:
        edge = gv.edge(parent, n)
        gv.setv(edge, 'penwidth', '%3.4f'%(size))
        gv.setv(edge, 'arrowsize', '%3.4f'%(0.2*size))

    return n


def buildGraph(levels):
    baseSize = 20.0

    g = gv.digraph('g')
    gv.setv(gv.protonode(g),'style','filled')
    gv.setv(gv.protonode(g),'rank','min')
    #gv.setv(g,'overlap','prism')
    gv.setv(g,'mindist','0.1')
    gv.setv(g,'clusterrank','local')
    gv.setv(g,'compound','true')

    nodeNum = 0

    nodelist = []

    nodelist.append([])
    for i in xrange(levels[0]):
        n = addNode(g, None, baseSize, '%04d'%nodeNum)
        nodeNum += 1
        nodelist[0].append(n)



    for l in xrange(1, len(levels)):
        nodelist.append([])
        for parent_n in nodelist[l-1]:
            n = addNode(g, parent_n, baseSize / math.pow(l+1, 1.5), '%04d'%nodeNum)
            nodeNum += 1
            nodelist[l].append(n)
            
        r = -1
        for i in xrange(levels[l-1], levels[l]):
            if 1:
                r = random.randint(0, levels[l-1]-1)
            else:
                r += 1
                if r >= levels[l-1]:
                    r = 0
            parent_n = nodelist[l-1][r]
            n = addNode(g, parent_n, baseSize / math.pow(l+1, 1.5), '%04d'%nodeNum)
            nodeNum += 1
            nodelist[l].append(n)


        
    gv.layout(g, 'circo')
    gv.render(g, 'svg', 'bushy.svg')


def main():
    buildGraph([1,6,37,774, 25000])
    



if __name__=="__main__":
    main()
