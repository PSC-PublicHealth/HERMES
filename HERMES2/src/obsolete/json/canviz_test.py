#! /usr/bin/env python

#
# This file contains some substitution classes that can be used to
# get Canvis to run as a stand-alone text-only program for test
# purposes

##################################
# Notes-
#
##################################

_hermes_svn_id_="$Id$"

import re
from path import *
import x11colors
#import pyjd # dummy in pyjs

#from pyjamas.Canvas.GWTCanvas import GWTCanvas
#from pyjamas import Window, DOM
#from __pyjamas__ import JS

def JS(str):
	pass

class Element:
	def __init__(self,name):
		self.name= name
	def __str__(self):
		return "Element<%s>"%self.name
	def setStyle(self,style):
		debug('%s: set style %s'%(self.name,style),False)
	
class ContainerElement(Element):
	def __init__(self,name):
		Element.__init__(self,name)
		self.things= []
	def __str__(self):
		return "Container<%s>"%self.name
	def add(self,thing):
		debug("%s add %s"%(self.name,thing),False)
		self.things.append(thing)
	def getWidgetCount(self):
		return len(self.things)

class DOMClass:
	def createDiv(self):
		#debug('DOM.createDiv() called',False)
		return ContainerElement('<div>')
	def createElement(self,tag):
		debug('DOM.createElement(%s) called'%tag,False)
		return Element(tag)
	def setElementAttribute(self,element,attribute,value):
		debug('DOM.setElementAttribute(%s,%s,%s)'%(element,attribute,value),False)
	def setStyleAttribute(self,element,attribute,value):
		debug('DOM.setStyleAttribute(%s,%s,%s)'%(element,attribute,value),False)
	def setInnerHTML(self,element,value):
		debug('DOM.setInnerHTML(%s,%s)'%(element,value),False)
	def getElementById(self,idStr):
		debug('DOM.getElementById(%s)'%idStr,False)
		return ContainerElement(idStr)
	def createTextNode(self,str):
		#debug('DOM.createTextNode(%s)'%str,False)
		return Element('textNode(%s)'%str)
		
DOM= DOMClass()
		
class CanvasContext:
	def __init__(self,canvas):
		self.canvas= canvas
	def save(self):
		debug('Context.save() called',False)
	def restore(self):
		debug('Context.restore() called',False)
	def fillRect(self,x,y,width,height):
		debug("fillRect(%s,%s,%s,%s)"%(x,y,width,height),False)
	def translate(self,x,y):
		debug("translate(%s,%s)"%(x,y),False)
	def scale(self,sx,sy):
		debug("scale(%s,%s)"%(sx,sy),False)
	def beginPath(self):
		debug("beginPath")
	def moveTo(self,x,y):
		debug("moveTo(%f,%f)"%(x,y))
	def lineTo(self,x,y):
		debug("lineTo(%f,%f)"%(x,y))
	def fill(self):
		debug("fill")
	def bezierCurveTo(self,x1,y1,x2,y2,x3,y3):
		debug("bezier(%f,%f,%f,%f,%f,%f)"%(x1,y1,x2,y2,x3,y3))
		
class GWTCanvas:
	def __init__(self):
		pass
	def setStyle(self,style):
		debug('set style %s'%style,False)
	def getContext(self):
		return CanvasContext(self)
	
def escapeHTML(dirty):
	d = DOM.createDiv()
	t = DOM.createTextNode(dirty)
	d.add(t)
	#return DOM.getInnerHTML(d)
	debug('escapeHTML returns <%s>'%dirty)
	return dirty

def debug(str, escape=True):
	"""
	function debug(str, escape) {
		str = String(str);
		if (Object.isUndefined(escape)) {
			escape = true;
		}
		if (escape) {
			str = str.escapeHTML();
		}
		$('debug_output').innerHTML += '&raquo;' + str + '&laquo;<br />';
	}
	"""
	#if escape: str= escapeHTML(str)
	print '###DEBUG: '+str

