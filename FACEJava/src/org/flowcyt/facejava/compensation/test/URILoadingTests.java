package org.flowcyt.facejava.compensation.test;

import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;

import org.flowcyt.facejava.compensation.SpilloverMatrixSet;
import org.flowcyt.facejava.compensation.xmlio.CompensationMLFileReader;
import org.junit.Assert;
import org.junit.Test;

/**
 * Tests various cases when loading with URIs
 * 
 * @author echng
 */
public class URILoadingTests {
	
	private static final String REAL_COMPENSATION_FILE = CompensatorTestHarness.TEST_FILE_DIRECTORY + "CompensationExample.xml";
	@Test(expected=URISyntaxException.class)
	public void testInvalidURI() throws Exception {
		CompensationMLFileReader reader = new CompensationMLFileReader("http://a\\8080:80/test.fcs");
		reader.read();
	}
	
	@Test(expected=MalformedURLException.class)
	public void testNoProtocolURL() throws Exception {
		CompensationMLFileReader reader = new CompensationMLFileReader("no/scheme/url/test.fcs");
		reader.read();
	}
	
	@Test(expected=MalformedURLException.class)
	public void testInvalidProtocolURL() throws Exception {
		CompensationMLFileReader reader = new CompensationMLFileReader("asdas://bad/scheme/url/test.fcs");
		reader.read();
	}
	
	@Test(expected=IOException.class)
	public void testURLToNonExistentFile() throws Exception {
		CompensationMLFileReader reader = new CompensationMLFileReader("file:///src/org/flowcyt/gating/daasd/test.xml");
		reader.read();
	}
	
	@Test public void testLocalFileLoad() throws Exception {
		CompensationMLFileReader reader = new CompensationMLFileReader(new File(REAL_COMPENSATION_FILE.replace("file:", "")));
		SpilloverMatrixSet smc = reader.read(); 
		Assert.assertNotNull(smc);
		Assert.assertEquals(2, smc.size());
	}
	
	@Test public void testURILoad() throws Exception {
		CompensationMLFileReader reader = new CompensationMLFileReader(new URI(REAL_COMPENSATION_FILE));
		SpilloverMatrixSet smc = reader.read(); 
		Assert.assertNotNull(smc);
		Assert.assertEquals(2, smc.size());
	}
	
	@Test public void testURIStringLoad() throws Exception {
		CompensationMLFileReader reader = new CompensationMLFileReader(REAL_COMPENSATION_FILE);
		SpilloverMatrixSet smc = reader.read(); 
		Assert.assertNotNull(smc);
		Assert.assertEquals(2, smc.size());
	}
	
	@Test public void testURLLoad() throws Exception {
		CompensationMLFileReader reader = new CompensationMLFileReader(new URL(REAL_COMPENSATION_FILE));
		SpilloverMatrixSet smc = reader.read(); 
		Assert.assertNotNull(smc);
		Assert.assertEquals(2, smc.size());
	}
}
