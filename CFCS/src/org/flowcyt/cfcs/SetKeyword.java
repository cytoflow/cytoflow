package org.flowcyt.cfcs;

// A simple test of the unofficial non-API modify() method of CFCSSystem
// Usage: java SetKeyword file:input.fcs file:output.fcs '$classes' 'This FCS modified by me.'


public class SetKeyword {
	
	private static final int INPUT = 0, OUTPUT = 1, NAME = 2, VALUE = 3;

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

		try { system.modify(argv[INPUT], argv[OUTPUT]); }
		catch (CFCSError error) { if (failIfError(error) != 0) System.exit(1); }

		CFCSKeyword keyword = new CFCSKeyword();
		
		keyword.setKeywordName(argv[NAME]);
		keyword.setKeywordValue(argv[VALUE]);
		keyword.setKeywordSource(CFCSDataSet.TEXT);

		int nDataSets = system.getCount();

		for (int i = 0; i < nDataSets; i++) {
			CFCSDataSet dataset = system.getDataSet(i);

			CFCSKeywords keywords = dataset.getKeywords();

			keywords.addKeyword(keyword);
			}

		system.close();
		}
	}
