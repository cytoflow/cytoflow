package org.flowcyt.facejava.transformation.test;

import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;

import org.flowcyt.facejava.transformation.TransformationCollection;
import org.flowcyt.facejava.transformation.xmlio.TransformationMLFileReader;
import org.junit.Assert;
import org.junit.Test;

/**
 * Transformation URI loading tests.
 * 
 * @author echng
 */
public class URILoadingTests {
	private static final String REAL_TRANFORMATION_FILE = TransformationTestHarness.TRANSFORMATION_TEST_FILE_DIRECTORY + "SimpleTransformations.xml";
	
	@Test(expected=URISyntaxException.class)
	public void testInvalidURI() throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader("http://a\\8080:80/test.fcs");
		reader.read();
	}
	
	@Test(expected=MalformedURLException.class)
	public void testNoProtocolURL() throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader("no/scheme/url/test.fcs");
		reader.read();
	}
	
	@Test(expected=MalformedURLException.class)
	public void testInvalidProtocolURL() throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader("asdas://bad/scheme/url/test.fcs");
		reader.read();
	}
	
	@Test(expected=IOException.class)
	public void testURLToNonExistentFile() throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader("file:///src/org/flowcyt/gating/daasd/test.xml");
		reader.read();
	}
	
	@Test public void testLocalFileLoad() throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader(new File(REAL_TRANFORMATION_FILE.replace("file:", "")));
		TransformationCollection tc = reader.read(); 
		Assert.assertNotNull(tc);
		Assert.assertEquals(9, tc.size());
	}
	
	@Test public void testURILoad() throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader(new URI(REAL_TRANFORMATION_FILE));
		TransformationCollection tc = reader.read(); 
		Assert.assertNotNull(tc);
		Assert.assertEquals(9, tc.size());
	}
	
	@Test public void testURIStringLoad() throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader(REAL_TRANFORMATION_FILE);
		TransformationCollection tc = reader.read(); 
		Assert.assertNotNull(tc);
		Assert.assertEquals(9, tc.size());
	}
	
	@Test public void testURLLoad() throws Exception {
		TransformationMLFileReader reader = new TransformationMLFileReader(new URL(REAL_TRANFORMATION_FILE));
		TransformationCollection tc = reader.read(); 
		Assert.assertNotNull(tc);
		Assert.assertEquals(9, tc.size());
	}
}
