package org.flowcyt.cfcs;


// Pack the data in a ListMode FCS file of type $DATATYPE/I

// Usage: java PackToRange file:unpacked.fcs file:packed.fcs


public class PackToRange {

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

	public static int rangeBits(int range) {
		int bits = 1, mask = 1;

		range--;

		while ((range | mask) != mask) {
			mask = (mask << 1) + 1;
			++bits;
			}

		return bits;
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
			CFCSParameters readParam = readSet.getParameters();
			CFCSData readData = readSet.getData();
			
			int type = readData.getType();

			CFCSDataSet writeSet = writeSystem.createDataSet(readSet);
			CFCSParameters writeParam = writeSet.getParameters();
			CFCSData writeData = writeSet.getData();

			for (int i = 0, count = writeParam.getCount(); i < count; i++) {
				CFCSParameter parameter = writeParam.getParameter(i);
				parameter.setFieldSize(rangeBits(parameter.getRange()));
				writeParam.replaceParameter(i, parameter);
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

				default: System.exit(1);	
				}
			}

		readSystem.close();
		writeSystem.close();
		}
	}
