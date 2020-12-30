BEGIN {
	print "name: cytoflow"
	print "channels:"
	print " - bpteague"
	print ""
	print "dependencies:"
	}

/test:$/ { SAW_RUN=0 }
//       { if (SAW_RUN) print }
/run:$/  { SAW_RUN=1 }
