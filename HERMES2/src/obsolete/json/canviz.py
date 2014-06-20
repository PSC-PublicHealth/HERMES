#! /usr/bin/env python

#
# This Python code is intended to be compiled with the PyJamas
# python-to-javascript compiler.  It is a GraphVis 'xdot' format
# display tool.  The algorithm is largely a Python transcoding 
# of the Canviz javascript utility from ryandesign.com 
# (see http://www.canviz.org ).  Some performance optimizations
# have been made, in some cases involving loss of functionality.
#

#/*
# * This file is part of Canviz. See http://www.canviz.org/
# * $Id$
# */

##################################
# Notes-
#
##################################

_hermes_svn_id_="$Id$"

import re,math
import x11colors

from pyjamas.ui.HTML import HTML
from pyjamas.ui.Image import Image
from pyjamas.ui import Event
from pyjamas.HTTPRequest import HTTPRequest
from pyjamas import Window, DOM
from __pyjamas__ import JS

from canvizutil import getTotalOffsets, CanvasContext, CanvizCanvas, escapeHTML, BoundingBox

class CanvizTokenizer:
	"""
	This class is constructed with a string.  It hangs on to the string and pulls tokens from the
	front according to several expected syntax patterns.
	"""
	def __init__(self,str):
		"""
		The parameter is the string which will be pulled apart into tokens.
		"""
		self.str= str
		#self.tokenRe= re.compile('^(\S+)\s*')
		self.tokenRe= re.compile('^\s*(\S+)\s*')
	def takeChars(self,num=1):
		"""
		Return one or more tokens.  If 1 token is requested it is returned as is; two or more tokens
		are returned as a list.  When the string runs out of tokens, False is returned.
		"""	
		tokens= []
		while num:
			num -= 1
			matches= self.tokenRe.match(self.str)
			if matches:
				self.str= self.str[len(matches.group(0)):]
				tokens.append(matches.group(1))
			else:
				tokens.append(False)
		if len(tokens)==1: return tokens[0]
		else: return tokens
		
	def takeInt(self,num=1):
		"""
		Parse the next token in the string as an integer and return it.
		"""
		if num==1:
			t= self.takeChars()
			return int(t)
			#return JS("""Number(t)""")
		else:
			tokens= self.takeChars(num)
			return [int(t) for t in tokens]
			#return [JS("""Number(t)""") for t in tokens]
		
	def takeFloat(self,num=1):
		"""
		Parse the next token in the string as a float and return it.
		"""
		if num==1:
			t= self.takeChars()
			return float(t)
			#return JS("""Number(t)""")
		else:
			tokens= self.takeChars(num)
			return [float(t) for t in tokens]
			#return [JS("""Number(t)""") for t in tokens]
		
	def takeString(self):
		"""
		The input string is expected to specify a string in the format 'nnn -charcharchar...'
		where nnn is a text representation of the integer number of characters expected after the
		dash.  This function clips those characters off the input string and returns the result
		as a string.
		"""
		byteCount= int(self.takeChars())
		charCount= 0
		charCode= 0
		if self.str[0] != '-': return False
		charCount=byteCount # because python apparently handles strings more sensibly than javascript
		str= self.str[1:charCount+1]
		self.str= self.str[charCount+1:]
		return str
			
