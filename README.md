#log_grapher

Real time graphs from any log file using regular expressions, in Python.

##Requirements

###General
 * Python 3
 * tkinter
 * matplotlib

###Windows
 * cygwin (for tail.exe) in PATH
 * Set environment variable CYGWIN=nodosfilewarning

###Linux
I managed to get things working on Ubuntu by following these [instructions](http://joat-programmer.blogspot.co.uk/2012/11/install-matplotlib-on-ubuntu-1210-for.html).

##Usage
      [python] log_grapher.py [conf_file.json]
...where conf\_file.json is optional, and defaults to log\_grapher\_conf.json.

###Config file format

    {
    	"path": "mylogfile.txt",
    	"csv": "mylogfile_memory.csv",
    	"filters": [
    		{
    			"regex": "memBytesUsed=(\\d*) memBytesHigh=(\\d*)",
    			"groups": [1,2],
    			"labels": ["memBytesUsed","memBytesHigh"]
    		},
    		{
    			"regex": "gfxBytesUsed=(\\d*) gfxBytesHigh=(\\d*) gfxBytesLimit=(\\d*) gfxNumPlanes=(\\d*)",
    			"groups": [1,4],
    			"labels": ["gfxBytesUsed","gfxNumPlanes"]
    		}
    	]
    }

 * **path**: Location of the log file to be followed.
 * **csv**: A file which will be created and periodically updated with graph data.
 * **filters**: Array of filter objects, which describe the data to be graphed.

####Filters
Each filter consists of:

 * A regular expression with one or more capture groups. Because this is JSON, stuff must be double-escaped; use two backslashes instead of one. Capture groups must be numeric.
 * A list of capture groups from the preceding regex which should be displayed on the graph. The first group is 1, second is 2, etc (not zero-based).
 * Labels to appear on the legend of the graph, corresponding to the capture groups in the 'groups' array.

##Notes

 * The x-axis of the graph is time in seconds since log_grapher started. Next time I need to deal with a log file that actually has timestamps I'll reexamine this.
 * May have bugs, may not be very Pythonic, I just used Python because it looked quite fun, YMMV.
