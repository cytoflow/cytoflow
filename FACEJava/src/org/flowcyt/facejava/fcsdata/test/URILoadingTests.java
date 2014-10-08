package org.flowcyt.facejava.fcsdata.test;

import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.net.URISyntaxException;

import org.flowcyt.facejava.fcsdata.impl.FcsDataFile;
import org.flowcyt.facejava.fcsdata.io.CFCSInput;
import org.flowcyt.facejava.fcsdata.io.FcsInput;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;

/**
 * Test loading with various valid and invalid URIs, strings, and files.
 * 
 * @author echng
 */
public class URILoadingTests {
	
	private static final String REAL_FCS_FILE = DataFileTestHarness.TEST_FILE_DIRECTORY + "int-15_events.fcs";
	
	FcsInput adapter;
	
	@Before public void setUp() {
		adapter = new CFCSInput();
	}
	
	@Test(expected=URISyntaxException.class)
	public void testInvalidURI() throws Exception {
		adapter.read("http://a\\8080:80/test.fcs");
	}
	
	// Malformed URLS are masked by the CFCS library so we just get an IOException.
	@Test(expected=IOException.class)
	public void testNoProtocolURL() throws Exception {
		adapter.read("no/scheme/url/test.fcs");
	}

	// Malformed URLS are masked by the CFCS library so we just get an IOException.
	@Test(expected=IOException.class)
	public void testInvalidProtocolURL() throws Exception {
		adapter.read("notarealprotocol://bad/scheme/url/test.fcs");
	}
	
	@Test(expected=IOException.class)
	public void testURLToNonExistentFile() throws Exception {
		adapter.read("file:///src/org/flowcyt/fcsdata/daasd/test.fcs");
	}
	
	@Test public void testStringFileLoad() throws Exception {
		FcsDataFile popColl = adapter.read(REAL_FCS_FILE);
		Assert.assertNotNull(popColl);
		Assert.assertEquals(1, popColl.size());
		Assert.assertEquals(15, popColl.getByDataSetNumber(1).size());
	}
	
	@Test public void testLocalFileLoad() throws Exception {
		FcsDataFile popColl = adapter.read(new File(REAL_FCS_FILE.replace("file:", "")));
		Assert.assertNotNull(popColl);
		Assert.assertEquals(1, popColl.size());
		Assert.assertEquals(15, popColl.getByDataSetNumber(1).size());
	}
	
	@Test public void testURILoad() throws Exception {
		FcsDataFile popColl = adapter.read(new URI(REAL_FCS_FILE));
		Assert.assertNotNull(popColl);
		Assert.assertEquals(1, popColl.size());
		Assert.assertEquals(15, popColl.getByDataSetNumber(1).size());
	}
	
	@Test public void testURIStringLoad() throws Exception {
		FcsDataFile popColl = adapter.read(REAL_FCS_FILE);
		Assert.assertNotNull(popColl);
		Assert.assertEquals(1, popColl.size());
		Assert.assertEquals(15, popColl.getByDataSetNumber(1).size());
	}
}