class CanvizEntity:
	"""
	This is the base class for geometrical objects in a Canviz graph.  Nodes, edges, images and graphs are
	all derived from this class.  Instances of this class or derived classes are created and strung together
	as the Canviz instance parses an xdot string.
	"""
	entityCounter= 0
	def __init__(self,defaultAttrHashName, name, canviz, rootGraph, parentGraph, immediateGraph):
		"""
		Parameters are:
		
		   defaultAttrHashName: attribute set to use; this value is set by the derived class
		   name: entity name
		   canviz: owning instance of Canviz
		   rootGraph: the parent graph, or None for the top level container
		   parentGraph: the immediate parent, or None for the top level container
		   immediateGraph: the current graph
		},
		"""
		self.defaultAttrHashName= defaultAttrHashName
		self.name= name
		self.canviz= canviz
		self.rootGraph= rootGraph
		self.parentGraph= parentGraph
		self.immediateGraph= immediateGraph
		self.attrs= {}
		self.drawAttrs= {}
		self.bbRect= None
		self.escStringMatchRe= None
		self.posRe= re.compile(r'([0-9.]+),([0-9.]+)')
		self.textRe= re.compile(r'^\s*$')
		self.plusRe= re.compile(r' ( +)')
		self.setLineWidthRe= re.compile(r'^setlinewidth\((.*)\)$')
		self.rgbRe= re.compile(r'^#(?:[0-9a-f]{2}\s*){3,4}$')
		self.hsvRe= re.compile(r'^(\d+(?:\.\d+)?)[\s,]+(\d+(?:\.\d+)?)[\s,]+(\d+(?:\.\d+)?)$')
		self.namedColorRe= re.compile(r'^\/(.*)\/(.*)$')
		self.shortNamedColorRe= re.compile(r'^\/(.*)$')
		CanvizEntity.entityCounter += 1
	def initBB(self):
		"""
		Calculate and record the bounding box of this instance.  The xdot format provides this info
		in a convenient form.
		"""
		matches= self.posRe.search(self.getAttr('pos'))
		if matches:
			x= float(matches.group(1))
			y= float(matches.group(2))
			h= 72.0*float(self.getAttr('height'))
			w= 72.0*float(self.getAttr('width'))
			self.bbRect= BoundingBox(x-w/2,y-h/2,x+w/2,y+h/2)
		else:
			self.canviz.debug('Failed to parse entity pos string <%s>'%self.getAttr('pos'))
			
	def getAttr(self,attrName,escString=False):
		"""
		Look up the named attribute for this entity.  escString is a flag indicating whether
		certain text elements in the value are to be replaced with values specific to this
		CanvizEntity instance.
		"""
		attrValue= None
		if self.attrs.has_key(attrName): attrValue= self.attrs[attrName]
		else:
			graph= self.parentGraph
			while graph is not None:
				if graph.attrs.has_key(self.defaultAttrHashName):
					attrValue= graph[self.defaultAttrHashName]
					break
				else:
					graph= graph.parentGraph
		if attrValue is not None and escString and self.escStringMatchRe:
			def subFun(matchobj):
				match= matchobj.group(0)
				p1= matchobj.group(1)
				if p1=='N': return match
				elif p1=='E': return self.name
				elif p1=='T': return self.tailNode
				elif p1=='H': return self.headNode
				elif p1=='G': return self.immediateGraph.name
				elif p1=='L': return self.getAttr('label',True)
				else: return match
			attrValue= escStringMatchRe.sub(attrValue, subFun)
		return attrValue
	def draw(self,ctx,redrawCanvasOnly):
		"""
		Draw the element into the given context, based on pre-parsed attributes. 
		"""
		if not self.bbRect:
			self.initBB()
		if not redrawCanvasOnly:
			pass
			#self.self.initBB()
			#bbDivE= DOM.createDiv()
			#self.canviz.elementsE.appendChild(bbDivE)
		#self.bbRect.draw(ctx)
		if self.bbRect is not None and not self.bbRect.intersects( ctx.getProjectionBBox() ):
			#self.canviz.debug('skip %s'%self.name)
			return
		for dA_name,dA_value in self.drawAttrs.items():
			command = dA_value
			#self.canviz.debug(command)
			tokenizer = CanvizTokenizer(command)
			token = tokenizer.takeChars()
			if token:
				dashStyle = 'solid'
				#ctx.save()
				while token: 
					#self.canviz.debug('processing token ' + token)
					path= False
					if token in ['E','e']:
						filled= ('E'==token)
						cx= tokenizer.takeFloat()
						cy= tokenizer.takeFloat()
						rx= tokenizer.takeFloat()
						ry= tokenizer.takeFloat()
						if not self.replaceTinyThingsWithBBox(ctx):
							ctx.beginPath()
							path= True
							# This logic is grafted in from the associated Path module,
							# which is otherwise unnecessary with CanvizCanvas							
							KAPPA= 0.5522847498
							ctx.moveTo(cx,cy-ry)
							ctx.cubicCurveTo(cx+KAPPA*rx, cy-ry, cx+rx, cy-KAPPA*ry, cx+rx, cy)
							ctx.cubicCurveTo(cx+rx, cy+KAPPA*ry, cx+KAPPA*rx, cy+ry, cx, cy+ry)
							ctx.cubicCurveTo(cx-KAPPA*rx, cy+ry, cx-rx, cy+KAPPA*ry, cx-rx, cy)
							ctx.cubicCurveTo(cx-rx, cy-KAPPA*ry, cx-KAPPA*rx, cy-ry, cx, cy-ry)
					elif token in ['P','p','L']:
						filled= ('P'==token)
						closed= ('L'!=token)
						numPoints= tokenizer.takeInt()
						tokens= tokenizer.takeFloat(2*numPoints)
						if not self.replaceTinyThingsWithBBox(ctx):
							ctx.beginPath()
							path= True
							ctx.moveTo(tokens[0],tokens[1])
							for i in xrange(2,2*numPoints,2):
								ctx.lineTo(tokens[i], tokens[i+1])
							if closed:
								ctx.closePath()
					elif token in ['B','b']:
						filled = ('b' == token)
						numPoints = tokenizer.takeInt()
						tokens = tokenizer.takeFloat(2 * numPoints)
						if not self.replaceTinyThingsWithBBox(ctx):
							ctx.beginPath()
							path = True
							ctx.moveTo(tokens[0],tokens[1])
							for i in xrange(2,2*numPoints,6):
								ctx.cubicCurveTo(tokens[i], tokens[i+1],
												 tokens[i+2],tokens[i+3],
												 tokens[i+4],tokens[i+5])
					elif token=='I':
						l = tokenizer.takeFloat()
						b = tokenizer.takeFloat()
						w = tokenizer.takeFloat()
						h = tokenizer.takeFloat()
						src = tokenizer.takeString()
						if not self.replaceTinyThingsWithBBox(ctx):
							if not self.canviz.images.has_key(src):
								self.canviz.images[src] = CanvizImage(self.canviz, src)
							self.canviz.images[src].draw(ctx, l, b - h, w, h)
					elif token=='T':
						scaledFontSize= abs(fontSize*ctx.t11) # remember, t11 is negative
						x= tokenizer.takeFloat()
						y= tokenizer.takeFloat()
						textAlign = tokenizer.takeInt()
						textWidth= tokenizer.takeFloat()*ctx.t00
						str = tokenizer.takeString()
						# Text has a lot of overhead.  If the projected text is tiny, we'll just skip it-
						# the user can't see it and probably can't intentionally click on it.  Of course,
						# we will also skip the text if it projects outside the window.
						tuple= ctx.getClippedProjectedCoords(x,y)
						if tuple is not None and scaledFontSize >= 1.0:
							lRaw,tRaw= tuple
							l = self.canviz.offsetBaseLeft + int(round(lRaw))
							t = self.canviz.offsetBaseTop + int(round(tRaw))
							textWidth = int(round(textWidth))
							#self.canviz.debug("text <%s>: %s %s %s %s -> %s %s -> %s %s -> %s %s"%\
							#					(str,ctx.t00,ctx.t11,ctx.t02,ctx.t12,x,y,lRaw,tRaw,l,t))
							if not redrawCanvasOnly and not self.textRe.match(str):
								str = escapeHTML(str)
								while True:
									matches= self.plusRe.match(str)
									if matches:
										spaces = ' '
										for i in xrange(len(matches.group(1))):
											spaces += '&nbsp;'
										str= self.plusRe.sub(spaces,str)
									else:
										break
								href = (self.getAttr('URL', True) or self.getAttr('href', True))
								if href:
									target = self.getAttr('target', True) 
									if target is None: target= '_self'
									tooltip = self.getAttr('tooltip', True) 
									if tooltip is None: tooltip= self.getAttr('label', True)
									text= DOM.createElement('a')
									DOM.setElemAttribute(text,'href',href)
									DOM.setElemAttribute(text,'target',target)
									DOM.setElemAttribute(text,'title',tooltip)
									for attrName in ['onclick', 'onmousedown', 'onmouseup', 'onmouseover', 
													'onmousemove', 'onmouseout']:
										attrValue = self.getAttr(attrName, True)
										if attrValue:
											DOM.setElemAttribute(text,attrName,attrValue)
									DOM.setStyleAttribute(text,'textDecoration','none')
								else:
									text = DOM.createElement('span')
								DOM.setInnerHTML(text,str)
								DOM.setStyleAttribute(text,'fontSize',"%dpx"%int(round(scaledFontSize)))
								DOM.setStyleAttribute(text,'fontFamily',fontFamily)
								DOM.setStyleAttribute(text,'color',strokeColor['textColor'])
								DOM.setStyleAttribute(text,'position','absolute')
								if textAlign==-1: tA= 'left'
								elif textAlign==1: tA= 'right'
								else: tA= 'center'
								DOM.setStyleAttribute(text,'textAlign',tA)
								DOM.setStyleAttribute(text,'left','%dpx'%(l-(1+textAlign)*textWidth))
								DOM.setStyleAttribute(text,'top','%dpx'%(t-scaledFontSize))
								DOM.setStyleAttribute(text,'width','%dpx'%(2*textWidth))
								if 1 != strokeColor['opacity']: 
									DOM.setElemAttribute(text,'opacity',strokeColor['opacity'])
								self.canviz.elementsE.appendChild(text)
						else:
							#self.canviz.debug('skipped text %s'%str)
							pass
					elif token in ['C','c']:
						fill = ('C' == token)
						color = self.parseColor(tokenizer.takeString())
						if fill:
							fillColor = color
							ctx.setFillStyle(color['canvasColor'])
						else:
							strokeColor = color
							ctx.setStrokeStyle(color['canvasColor'])
							
					elif token=='F':
						fontSize = tokenizer.takeFloat()
						fontFamily = tokenizer.takeString()
						if fontFamily=='Times-Roman':
							fontFamily = 'Times New Roman'
						elif fontFamily=='Courier':
							fontFamily = 'Courier New'
						elif fontFamily=='Helvetica':
							fontFamily = 'Arial'
						else:
							pass
					elif token=='S':
						style = tokenizer.takeString()
						if style in ['solid','filled']:
							pass
						elif style in ['dashed','dotted']:
							dashStyle= style
						elif style=='bold':
							ctx.setLineWidth(2.0)
						else:
							matches= self.setLineWidthRe.match(style)
							if matches:
								ctx.setLineWidth(float(matches.group(1)))
							else:
								self.canviz.debug('unknown style ' + style)
					else:
						self.canviz.debug('unknown token ' + token)
						return
					if path:
						#self.canviz.debug('about to draw path')
						self.canviz.drawPath(ctx, filled, dashStyle)
						path = False
					#self.canviz.debug('Ready for new token')
					token = tokenizer.takeChars()
					
	def replaceTinyThingsWithBBox(self,ctx):
		"""
		If the current bounding box is less than 2 pixels in both dimensions, this
		function will draw the bounding box and return True.  Otherwise, it 
		returns False.  Since many element types are drawn with splines, cubic curves
		or long polylines, this can be a significant economy for small elements.
		"""
		if self.bbRect is None:
			return False
		else:
			h= self.bbRect.t - self.bbRect.b
			w= self.bbRect.r - self.bbRect.l
			if abs(w*ctx.t00)<2.0 and abs(h*ctx.t11)<2.0:
				self.bbRect.drawFilled(ctx)
				return True
			else:
				return False
					
	def parseColor(self,color):
		"""
		The input parameter 'color' is a string representation of a color, in any of a number
		of formats.  The output is a dictionary of the form 
		{'textColor':'#000000', 'canvasColor':'#000000', 'opacity':1}
		"""
		parsedColor = {'opacity': 1}
		# rgb/rgba
		if self.rgbRe.match(color):
			return self.canviz.parseHexColor(color)
		# hsv
		matches = self.hsvRe.match(color)
		if matches:
			clr= self.canviz.hsvToRgbColor(float(matches.group(1)), float(matches.group(2)), float(matches.group(3)))
			parsedColor['canvasColor'] = clr
			parsedColor['textColor']= clr
			return parsedColor
		# named color
		colorScheme = self.getAttr('colorscheme')
		if not colorScheme: colorScheme= 'X11'
		colorName = color
		matches = self.namedColorRe.match(color)
		if matches:
			if len(matches.group(1)): colorScheme = matches.group(1)
			colorName = matches.group(2)
		else:
			matches = self.shortNamedColorRe.match(color)
			if matches:
				colorScheme = 'X11'
				colorName = matches.group(1)
		colorName = colorName.lower()
		colorSchemeName = colorScheme.lower()
		if Canviz.colors.has_key(colorSchemeName):
			colorSchemeData = Canviz.colors[colorSchemeName]
			if colorSchemeData.has_key(colorName):
				colorData = colorSchemeData[colorName]
				return self.canviz.parseHexColor('#' + colorData)
		else:
			colorSchemeData= None
		fbColorSchemeData= Canviz.colors['fallback']
		if fbColorSchemeData.has_key(colorName):
			colorData = fbColorSchemeData[colorName];
			return self.canviz.parseHexColor('#' + colorData)
		if not colorSchemeData:
			self.canviz.debug('unknown color scheme ' + colorScheme)
		# unknown
		self.canviz.debug('unknown color ' + color + '; color scheme is ' + colorScheme)
		parsedColor['canvasColor']= '#000000'
		parsedColor['textColor']= '#000000'
		return parsedColor

