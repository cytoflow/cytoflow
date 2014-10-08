package org.flowcyt.cfcs;
// Gate an FCS file, removing all values of P1 < 100 channels for all
// listmode datasets in the file (skipping any non-listmode datasets)

// Usage: java PrintKeywords file:source.fcs file:destination.fcs


public class GateChannels {

	private static final int INPUT = 0, OUTPUT = 1;
	
	private static final int LIMIT = 100;
	
	static int failIfError(CFCSError error) {
		int errorType = 0;

		while (error != null) {
			System.err.println(error);

			if (error.errorNumber < 0) {
				errorType = -1;
				}
			else if (error.errorNumber > 0 && errorType == 0) {
				errorType = 1;
				}

			error = error.nextError;
			}

		return errorType;
		}

	public static void main(String[] argv) {
		CFCSSystem readSystem = new CFCSSystem();

		try { readSystem.open(argv[INPUT]); }
		catch (CFCSError error) {
			if (failIfError(error) != 0) System.exit(1);
			}

		CFCSSystem writeSystem = new CFCSSystem();

		try { writeSystem.create(argv[OUTPUT]); }
		catch (CFCSError error) {
			if (failIfError(error) != 0) System.exit(1);
			}

		int nDataSets = readSystem.getCount();

		for (int iset = 0; iset < nDataSets; iset++) {
			CFCSDataSet readSet = readSystem.getDataSet(iset);
			CFCSData readData = readSet.getData();
			int readDataType = readData.getType();

			if (readDataType == CFCSData.LISTMODE) {
				CFCSDataSet writeSet = writeSystem.createDataSet(readSet);
				CFCSData writeData = writeSet.getData();

				CFCSListModeData readList = (CFCSListModeData) readData;
				CFCSListModeData writeList = (CFCSListModeData) writeData;

				CFCSParameters paramList = readSet.getParameters();

				// allocate an array to hold one event
				short[] event = new short[paramList.getCount()];

				int nEvents = readList.getCount();

				for (int idx = 0; idx < nEvents; idx++) {
					readList.getEvent(idx, event);
					if (event[0] < LIMIT) writeList.addEvent(event);
					}	
				}
			}

		readSystem.close();
		writeSystem.close();
		}
	}
