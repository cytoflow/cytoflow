package org.flowcyt.facejava.faceflow.test;

import org.flowcyt.facejava.compensation.SpilloverMatrixSet;
import org.flowcyt.facejava.compensation.xmlio.CompensationMLFileReader;
import org.flowcyt.facejava.faceflow.application.outputlayers.BaseDataSetLayer;
import org.flowcyt.facejava.faceflow.application.outputlayers.CompensationLayer;
import org.flowcyt.facejava.faceflow.application.outputlayers.GateLayer;
import org.flowcyt.facejava.faceflow.application.outputlayers.OutputLayer;
import org.flowcyt.facejava.faceflow.application.outputlayers.TransformationLayer;
import org.flowcyt.facejava.fcsdata.impl.FcsDataFile;
import org.flowcyt.facejava.fcsdata.io.CFCSInput;
import org.flowcyt.facejava.fcsdata.io.FcsInput;
import org.flowcyt.facejava.gating.gates.GateSet;
import org.flowcyt.facejava.gating.xmlio.GatingMLFileReader;
import org.flowcyt.facejava.transformation.TransformationCollection;
import org.flowcyt.facejava.transformation.xmlio.TransformationMLFileReader;

public class OutputLayersTestHarness {
	private String fileLocation;
	
	private FcsDataFile dataFile;
	
	private SpilloverMatrixSet spilloverColl;
	
	private TransformationCollection transColl;
	
	private GateSet gateColl;
	
	public void setFcsFile(String uri) throws Exception {
		this.fileLocation = uri;
		FcsInput fcsIn = new CFCSInput();
		dataFile = fcsIn.read(uri);
	}
	
	public void setCompensationFile(String uri) throws Exception {
		CompensationMLFileReader reader = new CompensationMLFileReader(uri);
		spilloverColl = reader.read();
	}
	
	public void setGatingFile(String uri) throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(uri);
		gateColl = reader.read();
	}

	public void setTransformationFile(String uri) throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader(uri);
		transColl = reader.read();
	}
	
	public OutputLayer getFinalLayer(int dataSetNumber, String spilloverMatrixId, String gateId) throws Exception {
		OutputLayer rv = new BaseDataSetLayer(dataFile.getByDataSetNumber(dataSetNumber), fileLocation);
		
		if (spilloverMatrixId != null && spilloverColl != null)
			rv = new CompensationLayer((BaseDataSetLayer)rv, spilloverColl.get(spilloverMatrixId));
		
		if (transColl != null)
			rv = new TransformationLayer(rv, transColl);
		
		if (gateId != null && gateColl != null)
			rv = new GateLayer(rv, gateColl.get(gateId));
		
		return rv;
	}
}
