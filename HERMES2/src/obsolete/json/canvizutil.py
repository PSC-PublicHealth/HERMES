#! /usr/bin/env python

#/*
# * This file is part of Canviz. See http://www.canviz.org/
# * $Id$
# */

##################################
# Notes-
#
##################################

_hermes_svn_id_="$Id$"

from pyjamas import Window, DOM
from __pyjamas__ import JS
from pyjamas.Canvas.GWTCanvas import GWTCanvas

class BoundingBox:
	def __init__(self,l,b,r,t):
		"""
		This class is an attempt to get bounding box rectangles out of
		the Path hierarchy, because the Pyjamas compiler seems to be having
		some sort of problem with the recursion involved.
		"""
		if l<=r:
			self.l= l
			self.r= r
		else:
			self.l= r
			self.r= t
		if b<t:
			self.t= t
			self.b= b
		else:
			self.t= b
			self.b= t
	def draw(self,ctx):
		ctx.save()
		#ctx.setStrokeStyle('#f00')
		ctx.setLineWidth(1)
		#ctx.beginPath()
		#ctx.moveTo(self.l,self.b)
		#ctx.lineTo(self.r,self.t)
		#ctx.moveTo(self.r,self.b)
		#ctx.lineTo(self.l,self.t)
		#ctx.stroke()
		ctx.strokeRect(self.l,self.b,self.r-self.l,self.t-self.b)
		ctx.restore()
	def drawFilled(self,ctx):
		ctx.save()
		ctx.strokeRect(self.l,self.b,self.r-self.l,self.t-self.b)
		ctx.restore()
	def expandToInclude(self,rect):
		"""
		Mimic the Rect method.
		"""
		self.l= min(self.l, rect.l)
		self.t= max(self.t, rect.t)
		self.r= max(self.r, rect.r)
		self.b= min(self.b, rect.b)
	def intersects(self,otherBB):
		if self.r<otherBB.l or self.l>otherBB.r or self.t<otherBB.b or self.b>otherBB.t: 
			return False
		else:
			return True
	def getHeight(self):
		return self.b - self.t
	def getWidth(self):
		return self.r - self.l
	def str(self):
		return "BoundingBox<%s,%s,%s,%s>"%(self.l,self.b,self.r,self.t)

