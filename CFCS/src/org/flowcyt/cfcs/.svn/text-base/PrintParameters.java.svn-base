package org.flowcyt.cfcs;

// Read in an FCS file, and print parameter descriptions for each data set.

// Usage: java PrintParameters file:source.fcs

/*
import CFCSDataSet;
import CFCSError;
import CFCSParameter;
import CFCSParameters;
import CFCSSystem;
*/

public class PrintParameters {

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
		CFCSSystem system = new CFCSSystem();

		try { system.open("http://www.flowjo.classes/Sample1.fcs"); }
		catch (CFCSError error) { if (failIfError(error) != 0) System.exit(1); }

		int nDataSets = system.getCount();

		for (int iSet = 0; iSet < nDataSets; iSet++) {
			CFCSDataSet set = null;
			CFCSParameters fcsParameters = null;

			System.out.println("Parameters for data set #" + (iSet + 1) + "\n");

			try {
				set = system.getDataSet(iSet);
				fcsParameters = set.getParameters();
				}
			catch (CFCSError error) { if (failIfError(error) != 0) break; }

			int count = fcsParameters.getCount();

			for (int idx = 0; idx < count; idx++) {
				CFCSParameter parameter = fcsParameters.getParameter(idx);
				String fullName = null, shortName = null;
				
				try { fullName = parameter.getFullName(); }
				catch (CFCSError error) { fullName = ""; }
				
				try { shortName = "(" + parameter.getShortName() + ")"; }
				catch (CFCSError error) { shortName = ""; }
				
				System.out.println("\t#" + (idx + 1) + " " + fullName + " " + shortName);

				// Required parameters:
				System.out.println("\t\tField Size: " + parameter.getFieldSize());
				System.out.println("\t\tRange: " + parameter.getRange());
				
				try {
					System.out.println("\t\tLog Decades: " + parameter.getLogDecades());
					System.out.println("\t\tOffset: " + parameter.getOffset());
					}
				catch (CFCSError error) { if (error.errorNumber < 0) break; }

				// Optional parameters:

				try {
					System.out.println("\t\tFilter: " + parameter.getFilter());
					}
				catch (CFCSError error) { if (error.errorNumber < 0) break; }
				
				try {
					System.out.println("\t\tDetector Type: " + parameter.getDetectorType());
					}
				catch (CFCSError error) { if (error.errorNumber < 0) break; }
				
				try {
					System.out.println("\t\tGain: " + parameter.getGain());
					}
				catch (CFCSError error) { }
				
				try {
					System.out.println("\t\tLaser Power: " + parameter.getLaserPower());
					}
				catch (CFCSError error) { if (error.errorNumber < 0) break; }

				try {
					System.out.println("\t\tEmitted Percent: " + parameter.getEmittedPercent());
					}
				catch (CFCSError error) { if (error.errorNumber < 0) break; }

				try {
					System.out.println("\t\tVoltage: " + parameter.getVoltage());
					}
				catch (CFCSError error) { if (error.errorNumber < 0) break; }

				try {
					System.out.println("\t\tExcitation Wavelength: " + parameter.getExcitationWavelength());
					}
				catch (CFCSError error) { if (error.errorNumber < 0) break; }

				if (idx < count) System.out.println();
				}
			if (iSet < nDataSets - 1) System.out.println();
			}

		system.close();
		}
	}
