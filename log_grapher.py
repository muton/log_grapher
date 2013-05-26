#!/usr/bin/env python

import tkinter as tk, time, subprocess, csv, re, time, matplotlib, sys, random, numpy, json
matplotlib.use( "TkAgg" )
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from pprint import pprint
from tkinter.constants import *
from threading import Thread
from queue import Queue, Empty

conf_file_name = "log_grapher_conf.json"
if len( sys.argv ) > 1:
	conf_file_name = sys.argv[1]

class LogReader:
	"""
	Tails a log file and allows lines to be retreived 
	in a non-blocking way.
	If windows:
		needs cygwin (or just tail.exe) in path
		needs set CYGWIN=nodosfilewarning environment variable
	"""
	def __init__(self, filePath):
		self.proc = subprocess.Popen( ["tail", "--sleep-interval=0.25", "-F", filePath], 
			stdout=subprocess.PIPE, universal_newlines=True )
		self.queue = Queue()
		self.thread = Thread( target=self.enqueue_output, args=( self.proc.stdout, self.queue ) )
		self.thread.daemon = True
		self.thread.start()

	def enqueue_output( self, pipe, queue ):
		for line in iter( pipe.readline, b'' ):
			queue.put( line )
		pipe.close()

	def get_line( self ):
		line = None
		try:
			line = str( self.queue.get_nowait() )
		except Empty:
			pass
		return line


class GraphModel:
	def __init__( self ):
		self.rows = []
		self.labels = ["time"]
		self.numCols = 0
		self.rowsSentToGui = 0

	def setLabels( self, labelList ):
		self.labels = ["time"] + labelList
		self.numCols = len( self.labels )

	def add( self, elapsedTime, labelList, valueList ):
		"""
		Put items in the list at recorded time. Note time must be greater 
		than or equal to the latest time previously logged
		"""
		row = None
		if len( self.rows ) > 0:
			row = self.rows[-1]
		if row is None or row[0] != elapsedTime:
			row = self.numCols * [None]
			row[0] = elapsedTime;
			self.rows.append( row )
		for idx, val in enumerate( labelList ):
			row[self.labels.index(val)] = float( valueList[idx] ) 

	def updateGui( self, gui ):
		for idx in range( self.rowsSentToGui, len( self.rows ) ):
			row = self.rows[idx]
			gui.append( row[0], row[1:] )
		self.rowsSentToGui = len( self.rows )
		gui.update()

	def writeCsv( self, csvPath ):
		with open( csvPath, 'w', newline='') as csvfile:
			sheet = csv.writer( csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL )
			sheet.writerow( self.labels )
			for row in self.rows:
				sheet.writerow( row )


class GraphDataFilter:
	def __init__( self, regexStr, captureGroupList, fieldNameList ):
		self.regex = re.compile( regexStr )
		self.captureGroupList = captureGroupList
		self.fieldNameList = fieldNameList

	def processLine( self, line, time, graphModel ):
		match = self.regex.search( line )
		pprint( line )
		if ( match != None ):
			vals = len( self.captureGroupList ) * [None]
			for idx, val in enumerate( self.captureGroupList ):
				vals[idx] = match.group( val )
			graphModel.add( time, self.fieldNameList, vals )

class Gui:
	def __init__( self ):
		self.root = tk.Tk()
		self.root.wm_title( "Log grapher" )
		matplotlib.rc('font', size=8 )
		self.fig = Figure( figsize=(11,5), dpi=100 )
		self.fig.set_tight_layout( True )
		self.axis = self.fig.add_subplot( 111 )
		self.axis.set_title( 'Graph' )
		self.axis.set_xlabel( 'X axis label' )
		self.axis.set_ylabel( 'Y label' )
		self.canvas = FigureCanvasTkAgg( self.fig, master=self.root )
		self.canvas.show()
		self.canvas.get_tk_widget().pack( side=TOP, fill=BOTH, expand=1 )

	def setLabels( self, labelList ):
		"""setLabels before doing anything else - configures axes etc"""
		self.labels = labelList
		for i in range( 0, len( labelList ) ):
			self.axis.plot( [] )
		self.fig.legend( self.axis.lines, self.labels, 'lower center', ncol=len(self.labels), 
			borderpad=0.3, handletextpad=0.2, columnspacing=0.3 )

	def append( self, xVal, yValList ):
		"""
		yValList must be the same length as labelList, None values will be ignored.
		Call update() afterwards.
		"""
		#print( "gui append " + str( xVal ) + ", " )
		#pprint( yValList )
		for idx, yVal in enumerate( yValList ):
			if yVal is not None:
				hl = self.axis.lines[idx]
				hl.set_xdata( numpy.append( hl.get_xdata(), xVal ) )
				hl.set_ydata( numpy.append( hl.get_ydata(), yVal ) )

	def update( self ):
		self.axis.relim()
		self.axis.autoscale_view()
		self.canvas.draw()


with open( conf_file_name ) as conf_file:    
    conf = json.load( conf_file )

filters = []
for fltObj in conf["filters"]:
	filters.append( GraphDataFilter( fltObj["regex"], fltObj["groups"], fltObj["labels"] ) )

reader = LogReader( conf["url"] )
model = GraphModel()

labelList = []
for flt in filters: labelList.extend( flt.fieldNameList )
model.setLabels( labelList )

startTime = time.time()

gui = Gui()
gui.setLabels( labelList )

pollCount = 0

def periodicFunc():
	global filters, model, gui, pollCount
	pollCount += 1
	elapsedTime = time.time() - startTime
	line = reader.get_line()
	while line is not None:
		for flt in filters: flt.processLine( line, elapsedTime, model )
		line = reader.get_line()
	#model.writeCsv( "output.csv" )
	if pollCount % 4 == 0:
		model.updateGui( gui )
	gui.root.after( 250, periodicFunc )

gui.root.after( 250, periodicFunc )

tk.mainloop()