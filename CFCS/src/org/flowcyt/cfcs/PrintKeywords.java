package org.flowcyt.cfcs;

// Read in an FCS file, and prints the version
// and all associated keywords for each data set.

// Usage: java PrintKeywords file:source.fcs


public class PrintKeywords {

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
			CFCSKeywords fcsKeywords = null;

			try {
				set = system.getDataSet(iSet);
				fcsKeywords = set.getKeywords();
				}
			catch (CFCSError error) { if (failIfError(error) != 0) break; }

			String version = set.getVersion();

			System.out.println("Keywords for data set #" + (iSet + 1) + " (" + version + ")\n");

			int count = fcsKeywords.getCount();

			for (int idx = 0; idx < count; idx++) {
				CFCSKeyword keyword = fcsKeywords.getKeyword(idx);
				String keyName = keyword.getKeywordName();
				String keyValue = keyword.getKeywordValue();

				System.out.println(keyName + ": " + keyValue);
				}
				
			if (iSet < nDataSets - 1) System.out.println();
			}
			
		system.close();
		}
	}
