package org.flowcyt.cfcs;

// JS
public class CFCSSpillover {
	
	private double[][] spilloverCoefficients;
	private String[] parameterNames;
	
	CFCSSpillover(String spilloverKeywordValue) throws CFCSError {
		
		String[] sTmp = spilloverKeywordValue.split(",");
		if(sTmp.length < 2) throwCFCSIllegalValueError(spilloverKeywordValue);
		
		int n = 0;
		try { n = Integer.parseInt(sTmp[0]); }
		catch (Exception e) { throwCFCSIllegalValueError(spilloverKeywordValue); }
		
		if(sTmp.length != 1+n+n*n) throwCFCSIllegalValueError(spilloverKeywordValue);
		
		parameterNames = new String[n];
		spilloverCoefficients = new double[n][n];
		
		for(int i = 0; i < n; i++) {
			parameterNames[i] = sTmp[i+1];
		}

		for(int i = 0; i < n; i++) {
			for(int j = 0; j < n; j++) {
				try { spilloverCoefficients[i][j] = Double.parseDouble(sTmp[1+n+n*i+j]); }
				catch (Exception e) { throwCFCSIllegalValueError(spilloverKeywordValue); }
			}
		}

	}
	
	String getSpilloverKeywordValue() {
		int n = parameterNames.length;
		String ret = "" + n;
		for(int i = 0; i < n; i++) ret += "," + parameterNames[i];
		for(int i = 0; i < n; i++) {
			for(int j = 0; j < n; j++) {
				ret += "," + spilloverCoefficients[i][j];
			}
		}
		
		return ret;
	}
	
	private void throwCFCSIllegalValueError(String s) throws CFCSError {
		throw new CFCSError(CFCSErrorCodes.CFCSIllegalValue, "Spillover " + s);
	}
	
	public final String[] getParameterNames() {
		int n = parameterNames.length;
		String[] names = new String[n]; 
		System.arraycopy(parameterNames, 0, names, 0, n);
		return names;
	}
	
	public final double[][] getSpilloverCoefficients() {
		int n = parameterNames.length;
		double[][] values = new double[n][n]; 
		for(int i = 0; i < n; i++) { System.arraycopy(spilloverCoefficients[i], 0, values[i], 0, n); }
		return values;
	}
	
	public final int getParameterCount() {
		return parameterNames.length;
	}
	
	public final String getParameterName(int parameterIndex) {
		if(parameterIndex >= 0 && parameterIndex < parameterNames.length) return parameterNames[parameterIndex];
		else return null;
	}
	
	public final int getParameterIndex(String parameterName) {
		int n = parameterNames.length;
		for(int i = 0; i < n; i++) {
			if(parameterNames[i].compareToIgnoreCase(parameterName) == 0) return i;
		}
		return -1;
	}
	
	public final double getSpilloverCoefficient(int i, int j) {
		if(i >= 0 && j >= 0 && i < parameterNames.length && j < parameterNames.length) return spilloverCoefficients[i][j];
		else return Double.NaN;
	}
	
	public final double getSpilloverCoefficient(String fromParameterName, String toParameterName) {
		int i = -1, j = -1, n = parameterNames.length;
		for(int x = 0; x < n; x++) {
			if(parameterNames[x].compareToIgnoreCase(fromParameterName) == 0) i = x;
			if(parameterNames[x].compareToIgnoreCase(toParameterName) == 0) j = x;
		}
		return getSpilloverCoefficient(i, j);
	}
	
	/**
	 * Set a spillover coefficient, return true if succeeded, false otherwise (e.g., index out of range) 
	 * @param i spillover coefficient from parameter i
	 * @param j spillover coefficient to parameter j
	 * @param spilloverCoefficient spillover coefficient to be set
	 * @return true if succeeded, false otherwise (e.g., index out of range) 
	 */
	public final boolean setSpilloverCoefficient(int i, int j, double spilloverCoefficient) {
		if(i >= 0 && j >= 0 && i < parameterNames.length && j < parameterNames.length) spilloverCoefficients[i][j] = spilloverCoefficient;
		else return false;
		return true;
	}
	
	public final boolean addSpilloverParameter(String parameterName) {
		int n = parameterNames.length;
		double[] s = new double[n+1];
		for(int i = 0; i < n; i++) s[i] = 0;
		s[n] = 1;
		return addSpilloverParameter(parameterName, s, s);
	}
	
	public final boolean addSpilloverParameter(String parameterName, double[] spilloverFromValues, double[] spilloverToValues) {
		int n = parameterNames.length;
		if(spilloverFromValues == null || spilloverFromValues.length != n+1 || 
		   spilloverToValues == null || spilloverToValues.length != n+1) return false;
		for(int i = 0; i < n; i++) if(parameterNames[i].compareToIgnoreCase(parameterName) == 0) return false;
		if(parameterName.indexOf(",") != -1) return false;
		
		CFCSSpillover oldCopy = createSpilloverMatrix(this);
		
		this.parameterNames = new String[n+1];
		this.spilloverCoefficients = new double[n+1][n+1];
		
		System.arraycopy(oldCopy.parameterNames, 0, parameterNames, 0, n);
		parameterNames[n] = parameterName;
		for(int i = 0; i < n; i++) { 
			System.arraycopy(oldCopy.spilloverCoefficients[i], 0, spilloverCoefficients[i], 0, n); 
		}
		
		for(int i = 0; i <= n; i++) {
			spilloverCoefficients[n][i] = spilloverFromValues[i];
			spilloverCoefficients[i][n] = spilloverToValues[i];
		}
		
		return true;
	}
	
	public static CFCSSpillover createSpilloverMatrix(String[] parameterNames, double[][] spilloverCoefficients) throws CFCSError {
		return new CFCSSpillover(parameterNames, spilloverCoefficients);
	}
	
	public static CFCSSpillover createSpilloverMatrix(CFCSSpillover sourceMatrix) throws CFCSError {
		return createSpilloverMatrix(sourceMatrix.getParameterNames(), sourceMatrix.getSpilloverCoefficients());
	}

	private CFCSSpillover(String[] parameterNames, double[][] spilloverCoefficients) throws CFCSError {
		int n = parameterNames.length;
		if(spilloverCoefficients.length != n) throwCFCSIllegalValueError("");
		for(int i = 0; i < n; i++) if(spilloverCoefficients[i].length != n) throwCFCSIllegalValueError("");
		
		this.parameterNames = new String[n];
		this.spilloverCoefficients = new double[n][n];
		
		System.arraycopy(parameterNames, 0, this.parameterNames, 0, n);
		for(int i = 0; i < n; i++) { System.arraycopy(spilloverCoefficients[i], 0, this.spilloverCoefficients[i], 0, n); }
	}
	
}
