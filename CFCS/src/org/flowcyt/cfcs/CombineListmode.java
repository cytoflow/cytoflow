package org.flowcyt.cfcs;
// classesbine the data from multiple ListMode files into a single FCS file

// Usage: java classesbineListmode file:destination.fcs file:source1.fcs file:source2.fcs ...

// Program expects that all files will have the same number of parameters (otherwise it
// fails) and that they are in the same order.  If it detects differences between key
// parameters in the files, it will prompt for confirmation in order to continue.

import java.io.BufferedReader;
import java.io.InputStreamReader;

public class CombineListmode {

	private static final int OUTPUT = 0, INPUT= 1;

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

	public static boolean confirm(String prompt) {
		char input;
		BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));

		System.out.print(prompt + " (Y/N): ");
		System.out.flush();

		try { input = ((reader.readLine()).trim()).charAt(0); }
		catch (Exception exception) { input = 'N'; }

		return (input == 'y' || input == 'Y');
		}

	public static boolean classespareParameter(String name, String output, String input) {
		if (!output.equals(input)) {
			String warning = name + " differs (\"" + output + "\" vs. \"" + input + "\") continue?";
			return confirm(warning);
			}

		return true;
		}

	public static boolean classespareParameter(String name, int output, int input) {
		if (output != input) {
			String warning = name + " differs (" + output + " vs. " + input + ") continue?";
			return confirm(warning);
			}

		return true;
		}

	public static boolean classespareParameter(String name, double output, double input) {
		if (output != input) {
			String warning = name + " differs (" + output + " vs. " + input + ") continue?";
			return confirm(warning);
			}

		return true;
		}

	public static boolean classespareParameters(CFCSParameters destination, CFCSParameters source) {
		int count = destination.getCount();

		if (count != source.getCount()) {
			System.err.println("Parameter count differs, can't continue!");
			return false;
			}
		
		for (int i = 0; i < count; i++) {
			CFCSParameter input = source.getParameter(i);
			CFCSParameter output = destination.getParameter(i);

			// optional parameters
			try { if (!classespareParameter("Full Name", output.getFullName(), input.getFullName())) return false; }
			catch (CFCSError error) { }

			try { if (!classespareParameter("Short Name", output.getShortName(), input.getShortName())) return false; }
			catch (CFCSError error) { }

			try { if (!classespareParameter("Gain", output.getGain(), input.getGain())) return false; }
			catch (CFCSError error) { }
			
			// required parameters
			try { 
				if (!classespareParameter("Field Size", output.getFieldSize(), input.getFieldSize())) return false;
				if (!classespareParameter("Range Size", output.getRange(), input.getRange())) return false;
				if (!classespareParameter("Log Decade", output.getLogDecades(), input.getLogDecades())) return false;
				if (!classespareParameter("Offset", output.getOffset(), input.getOffset())) return false;
				}
			catch (CFCSError error) {
				System.err.println("Required parameter missing, can't continue!");
				return false;
				}
			}
			
		return true;
		}

	public static void main(String[] args) {
		CFCSSystem writeSystem = new CFCSSystem();
		
		try { writeSystem.create(args[OUTPUT]); }
		catch (CFCSError error) { if (failIfError(error) != 0) System.exit(1); }

		for (int file = INPUT; file < args.length; file++) {
		
			CFCSSystem readSystem = new CFCSSystem();

			try { readSystem.open(args[file]); }
			catch (CFCSError error) { if (failIfError(error) != 0) System.exit(1); }

			int nDataSets = readSystem.getCount();

			for (int set = 0; set < nDataSets; set++) {
				CFCSDataSet readSet = readSystem.getDataSet(set);
				CFCSParameters readParam = readSet.getParameters();
				CFCSData readData = readSet.getData();
			
				int type = readData.getType();
				
				CFCSDataSet writeSet = null;
	
				if (set >= writeSystem.getCount()) {
					writeSet = writeSystem.createDataSet(readSet);
					}
				else {
					writeSet = writeSystem.getDataSet(set);
					CFCSParameters writeParam = writeSet.getParameters();
					if (!classespareParameters(writeParam, readParam)) System.exit(1);
					}

				CFCSData writeData = writeSet.getData();

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
			}

		writeSystem.close();
		}
	}