class CanvizNode(CanvizEntity):
	def __init__(self,name,canviz,rootGraph,parentGraph):
		"""
		Instances of this class represent graph nodes.
		"""
		CanvizEntity.__init__(self,'nodeAttrs',name,canviz,rootGraph,parentGraph,parentGraph)
		self.escStringMatchRe= re.compile(r'\\([NGL])')

class CanvizEdge(CanvizEntity):
	def __init__(self,name,canviz,rootGraph,parentGraph,tailNode,headNode):
		"""
		Instances of this class represent graph edges.
		"""
		CanvizEntity.__init__(self,'edgeAttrs',name,canviz,rootGraph,parentGraph,parentGraph)
		self.tailNode= tailNode
		self.headNode= headNode
		self.escapeStringMatchRe= re.compile(r'\\([EGTHL])')
	def initBB(self):
		"""
		Calculate a bounding box from the spline control points given in the edge's "pos" attribute
		"""
		posStr= self.getAttr('pos')
		try:
			posBlocks= posStr.split()
			bl= posBlocks[0]
			if bl[:2] in ['e,','s,']: # usually but not always present
				bl= bl[2:]
			posPairs= bl.split()
			words= posPairs[0].split(',')
			x= float(words[0])
			y= float(words[1])
			xmin= x
			xmax= x
			ymin= y
			ymax= y
			for bl in posBlocks[1:]:
				if bl[:2] in ['e,','s,']: # usually but not always present
					bl= bl[2:]
				words= bl.split(',')
				x= float(words[0])
				y= float(words[1])
				if x<xmin: xmin= x
				if x>xmax: xmax= x
				if y<ymin: ymin= y
				if y>ymax: ymax= y
			self.bbRect= BoundingBox(xmin,ymin,xmax,ymax)
		except:
			self.canviz.debug('Failed to parse edge pos string <%s>'%self.getAttr('pos'))
		
