package org.flowcyt.cfcs;

// Unpack the data in a ListMode FCS file of type $DATATYPE/I

// Usage: java UnpackData file:packed.fcs file:unpacked.fcs


public class UnpackData {

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

	public static int rangeToBits(int range) {
		int bits = 1, mask = 1;

		range--;

		while ((range | mask) != mask) {
			mask = (mask << 1) + 1;
			++bits;
			}

		return 8 * ((bits + 7) / 8);
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
			CFCSData readData = readSet.getData();

			if (readData.getType() == CFCSData.LISTMODE) {
				CFCSDataSet writeSet = writeSystem.createDataSet(readSet);

				CFCSParameters readParam = readSet.getParameters();
				CFCSParameters writeParam = writeSet.getParameters();
				
				for (int i = 0, count = writeParam.getCount(); i < count; i++) {
					CFCSParameter parameter = writeParam.getParameter(i);
					parameter.setFieldSize(rangeToBits(parameter.getRange()));
					writeParam.replaceParameter(i, parameter);
					}

				CFCSData writeData = writeSet.getData();

				CFCSListModeData readList = (CFCSListModeData) readData;
				CFCSListModeData writeList = (CFCSListModeData) writeData;

				// allocate an array to hold one event
				int[] event = new int[readParam.getCount()];

				int nEvents = readList.getCount();

				for (int i = 0; i < nEvents; i++) {
					readList.getEvent(i, event);
					writeList.addEvent(event);
					}	
				}
			}

		readSystem.close();
		writeSystem.close();
		}
	}
