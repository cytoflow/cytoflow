package org.flowcyt.cfcs;
// Convert an FCS file of type $DATATYPE/I to type $DATATYPE/A

// Usage: java IntegerToAscii file:integerSource.fcs file:asciiDestination.fcs

// Note: probably also works fine with a source of $DATATYPE/D or F


public class IntegerToAscii {

	private static final int INPUT = 0, OUTPUT = 1;

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
		catch (CFCSError error) { if (failIfError(error) != 0) System.exit(1); }

		CFCSSystem writeSystem = new CFCSSystem();

		try { writeSystem.create(argv[OUTPUT]); }
		catch (CFCSError error) { if (failIfError(error) != 0) System.exit(1); }

		int nDataSets = readSystem.getCount();

		for (int set = 0; set < nDataSets; set++) {
			CFCSDataSet readSet = readSystem.getDataSet(set);
			CFCSKeywords readKeywords = readSet.getKeywords();
			CFCSParameters readParam = readSet.getParameters();
			CFCSData readData = readSet.getData();
			
			int type = readData.getType();

			CFCSDataSet writeSet = writeSystem.createDataSet(type, CFCSDatatype.ASCII);
			CFCSKeywords writeKeywords = writeSet.getKeywords();
			CFCSParameters writeParam = writeSet.getParameters();
			CFCSData writeData = writeSet.getData();
		
			for (int i = 0, count = readParam.getCount(); i < count; i++) {
				CFCSParameter parameter = readParam.getParameter(i);
				parameter.setFieldSize(0); // Free format
				writeParam.addParameter(parameter);
				}

			switch (type) {
				case CFCSData.LISTMODE : /* ListModeData */

					// allocate an array to hold one event
					int[] event = new int[readParam.getCount()];

					int nEvents = ((CFCSListModeData) readData).getCount();

					for (int i = 0; i < nEvents; i++) {
						((CFCSListModeData) readData).getEvent(i, event);
						((CFCSListModeData) writeData).addEvent(event);
						}	
					break;
				
				case CFCSData.UNCORRELATED : /* UncorrelatedData */

					int nParams = writeParam.getCount();

					for (int i = 0; i < nParams; i++) {
						// allocate an array to hold one histogram bucket
						int[] array = new int[writeParam.getParameter(i).getRange()];

						((CFCSUncorrelatedData) readData).getArray(i, array);
						((CFCSUncorrelatedData) writeData).addArray(array);
						}
					break;	
				
				case CFCSData.CORRELATED : /* CorrelatedData */

					// allocate an array to hold entire histogram
					int[][] table = new int[writeParam.getParameter(1).getRange()][writeParam.getParameter(0).getRange()];

					((CFCSCorrelatedData) readData).getArray(table);
					((CFCSCorrelatedData) writeData).setArray(table);

					break;	
				}
			
			// Try to copy all the 'safe' keywords that haven't already been set

			for (int i = 0, count = readKeywords.getCount(); i < count; i++) {
				CFCSKeyword keyword = readKeywords.getKeyword(i);

				try { writeKeywords.getKeyword(keyword.getKeywordName()); }
				catch (CFCSError error) {
					if (error.errorNumber == CFCSErrorCodes.CFCSKeywordNotFound) {
						try { writeKeywords.addKeyword(keyword); }
						catch (CFCSError exception) { }
						}
					else if (failIfError(error) != 0) System.exit(1);
					}
				}
			}

		readSystem.close();
		writeSystem.close();
		}
	}