class CanvizGraph(CanvizEntity):
	"""
	Instances of this class represent graphs or subgraphs.  
	"""
	def __init__(self,name,canviz,rootGraph=None,parentGraph=None):
		"""
		Instances of this class represent graphs or subgraphs.
		"""
		CanvizEntity.__init__(self,'attrs',name,canviz,rootGraph,parentGraph,self)
		self.nodeAttrs= {}
		self.edgeAttrs= {}
		self.nodes= []
		self.edges= []
		self.subgraphs= []
		self.escStringMatchRe= re.compile(r'\\([GL])')
	def initBB(self):
		"""
		Initialize the graph bounding box if information is available.  xdot provides the special
		attribute 'bb' for this purpose.  Embedded sub-graphs may have empty bb strings; they
		are left without bounding boxes.
		"""
		coordStr= self.getAttr('bb')
		if coordStr is not None and coordStr != '':
			coordStr= coordStr.strip() 
			try:
				coords= [int(s) for s in coordStr.split(',')]
				self.bbRect= BoundingBox(int(coords[0]), int(coords[1]),
										int(coords[2]), int(coords[3]))
			except:
				self.canviz.debug('Failed to parse graph bounding box <%s>'%self.getAttr('bb'))
	def draw(self,ctx,redrawCanvasOnly):
		"""
		Draw the graph, recursively descending into the draw routines of all the elements it contains.
		ctx is a drawing context; redrawCanvasOnly is a flag to indicate that text elements should not
		be drawn.
		"""
		CanvizEntity.draw(self,ctx,redrawCanvasOnly)
		for tp in [self.subgraphs, self.nodes, self.edges]:
			for entity in tp:
				entity.draw(ctx,redrawCanvasOnly)

class CanvizImage:
	"""
	Instances of this class represent images to be drawn as graph elements.
	"""
	def __init__(self,canviz,src):
		"""
		Initialization parameters:
		
		  canviz: the owning Canviz instance
		  src: the source URL (including parameters) from which the image is to be loaded
		"""
		self.canviz= canviz
		self.src= src
		self.canviz.numImages += 1
		self.img= Image()
		self.img.addLoadListener(self)
		self.loaded= False
		self.loadFinished= False
		# The next couple of lines are from pyjamas.Canvas.ImageLoader; they
		# serve to get the image loaded even though the image element is not
		# linked into the DOM.
		DOM.setEventListener(self.img.getElement(),self.img)
		DOM.sinkEvents(self.img.getElement(), Event.ONLOAD|Event.ONERROR)
		self.canviz.reportImageLoadStarted(self)
		self.img.setUrl(self.canviz.imagePath+src)
	def onLoad(self,sender=None):
		"""
		Callback method of the LoadListener interface; called asynchronously when
		a successful load has completed.
		"""
		#Window.alert('onLoad was called for %s'%self.src)
		self.loaded= True
		self.loadFinished= True
		self.canviz.reportImageLoadFinished(self)
	def onError(self):
		"""
		Callback method of the LoadListener interface; called asynchronously when
		a successful load has ended in failure.
		"""
		#Window.alert('onError was called for %s'%self.src)
		self.loaded= False
		self.loadFinished= True
		self.canviz.reportImageLoadFinished(self)
	
	def draw(self,l,t,w,h):
		"""
		Draw the image if it is available, or a surrogate 'broken image' glyph if it is not.
		"""
		if self.loaded:
			# The bad news is that many parts of canvas.drawImage(...) seem to be broken;
			# we will use the unbroken parts and our own transformation to get the image 
			# into place.  This should probably be done by the drawing context, but that
			# is not yet implemented.
			#
			# We want the image to come out right side up, so we have to briefly flip the coordinate
			# system back to its stupid upside down default scaling.
			rawW= self.img.getElement().width
			rawH= self.img.getElement().height

			self.canviz.ctx.save()
			xStretch= (1.0*w)/rawW
			yStretch= (1.0*h)/rawH
			
			self.canviz.ctx.translate(l, -t)
			self.canviz.ctx.transform(xStretch, 0.0, 
									  0.0,     -yStretch,   0.0, 2.0*t+(rawH*yStretch))
			
			self.canviz.ctx.drawImage(self.img.getElement(),0,0)
			self.canviz.ctx.restore()
		else:
			self.drawBrokenImage(l,t,w,h)
	def drawBrokenImage(self,l,t,w,h):
		"""
		Draw a 'broken image' glyph of the appropriate size and location
		"""
		self.canviz.ctx.save()
		self.canviz.ctx.setStrokeStyle('#f00')
		self.canviz.ctx.setLineWidth(1)
		self.canviz.ctx.beginPath()
		self.canviz.ctx.moveTo(l,t)
		self.canviz.ctx.lineTo(l+w,t+h)
		self.canviz.ctx.moveTo(l+w,t)
		self.canviz.ctx.lineTo(l,t+h)
		self.canviz.ctx.stroke()
		self.canviz.ctx.strokeRect(l,t,w,h)
		self.canviz.ctx.restore()