class CanvasContext:
	def __init__(self,canvas):
		"""
		This context is an enhancement of the GWTCanvas which keeps track of the
		projection transformation.  We'll support a 2D homogeneous transformation 
		without rotation, so the transformation matrix looks like:
		
		t00  0  t02
		0   t11 t12
		0    0   1
		
		For reasons beyond my ken is has been decreed that transformations be
		applied in reverse order for javascript Canvas elements, so we need to
		right-multiply each new transform as it comes in.
		"""
		self.canvas= canvas
		self.bgClr= '#ffffff'
		self.fillClr= '#000000'
		self.strokeClr= '#000000'
		self.ctxStack= []
		self.t00= 1.0
		self.t11= 1.0
		self.t02= 0.0
		self.t12= 0.0
		self.projectionBBox= None
	def reset(self):
		"""
		Returns context to the state it had when first created
		"""
		self.bgClr= '#ffffff'
		self.fillClr= '#000000'
		self.strokeClr= '#000000'
		self.ctxStack= []
		self.projectionBBox= None
		# We have to literally move the canvas back to its starting transformation
		self.scale(1.0/self.t00,1.0/self.t11)
		self.translate(-self.t02,-self.t12)
	def getProjectionBBox(self):
		if self.projectionBBox is None:
			l,b= self.getBackProjectedCoords(0,0)
			r,t= self.getBackProjectedCoords(self.canvas.getCoordWidth(),self.canvas.getCoordHeight())
			self.projectionBBox= BoundingBox(l,b,r,t)
		return self.projectionBBox
	def getBackProjectedCoords(self,x,y):
		bpX= (x-self.t02)/self.t00
		bpY= (y-self.t12)/self.t11
		return bpX,bpY
	def getProjectedCoords(self,x,y):
		projX= self.t00*x + self.t02
		projY= self.t11*y + self.t12
		return (projX,projY)
	def getClippedProjectedCoords(self,x,y):
		projX,projY= self.getProjectedCoords(x,y)
		if projX<0.0 or projY<0.0 or projX>self.canvas.getCoordWidth() or projY>self.canvas.getCoordHeight(): return None
		else: return (projX,projY)
	def save(self):
		self.canvas.saveContext()
		self.ctxStack.append((self.bgClr,self.fillClr,self.strokeClr,
							  self.t00,self.t11,self.t02,self.t12))
	def restore(self):
		self.bgClr,self.fillClr,self.strokeClr,self.t00,self.t11,self.t02,self.t12= self.ctxStack.pop()
		self.projectionBBox= None
		self.canvas.restoreContext()
	def fillRect(self,x,y,width,height):
		#self.canvas.setFillStyle(self.fillStyle)
		self.canvas.fillRect(x,y,width,height)
	def strokeRect(self,x,y,width,height):
		self.canvas.strokeRect(x,y,width,height)
	def translate(self,x,y):
		self.canvas.translate(x,y)
		self.t02 += self.t00*x
		self.t12 += self.t11*y
		self.projectionBBox= None
	def scale(self,sx,sy):
		self.canvas.scale(sx,sy)
		self.t00 *= sx
		self.t11 *= sy
		self.projectionBBox= None
	def transform(self,m00,m01,m10,m11,dx,dy):
		"Our transforms are always unrotated, so m01 and m10 are ignored"
		self.canvas.transform(m00,0.0,0.0,m11,dx,dy)
		self.t02= self.t00*dx + self.t02
		self.t12= self.t11*dy + self.t12
		self.t00 *= m00
		self.t11 *= m11
		self.projectionBBox= None
	def beginPath(self):
		self.canvas.beginPath()
	def closePath(self):
		self.canvas.closePath()
	def moveTo(self,x,y):
		self.canvas.moveTo(x,y)
	def lineTo(self,x,y):
		self.canvas.lineTo(x,y)
	def fill(self):
		self.canvas.setFillStyle(self.fillClr)
		self.canvas.fill()
	def stroke(self):
		self.canvas.setStrokeStyle(self.strokeClr)
		self.canvas.stroke()
	def quadraticCurveTo(self,x1,y1,x2,y2):
		self.canvas.quadraticCurveTo(x1,y1,x2,y2)
	def cubicCurveTo(self, cp1x, cp1y, cp2x, cp2y, x, y):
		self.canvas.cubicCurveTo(cp1x,cp1y,cp2x,cp2y,x,y)
	def setBackgroundColor(self,clr):
		self.canvas.setBackgroundColor(clr)
		self.bgClr= clr
	def setFillStyle(self,clr):
		self.canvas.setFillStyle(clr)
		self.fillClr= clr
	def setStrokeStyle(self,clr):
		self.canvas.setStrokeStyle(clr)
		self.strokeClr= clr
	def setStrokeDashed(self):
		pass
	def setStrokeDotted(self):
		pass
	def setStrokeSolid(self):
		pass
	def clear(self):
		"""clear image; GWTCanvas.clear() method is broken"""
		self.setFillStyle(self.bgClr['canvasColor'])
		llX,llY= self.getBackProjectedCoords(0,0)
		trX,trY= self.getBackProjectedCoords(self.canvas.getCoordWidth(),self.canvas.getCoordHeight())
		self.canvas.fillRect(llX,llY,trX-llX,trY-llY)
		self.setFillStyle(self.fillClr)
	def drawImage(self,img,*args):
		self.canvas.drawImage(img,*args)
	def setLineWidth(self,width):
		self.canvas.setLineWidth(width)

class CanvizCanvas(GWTCanvas):
	def __init__(self):
		GWTCanvas.__init__(self)
	def getContext(self):
		return CanvasContext(self)

def escapeHTML(dirty):
	d = DOM.createDiv()
	t = DOM.createTextNode(dirty)
	d.appendChild(t)
	str= DOM.getInnerHTML(d)
	return str

def getTotalOffsets(elem):
    JS("""
    t= l= 0;
    if (elem.offsetParent) {
        do {
            l += elem.offsetLeft;
            t += elem.offsetTop;
        } while (elem= elem.offsetParent);
    }
    """)
    return t,l
		
