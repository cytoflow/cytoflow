BEGIN {
	print "name: cytoflow"
	print "channels:"
	print " - cytoflow"
	print ""
	print "dependencies:"
	}

/test:$/ { SAW_RUN=0 }
//       { if (SAW_RUN) print }
/run:$/  { SAW_RUN=1 }
