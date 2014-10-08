package org.flowcyt.cfcs;
// Convert the ListMode datasets of an FCS file to an
// (possibly multi-dataset) Uncorrelated histogram FCS file

// Usage: java ListModeToUncorrelated file:source.fcs file:destination.fcs

// Warning: Assumes all $PnR are <= 2^16, adjust the type of the event[] 
// array and the index mask if you need to cope with larger ranges.


public class ListModeToUncorrelated {

	private static final int INPUT = 0, OUTPUT = 1;

	private static final int BITSPERINT = 32;

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
		CFCSSystem read_system = new CFCSSystem();

		try { read_system.open( argv[INPUT]); }
		catch (CFCSError error) {
			if (failIfError(error) != 0) System.exit(1);
			}

		CFCSSystem write_system = new CFCSSystem();

		try { write_system.create(argv[OUTPUT]); }
		catch (CFCSError error) {
			if (failIfError(error) != 0) System.exit(1);
			}

		int nDataSets = read_system.getCount();

		for (int iset = 0; iset < nDataSets; iset++) {
			CFCSDataSet read_set = read_system.getDataSet(iset);
			CFCSData read_data = read_set.getData();

			if (read_data.getType() == CFCSData.LISTMODE) {
				CFCSDataSet write_set = write_system.createDataSet(CFCSData.UNCORRELATED);
				CFCSData write_data = write_set.getData();

				CFCSListModeData read_list = (CFCSListModeData) read_data;
				CFCSUncorrelatedData write_histogram = (CFCSUncorrelatedData) write_data;

				CFCSParameters read_parameters = read_set.getParameters();
				CFCSParameters write_parameters = write_set.getParameters();
				
				int count = read_parameters.getCount();
				
				int[][] histogram = new int[count][];

				for (int i = 0; i < count; i++) {
					CFCSParameter parameter = read_parameters.getParameter(i);

					parameter.setFieldSize(BITSPERINT);

					write_parameters.addParameter(parameter);

					histogram[i] = new int[parameter.getRange()];
					}

				// allocate an array to hold one event
				short[] event = new short[read_parameters.getCount()];

				int nEvents = read_list.getCount();

				for (int j = 0; j < nEvents; j++) {
					read_list.getEvent(j, event);

					for (int i = 0; i < event.length; i++) {
						histogram[i][event[i] & 0xffff]++;
						}
					}	

				for (int i = 0; i < count; i++) {
					write_histogram.addArray(histogram[i]);
					}
				}
			}

		write_system.close();
		read_system.close();
		}
	}
