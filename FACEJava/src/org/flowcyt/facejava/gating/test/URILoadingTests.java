package org.flowcyt.facejava.gating.test;

import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;

import org.flowcyt.facejava.gating.gates.GateSet;
import org.flowcyt.facejava.gating.xmlio.GatingMLFileReader;
import org.junit.Assert;
import org.junit.Test;

/**
 * Test loading with URIs.
 * 
 * @author echng
 */
public class URILoadingTests {
	private static final String REAL_GATING_FILE = GateTestHarness.GATING_TEST_FILE_DIRECTORY + "CombinedGates.xml";
	
	@Test(expected=URISyntaxException.class)
	public void testInvalidURI() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader("http://a\\8080:80/test.fcs");
		reader.read();
	}
	
	@Test(expected=MalformedURLException.class)
	public void testNoProtocolURL() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader("no/scheme/url/test.fcs");
		reader.read();
	}
	
	@Test(expected=MalformedURLException.class)
	public void testInvalidProtocolURL() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader("asdas://bad/scheme/url/test.fcs");
		reader.read();
	}
	
	@Test(expected=IOException.class)
	public void testURLToNonExistentFile() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader("file:///src/org/flowcyt/gating/daasd/test.xml");
		reader.read();
	}
	
	@Test public void testLocalFileLoad() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(new File(REAL_GATING_FILE.replace("file:", "")));
		GateSet gc = reader.read(); 
		Assert.assertNotNull(gc);
		Assert.assertEquals(91, gc.size());
	}
	
	@Test public void testURILoad() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(new URI(REAL_GATING_FILE));
		GateSet gc = reader.read(); 
		Assert.assertNotNull(gc);
		Assert.assertEquals(91, gc.size());
	}
	
	@Test public void testURIStringLoad() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(REAL_GATING_FILE);
		GateSet gc = reader.read(); 
		Assert.assertNotNull(gc);
		Assert.assertEquals(91, gc.size());
	}
	
	@Test public void testURLLoad() throws Exception {
		GatingMLFileReader reader = new GatingMLFileReader(new URL(REAL_GATING_FILE));
		GateSet gc = reader.read(); 
		Assert.assertNotNull(gc);
		Assert.assertEquals(91, gc.size());
	}
}