def ajaxSimulateLoad(url,urlParams,canviz):
	debug('Ajax Load <%s> <%s>'%(url,urlParams),False)
	canviz.parse("""
# Generated Tue Aug 21 10:21:20 GMT 2007 by dot - Graphviz version 2.15.20070819.0440 (Tue Aug 21 09:56:32 GMT 2007)
#
# 
# real	0m0.109s
# user	0m0.082s
# sys	0m0.022s

digraph G {
	node [label="\N"];
	graph [bb="0,0,308,250",
		_draw_="c 5 -white C 5 -white P 4 0 0 0 250 308 250 308 0 ",
		xdotversion="1.2"];
	subgraph cluster_0 {
		graph [label="hello world",
			color=hotpink,
			lp="229,153",
			bb="158,16,300,165",
			_ldraw_="F 14.000000 11 -Times-Roman c 5 -black T 229 148 0 82 11 -hello world ",
			_draw_="c 7 -hotpink p 4 158 16 158 165 300 165 300 16 ",
			xdotversion=""];
		a [pos="193,114", width="0.75", height="0.50", _draw_="c 5 -black e 193 114 27 18 ", _ldraw_="F 14.000000 11 -Times-Roman c 5 -black T 193 109 0 9 1 -a "];
		b [pos="193,42", width="0.75", height="0.50", _draw_="c 5 -black e 193 42 27 18 ", _ldraw_="F 14.000000 11 -Times-Roman c 5 -black T 193 37 0 9 1 -b "];
		c [pos="265,42", width="0.75", height="0.50", _draw_="c 5 -black e 265 42 27 18 ", _ldraw_="F 14.000000 11 -Times-Roman c 5 -black T 265 37 0 8 1 -c "];
		a -> b [pos="e,193,60 193,96 193,88 193,79 193,70", _draw_="c 5 -black B 4 193 96 193 88 193 79 193 70 ", _hdraw_="S 5 -solid S 15 -setlinewidth(1) c 5 -black C 5 -black P 3 197 70 193 60 190 70 "];
		a -> c [pos="e,250,57 208,99 218,89 231,76 243,64", _draw_="c 5 -black B 4 208 99 218 89 231 76 243 64 ", _hdraw_="S 5 -solid S 15 -setlinewidth(1) c 5 -black C 5 -black P 3 245 67 250 57 240 62 "];
	}
	subgraph cluster_1 {
		graph [label=MSDOT,
			color=purple,
			style=dashed,
			lp="79,230",
			bb="8,16,150,242",
			_ldraw_="F 14.000000 11 -Times-Roman c 5 -black T 79 225 0 57 5 -MSDOT ",
			_draw_="S 6 -dashed c 6 -purple p 4 8 16 8 242 150 242 150 16 ",
			xdotversion=""];
		x [pos="79,191", width="0.75", height="0.50", _draw_="c 5 -black e 79 191 27 18 ", _ldraw_="F 14.000000 11 -Times-Roman c 5 -black T 79 186 0 8 1 -x "];
		y [pos="115,114", width="0.75", height="0.50", _draw_="c 5 -black e 115 114 27 18 ", _ldraw_="F 14.000000 11 -Times-Roman c 5 -black T 115 109 0 8 1 -y "];
		z [pos="43,42", width="0.75", height="0.50", _draw_="c 5 -black e 43 42 27 18 ", _ldraw_="F 14.000000 11 -Times-Roman c 5 -black T 43 37 0 8 1 -z "];
		q [pos="115,42", width="0.75", height="0.50", _draw_="c 5 -black e 115 42 27 18 ", _ldraw_="F 14.000000 11 -Times-Roman c 5 -black T 115 37 0 9 1 -q "];
		x -> y [pos="e,107,131 87,174 92,164 97,151 103,140", _draw_="c 5 -black B 4 87 174 92 164 97 151 103 140 ", _hdraw_="S 5 -solid S 15 -setlinewidth(1) c 5 -black C 5 -black P 3 106 142 107 131 100 139 "];
		x -> z [pos="e,47,60 75,173 69,147 57,100 49,70", _draw_="c 5 -black B 4 75 173 69 147 57 100 49 70 ", _hdraw_="S 5 -solid S 15 -setlinewidth(1) c 5 -black C 5 -black P 3 52 69 47 60 46 70 "];
		y -> z [pos="e,58,57 100,99 90,89 77,76 65,64", _draw_="c 5 -black B 4 100 99 90 89 77 76 65 64 ", _hdraw_="S 5 -solid S 15 -setlinewidth(1) c 5 -black C 5 -black P 3 68 62 58 57 63 67 "];
		y -> q [pos="e,115,60 115,96 115,88 115,79 115,70", _draw_="c 5 -black B 4 115 96 115 88 115 79 115 70 ", _hdraw_="S 5 -solid S 15 -setlinewidth(1) c 5 -black C 5 -black P 3 119 70 115 60 112 70 "];
	}
	top [pos="189,191", width="0.75", height="0.50", _draw_="c 5 -black e 189 191 27 18 ", _ldraw_="F 14.000000 11 -Times-Roman c 5 -black T 189 186 0 25 3 -top "];
	top -> a [pos="e,192,132 190,173 191,164 191,152 191,142", _draw_="c 5 -black B 4 190 173 191 164 191 152 191 142 ", _hdraw_="S 5 -solid S 15 -setlinewidth(1) c 5 -black C 5 -black P 3 194 142 192 132 188 142 "];
	top -> y [pos="e,126,131 170,178 164,174 159,169 154,165 146,157 139,147 132,139", _draw_="c 5 -black B 7 170 178 164 174 159 169 154 165 146 157 139 147 132 139 ", _hdraw_="S 5 -solid S 15 -setlinewidth(1) c 5 -black C 5 -black P 3 135 137 126 131 129 141 "];
	y -> b [pos="e,177,57 131,99 142,89 157,75 169,64", _draw_="c 5 -black B 4 131 99 142 89 157 75 169 64 ", _hdraw_="S 5 -solid S 15 -setlinewidth(1) c 5 -black C 5 -black P 3 172 66 177 57 167 61 "];
}
	""")

def main():
	c= Canviz('foo')
	c.load('/foo/bar/baz','blrfl')