class Canviz:
	"""
	This class embodies the drawing environment.  It holds the current GraphVis graph description in
	xdot format and the Canvas element into which it is drawn.
	"""
	maxXdotVersion= '1.2'
	colors= {'fallback':{ 'black':'000000','lightgrey':'d3d3d3','white':'ffffff'},
			 'x11':x11colors.x11Colors}
	canvasCounter= 0
	def __init__(self,containerOrContainerName,dotString,width,height,dbgElementName=None):
		"""
		Create the canviz drawing environment and associated canvas.  The parameters are:
		
		  containerOrContainerName: either a PYJS DIV element or the ID of such an element.  The canvas will be
		                            inserted into this DIV.
		  dotString: an xdot-syntax GraphVis graph description, or None
		  width, heigh: integer width and height of the canvas.  (These are not taken from the container because
		                of sizing issues arising from embeding the container within other widgets.
		  dbgElementName: the ID string of a widget into which debugging text will be written, or None to supress
		                  debugging output.
		"""
		self.dotString= dotString
		if dbgElementName is None:
			self.dbgElementE= None
			self.dbgElementInitialContents= None
		else:
			self.dbgElementE= DOM.getElementById(dbgElementName)
			self.dbgElementInitialContents= DOM.getInnerHTML(self.dbgElementE)
		self.canvas= CanvizCanvas(self.dbgElementE)
		self.canvas.resize(width,height)
		Canviz.canvasCounter += 1
		self.canvas.setID('canviz_canvas_%d'%Canviz.canvasCounter)
		self.elementsE= DOM.createDiv()
		self.containerE= DOM.getElementById(containerOrContainerName)
		if self.containerE is None:
			self.containerE= containerOrContainerName.getElement()
		ctrE= self.containerE
		cnvE= self.canvas.getCanvasElement()
		DOM.setAttribute(cnvE,'className','canviz')
		self.containerE.appendChild(cnvE)
		self.containerE.appendChild(self.elementsE)
		self.ctx= None
		self.offsetBaseTop,self.offsetBaseLeft= None,None
		self.scaleSet= False
		self.redrawInProgress= False
		self.bb= BoundingBox(0,0,0,0)
		self.viewCtrX= 0.0
		self.viewCtrY= 0.0
		self.padding= 8
		self.dashLength= 6
		self.dotSpacing= 4
		self.graphs= []
		self.images= {}
		self.numImages= 0
		self.numImagesFinished= 0
		self.imagePath= "" # base path for image URLs
		self.redrawsPendingCount= 0
		self.loadURL= None # If a load of xdot from an http request is in progress, this is the URL
		idMatch= '([a-zA-Z\u0080-\uFFFF_][0-9a-zA-Z\u0080-\uFFFF_]*|-?(?:\\.\\d+|\\d+(?:\\.\\d*)?)|"(?:\\\\"|[^"])*"|<(?:<[^>]*>|[^<>]+?)+>)'
		nodeIdMatch= idMatch+r'(?::' + idMatch + ')?(?::' + idMatch + ')?'
		self.graphMatchRe= re.compile('^(strict\\s+)?(graph|digraph)(?:\\s+' + idMatch + ')?\\s*{$',re.IGNORECASE)
		self.subgraphMatchRe= re.compile('^(?:subgraph\\s+)?' + idMatch + '?\\s*{$',re.IGNORECASE)
		self.nodeMatchRe= re.compile('^(' + nodeIdMatch + ')\\s+\\[(.+)\\];$')
		self.edgeMatchRe= re.compile('^(' + nodeIdMatch + '\\s*-[->]\\s*' + nodeIdMatch + ')\\s+\\[(.+)\\];$')
		self.attrMatchRe= re.compile('^' + idMatch + '=' + idMatch + '(?:[,\\s]+|$)')
		self.drawAttrMatchRe= re.compile('^_.*draw_$')
		self.sizeRe= re.compile('^(\d+|\d*(?:\.\d+)),\s*(\d+|\d*(?:\.\d+))(!?)$')
		self.unescapeRe= re.compile('^"(.*)"$')
		self.unescapeReplaceRe= re.compile('\\"')
		self.hexColorRe= re.compile('^#([0-9a-f]{2})\s*([0-9a-f]{2})\s*([0-9a-f]{2})\s*([0-9a-f]{2})?$',re.IGNORECASE)
		if self.dotString:
			self.parse(self.dotString)
	def saveCtx(self):
		"""
		Save the current graphical context.
		"""
		self.ctx.save()
	def restoreCtx(self):
		"""
		Restore the graphical context to the most recently saved state.
		"""
		self.ctx.restore()
	def centeredScale(self,s):
		"""
		This convenience function applies a scale about the center of the canvas, rather than the top left.
		It would typically be used to implement zoom operations.
		"""
		self.debugClear()
		self.ctx.translate(-self.viewCtrX, -self.viewCtrY)
		self.ctx.scale(s,s)
		self.ctx.translate(self.viewCtrX, self.viewCtrY)
		self.debug('centeredScale')
	def centeredTranslate(self,dx,dy):
		"""
		This translates (moves) the drawing coordinates while leaving the centering and scaling unchanged.
		It would typically be used to implement a drag operation.
		"""
		self.debugClear()
		self.ctx.translate(dx,dy)
		self.viewCtrX += dx
		self.viewCtrY += dy
	def recenter(self):
		"""
		Recenter the drawing coordinates.
		"""
		self.debugClear()
		if self.scaleSet:
			self.viewCtrX= (-(self.bb.r-self.bb.l)+self.padding)/2
			self.viewCtrY= (-(self.bb.t-self.bb.b)+self.padding)/2
		else:
			self.viewCtrX= 0.0
			self.viewCtrY= 0.0
	def getOffsetBase(self):
		"""
		Get current beliefs about browser coordinates of the top left corner of the canvas
		"""
		return self.offsetBaseTop, self.offsetBaseLeft
	def setOffsetBase(self,top,left):
		"""
		Caller is providing the absolute browser coordinates of the top left corner of the canvas
		"""
		self.offsetBaseTop,self.offsetBaseLeft= top,left
	def offsetInitialized(self):
		"""
		Test to determine if the canvas offset has been initialized via setOffsetBase()
		"""
		return (self.offsetBaseTop is not None)
	def setImagePath(self,imagePath):
		"""
		Specify a path prefix for images
		"""
		self.imagePath= imagePath
	def reportImageLoadStarted(self, canvizImage):
		"""
		Used by images to announce their creation to the owning Canviz.
		"""
		self.debug('looking for %s'%canvizImage.src)
	def reportImageLoadFinished(self, canvizImage):
		"""
		Used by images to announce to their owning Canviz that their efforts to load
		have finished (not necessarily successfully).
		"""
		if canvizImage.loaded:
			self.debug('Loaded %s'%canvizImage.src)
		else:
			self.debug('Tried to load %s but failed'%canvizImage.src)
		self.numImagesFinished += 1
		if self.numImagesFinished==self.numImages:
			if self.redrawInProgress:
				self.redrawsPendingCount += 1 # Force additional redraw when current one finishes
			else:
				self.draw()
	def load(self,url):
		"""
		This routine asynchronously fetches an xdot text string from the given url
		and passes that string to parse().  
		"""
		self.loadURL= url
		HTTPRequest().asyncGet(self.loadURL,self)
		
	def onCompletion(self,text):
		"""
		This is a callback of the HTTPRequest handler interface.  It occurs in the case of normal
		completion.
		"""
		self.parse(text)
	
	def onError(self, text, code):
		"""
		This is a callback of the HTTPRequest handler interface.  It occurs in the case of error.
		"""
		Window.alert('Error code %d trying to fetch %s'%(code,self.loadURL))

	def onTimeout(self, text):
		"""
		This is a callback of the HTTPRequest handler interface.  It occurs if the request times out.
		"""
		Window.alert('Timeout trying to fetch %s'%self.loadURL)
		Window.alert('onTimeout; %d chars'%len(text))

	def debug(self, str, escape=True):
		"""
		Write the given string to the debug element, if that element is not None.  If 'escape'
		is true, the string is escaped for HTML.
		"""                                                                                                                                                                                                                                                                                                                        
		#Window.alert('debug: %s'%str)
		if self.dbgElementE is not None:
			dbgElementE= self.dbgElementE
			JS("""
			str = String(str);
			if (escape) {
				var div = document.createElement('div'); 
	     	   	var text = document.createTextNode(str); 
	       		div.appendChild(text); 
	       		str= div.innerHTML;
			}
			dbgElementE.innerHTML += '&raquo;' + str + '&laquo;<br />';
			""")

	def debugClear(self):
		"""
		This is used to clear the debugging output, for example at the beginning of a new draw
		"""
		if self.dbgElementE is not None and self.dbgElementInitialContents is not None:
			DOM.setInnerHTML(self.dbgElementE,self.dbgElementInitialContents)

	def parse(self,xdot):
		"""
		xdot is a GraphVis graph description string in xdot format.  This function replaces the
		Canvis instance's internal dot string (if any) with the given string, parses the new
		string into an internal representation suitable for calling the 'draw' method, and then
		calls the 'draw' method.
		"""
		self.dotString= xdot
		self.graphs = []
		if self.ctx is None:
			self.ctx= self.canvas.getContext()
		else:
			self.ctx.reset()
		self.maxWidth = False
		self.maxHeight = False
		self.bbEnlarge = False
		self.scaleSet= False
		#self.bbScale = 1
		self.dpi = 96
		self.bgcolor = {'opacity': 1, 'canvasColor':'#ffffff', 'textColor':'#ffffff' }
		# splitlines seems to be unimplemented, so we have to do it manually.
		#lines = xdot.splitlines()
		lines= []
		self.debugClear()
		while True:
			loc= xdot.find('\n')
			if loc>=0:
				lines.append(xdot[:loc])
				xdot= xdot[loc+1:]
			else:
				lines.append(xdot)
				break
		i = 0
		containers = []
		startingEntityCount= CanvizEntity.entityCounter
		self.debug('parsing %d lines of xdot'%len(lines))
		while i<len(lines):
			line= lines[i].strip()
			i += 1
			if '' != line and '#' != line[0]:
				while i<len(lines) and ';' != line[-1] and '{' != line[-1] and '}' != line[-1]:
					if '\\' == line[-1]: line= line[:-1]
					line += lines[i]
					i += 1
				#self.debug(line)
				if 0 == len(containers):
					matches = self.graphMatchRe.match(line)
					if matches:
						rootGraph = CanvizGraph(matches.group(3), self, None, None)
						containers.append(rootGraph)
						containers[0].strict = (matches.group(1) is None)
						if matches.group(2)=='graph':
							containers[0].type= 'undirected'
						else:
							containers[0].type= 'directed'
						containers[0].attrs['xdotversion']= '1.0'
						self.graphs.append(containers[0])
						self.debug('graph: ' + containers[0].name)
				else:
					matches = self.subgraphMatchRe.match(line)
					if matches:
						containers.insert(0,CanvizGraph(matches.group(1), self, rootGraph, containers[0]))
						containers[1].subgraphs.append(containers[0])
						if containers[0].name is None:
							self.debug('nameless subgraph')
						else:
							self.debug('subgraph: ' + containers[0].name);
				if matches:
					#self.debug('begin container ' + containers[0].name)
					pass
				elif '}' == line:
					#self.debug('end container ' + containers[0].name)
					containers= containers[1:]
					if len(containers)==0:
						break
				else:
					matches = self.nodeMatchRe.match(line)
					if matches:
						entityName = matches.group(2)
						attrs = matches.group(5)
						drawAttrHash = containers[0].drawAttrs
						isGraph = False
						if entityName=='graph':
							attrHash = containers[0].attrs
							isGraph = True
						elif entityName=='node':
							attrHash = containers[0].nodeAttrs
						elif entityName=='edge':
							attrHash = containers[0].edgeAttrs
						else:
							entity = CanvizNode(entityName, self, rootGraph, containers[0])
							attrHash = entity.attrs
							drawAttrHash = entity.drawAttrs
							containers[0].nodes.append(entity)
						#self.debug('node: ' + entityName)
					else:
						matches = self.edgeMatchRe.match(line)
						if matches:
							entityName = matches.group(1)
							attrs = matches.group(8)
							entity = CanvizEdge(entityName, self, rootGraph, containers[0], matches.group(2), matches.group(5))
							attrHash = entity.attrs
							drawAttrHash = entity.drawAttrs
							containers[0].edges.append(entity)
							#self.debug('edge: ' + entityName)
					if matches:
						while True:
							if len(attrs)==0: break
							matches = self.attrMatchRe.match(attrs)
							if matches:
								attrs = attrs[len(matches.group(0)):]
								attrName = matches.group(1)
								attrValue = self.unescape(matches.group(2))
								if self.drawAttrMatchRe.match(attrName):
									drawAttrHash[attrName]= attrValue
									#self.debug('drawAttr: ' + attrName + ' ' + attrValue)
								else:
									attrHash[attrName]= attrValue
									#self.debug('attr: ' + attrName + ' ' + attrValue)
								if isGraph and 1==len(containers):
									if attrName=='bb':
										bb = attrValue.split(',')
										self.bb= BoundingBox(int(bb[0]),int(bb[1]),int(bb[2]),int(bb[3]))
									elif attrName=='bgcolor':
										self.bgcolor = rootGraph.parseColor(attrValue);
									elif attrName=='dpi':
										self.dpi = int(attrValue)
									elif attrName=='size':
										size = self.sizeRe.match(attrValue)
										if size:
											self.maxWidth  = 72 * float(size.group(1))
											self.maxHeight = 72 * float(size.group(2))
											self.bbEnlarge= ('!'==size.group(3))
										else:
											self.debug('can\'t parse size')
									elif attrName=='xdotversion':
										if (0 > self.versionCompare(self.maxXdotVersion, attrHash['xdotversion'])):
											self.debug('unsupported xdotversion ' + attrHash['xdotversion'] + '; this script currently supports up to xdotversion ' + self.maxXdotVersion)
							else:
								self.debug('can\'t read attributes for entity ' + entityName + ' from ' + attrs)
							if not matches: break
		self.debug('done; built %d entities'%(CanvizEntity.entityCounter - startingEntityCount))
		self.draw()
	def draw(self,redrawCanvasOnly=False):
		"""
		Draw the graph represented by the current xdot string onto the Canviz instance's canvas.
		Images required for the graph are loaded as needed.  The text fields are actually
		HTML text elements drawn in such a way that they overlay the graph canvas.  If 
		redrawCanvasOnly is true, the text elements will not be redrawn- this can save time but 
		if the graphical transformation has changed since the text elements were drawn it can
		result in the text failing to line up with the graphical elements.
		
		If the xdot string requires that any images be loaded, this function will be called
		again automatically once all the image loads are complete.  If the loads complete while 
		a draw operation is in progress, the draw will be followed immediately by a second draw.
		
		For efficiency, bounding box information is used to skip over off-screen graph elements.
		Very tiny graph elements (less than 2x2 pixels) are replaced with a drawing of the element 
		bounding box. This may cause HTML text elements associated with these graph elements to 
		not be created, but those text elements are too small to read or click on in any case.
		"""
		# No sense drawing if our offset has not been initialized- ignore this
		# until setOffsetBase is called with valid values.
		if self.offsetInitialized():
			self.redrawsPendingCount += 1
			while self.redrawsPendingCount > 0:
				winSzX= self.canvas.getCoordWidth()
				winSzY= self.canvas.getCoordHeight()
				self.debug('winSz: %s %s'%(winSzX,winSzY))
				self.debug('bbox: %s %s %s %s'%(self.bb.l,self.bb.b,self.bb.r,self.bb.t))
				if not self.scaleSet:
					self.debug('setting scale')
					initialScaleX= winSzX/(self.bb.r+2*self.padding-self.bb.l)
					initialScaleY= winSzY/(self.bb.t+2*self.padding-self.bb.b)
					
					# Now we construct a transformation which maps the GraphVis image
					# to the canvas' coordinate space.  The Canvas transform rules
					# say that these transformations will be applied in reverse order,
					# so it makes more sense if one reads them backwards.
					# Step 4: Translate the origin to the canvas center location
					self.ctx.translate(winSzX/2,winSzY/2)
		
					# Step 3: Flip the Y axis, since the canvas coordinates are upside down
					self.ctx.scale(1.0,-1.0) # I prefer positive Y to be up
					
					# Step 2: Scale the bounding box into the canvas' bounding box size.
					s= min(initialScaleX,initialScaleY)
					self.ctx.scale(s,s)
		
					# Step 1: translate the center of the bounding box to the origin
					self.viewCtrX= (-(self.bb.r-self.bb.l)+self.padding)/2
					self.viewCtrY= (-(self.bb.t-self.bb.b)+self.padding)/2
					self.ctx.translate( self.viewCtrX, self.viewCtrY )
					
					self.scaleSet= True
					self.ctx.save()
				self.debug('drawing at trans %s %s %s %s'%(self.ctx.t00,self.ctx.t11,self.ctx.t02,self.ctx.t12))
				if not redrawCanvasOnly:
					# Clear the text elements
					sEE= self.elementsE
					JS("""
						while (sEE.hasChildNodes()) {
		   				 sEE.removeChild(sEE.lastChild);
						}
					""")
				self.ctx.save()
				self.ctx.lineCap = 'round';
				self.ctx.setFillStyle(self.bgcolor['textColor'])
				self.ctx.clear()
				self.graphs[0].draw(self.ctx, redrawCanvasOnly);
				self.ctx.restore()
				self.debug('done drawing.')
				self.redrawsPendingCount -= 1
			else:
				self.debug('draw skipped; offsets not initialized')
			
	def drawPath(self,ctx,filled,dashStyle):
		"""
		drawPath: function(ctx, path, filled, dashStyle) {
			if (filled) {
				ctx.beginPath();
				path.makePath(ctx);
				ctx.fill();
			}
			if (ctx.fillStyle != ctx.strokeStyle || !filled) {
				switch (dashStyle) {
					case 'dashed':
						ctx.beginPath();
						path.makeDashedPath(ctx, this.dashLength);
						break;
					case 'dotted':
						var oldLineWidth = ctx.lineWidth;
						ctx.lineWidth *= 2;
						ctx.beginPath();
						path.makeDottedPath(ctx, this.dotSpacing);
						break;
					case 'solid':
					default:
						if (!filled) {
							ctx.beginPath();
							path.makePath(ctx);
						}
				}
				ctx.stroke();
				if (oldLineWidth) ctx.lineWidth = oldLineWidth;
			}
		},
		"""
		if filled: ctx.fill()
		if dashStyle=='dashed':
			ctx.setStrokeDashed()
		elif dashStyle=='dotted':
			ctx.setStrokeDotted()
			#oldLineWidth = ctx.lineWidth
			#ctx.lineWidth *= 2
			#path.makeDottedPath(ctx, self.dotSpacing)
			#ctx.lineWidth= oldLineWidth
		elif dashStyle=='solid':
			ctx.setStrokeSolid()
		ctx.stroke()
	def unescape(self,str):
		"""
		unescape: function(str) {
			var matches = str.match(/^"(.*)"$/);
			if (matches) {
				return matches[1].replace(/\\"/g, '"');
			} else {
				return str;
			}
		},
		"""
		matches = self.unescapeRe.match(str)
		if matches:
			return self.unescapeReplaceRe.sub('"',matches.group(1))
		else:
			return str
	def parseHexColor(self,color):
		"""
		Convert a color of the form '#xx xx xx' to a color dictionary of the form:
			{'canvasColor':'rgba(255,255,255,255)','textColor':'rgba(255,255,255,255)','opacity':1}
		"""
		textColor= None
		opacity= None
		matches= self.hexColorRe.match(color)
		if matches:
			textColor= '#%s%s%s'%(matches.group(1),matches.group(2),matches.group(3))
			opacity= 1.0
			if matches.group(4) is not None:
				opacity = int(matches.group(4), 16) / 255
				canvasColor= 'rgba(%d,%d,%d,%f)'%(int(matches.group(1),16),int(matches.group(2),16),int(matches.group(3),16),
												  opacity)
			else:
				canvasColor = textColor;
		return {'canvasColor': canvasColor, 'textColor': textColor, 'opacity': opacity}
	def hsvToRgbColor(self,h,s,v):
		"""
		Convert a color value in the form of a HSV (hue, saturation, value) triple to a color
		string of the form 'rgb(255,255,255)'.
		"""
		h *= 360
		i = int(math.floor(h / 60)) % 6
		f = h / 60 - i
		p = v * (1 - s)
		q = v * (1 - f * s)
		t = v * (1 - (1 - f) * s);
		if i==0: r = v; g = t; b = p
		elif i==1: r = q; g = v; b = p
		elif i==2: r = p; g = v; b = t
		elif i==3: r = p; g = q; b = v
		elif i==4: r = t; g = p; b = v
		elif i==5: r = v; g = p; b = q
		return 'rgb(%d,%d,%d)'%(int(round(255*r)),
								int(round(255*g)),
								int(round(255*b)))
	def versionCompare(self,a,b):
		"""
		Compares two version strings.
		"""
		a = a.split('.')
		b = b.split('.')
		while len(a) or len(b):
			if len(a): 
				a1= int(a[0])
				a= a[1:]
			else:
				a1= 0
			if len(b): 
				b1= int(b[0])
				b= b[1:]
			else:
				b1= 0
			if a1<b1: return -1
			elif a1>b1: return 1
		return 0

