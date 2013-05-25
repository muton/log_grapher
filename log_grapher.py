import tkinter as t, time, subprocess, csv, re, time
from pprint import pprint
from tkinter.constants import *
from threading import Thread
from queue import Queue, Empty

class LogReader:
	"""
	Tails a log file and allows lines to be retreived 
	in a non-blocking way.
	If windows:
		needs cygwin (or just tail.exe) in path
		needs set CYGWIN=nodosfilewarning environment variable
	"""
	def __init__(self, filePath):
		self.proc = subprocess.Popen( ["tail", "-F", filePath], stdout=subprocess.PIPE, universal_newlines=True )
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
			row[self.labels.index(val)] = valueList[idx] 

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


filters = [
	GraphDataFilter( r"memBytesUsed=(\d*) memBytesHigh=(\d*) memBytesLimit=(\d*)", 
		[1,2,3], ["memBytesUsed","memBytesHigh","memBytesLimit"] ),
	GraphDataFilter( r"gfxBytesUsed=(\d*) gfxBytesHigh=(\d*) gfxBytesLimit=(\d*) gfxNumPlanes=(\d*)", 
		[1,2,3,4], ["gfxBytesUsed","gfxBytesHigh","gfxBytesLimit","gfxNumPlanes"] )
]

url = r'C:\Users\Tim Hawkins\AppData\Roaming\Macromedia\Flash Player\Logs\flashlog.txt'
displayStr = ""

root = t.Tk()
root.geometry( "500x500" )

frame = t.Frame( root, width=100, height=100 )
frame.pack( expand=1, fill=BOTH )

label = t.Label( frame, text="Hello World!", anchor=NW )
label.pack( expand=1, fill=BOTH )

quitBtn = t.Button( frame, text="Quit", command=frame.quit )
quitBtn.pack( side=RIGHT )

reader = LogReader( url )
model = GraphModel()

labelList = []
for flt in filters: labelList.extend( flt.fieldNameList )
model.setLabels( labelList )

startTime = time.time()

def periodicFunc():
	global displayStr, filters, model
	#now = time.strftime( "%H:%M:%S" )
	#displayStr += time.strftime( "%H:%M:%S" ) + "\n"
	#while True:
	elapsedTime = int( time.time() - startTime )
	line = reader.get_line()
	while line is not None:
		for flt in filters: flt.processLine( line, elapsedTime, model )
		displayStr += line
		line = reader.get_line()

	#if line is None: break
	#displayStr += line + "\n" 
	label.configure( text=displayStr )
	model.writeCsv( "output.csv" )
	root.after( 1000, periodicFunc )

root.after( 1000, periodicFunc )

root.mainloop()