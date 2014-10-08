package org.flowcyt.cfcs;
// Convert any two parameters of all ListMode datasets in an FCS
// file to a (possibly multi-dataset) Correlated histogram FCS file

// Usage: java ListModeToCorrelated file:src.fcs file:dst.fcs 2 5

// Note: if not supplied, parameters default to #1 and #2

// Warning: this can generate very large FCS files!


public class ListModeToCorrelated {

	private static final int INPUT = 0, OUTPUT = 1, PARM1 = 2, PARM2 = 3;
	
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
		
		int index_one = 0, index_two = 1;
		
		if (argv.length > PARM1) {
			index_one = (new Integer(argv[PARM1])).intValue() - 1;

			if (argv.length > PARM2) {
				index_two = (new Integer(argv[PARM2])).intValue() - 1;
				}
			}

		try { read_system.open(argv[INPUT]); }
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
				CFCSDataSet write_set = write_system.createDataSet(CFCSData.CORRELATED);
				CFCSData write_data = write_set.getData();

				CFCSListModeData read_list = (CFCSListModeData) read_data;
				CFCSCorrelatedData write_histogram = (CFCSCorrelatedData) write_data;

				CFCSParameters read_parameters = read_set.getParameters();
				CFCSParameters write_parameters = write_set.getParameters();
				
				CFCSParameter parameter_one = read_parameters.getParameter(index_one);
				CFCSParameter parameter_two = read_parameters.getParameter(index_two);
				
				int range_one = parameter_one.getRange();
				int range_two = parameter_two.getRange();
				
				parameter_one.setFieldSize(BITSPERINT);
				parameter_two.setFieldSize(BITSPERINT);
					
				write_parameters.addParameter(parameter_one);
				write_parameters.addParameter(parameter_two);

				int[][] histogram = new int[range_two][range_one];

				// allocate an array to hold one event

				int[] event = new int[read_parameters.getCount()];

				int nEvents = read_list.getCount();

				for (int j = 0; j < nEvents; j++) {
					read_list.getEvent(j, event);
					histogram[event[index_two]][event[index_one]]++;
					}	

				write_histogram.setArray(histogram);
				}
			}

		write_system.close();
		read_system.close();
		}
	}
