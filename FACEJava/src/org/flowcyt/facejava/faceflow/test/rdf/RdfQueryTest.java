package org.flowcyt.facejava.faceflow.test.rdf;

import org.flowcyt.facejava.faceflow.exception.DuplicateRelationException;
import org.flowcyt.facejava.faceflow.relations.CompensationRelation;
import org.flowcyt.facejava.faceflow.relations.GatingRelation;
import org.flowcyt.facejava.faceflow.relations.Relation;
import org.flowcyt.facejava.faceflow.relations.RelationVisitor;
import org.flowcyt.facejava.faceflow.relations.RelationsRepository;
import org.flowcyt.facejava.faceflow.relations.TransformationRelation;
import org.flowcyt.facejava.faceflow.relations.VisitMethod;
import org.flowcyt.facejava.faceflow.relations.rdf.RdfRelationsRepository;
import org.flowcyt.facejava.faceflow.test.TestFileConstants;
import org.junit.Assert;
import org.junit.BeforeClass;
import org.junit.Test;

public class RdfQueryTest {
	
	private static RelationsRepository repository;
	
	@BeforeClass
	public static void oneTimeSetUp() throws Exception {
		repository = new RdfRelationsRepository(TestFileConstants.RDF_TEST_FILE_DIRECTORY + "QueryTest.rdf");
	}
	
	@Test public void testDatafileDS1() throws Exception {
		TestRelationsVisitor tester = new TestRelationsVisitor("file:gating.xml", null, null, null, "file:transformation.xml");
		for (Relation rel : repository.getRelations("file:datafile.fcs", 1)) {
			Assert.assertTrue(tester.dispatch(rel));
		}
	}
	
	@Test public void testDatafileDS2() throws Exception {
		TestRelationsVisitor tester = new TestRelationsVisitor("file:override-gating.xml", null, "file:compensation.xml", "matrix", "file:transformation.xml");
		for (Relation rel : repository.getRelations("file:datafile.fcs", 2)) {
			Assert.assertTrue(tester.dispatch(rel));
		}
	}
	
	@Test public void testDatafileDS3() throws Exception {
		TestRelationsVisitor tester = new TestRelationsVisitor("file:gating.xml", null, null, null, "file:transformation.xml");
		for (Relation rel : repository.getRelations("file:datafile.fcs", 3)) {
			Assert.assertTrue(tester.dispatch(rel));
		}
	}
	
	@Test public void testDatafile2DS1() throws Exception {
		TestRelationsVisitor tester = new TestRelationsVisitor(null, null, null, null, null);
		for (Relation rel : repository.getRelations("file:datafile2.fcs", 1)) {
			Assert.assertTrue(tester.dispatch(rel));
		}
	}
	
	@Test public void testDatafile2DS2() throws Exception {
		TestRelationsVisitor tester = new TestRelationsVisitor(null, null, null, null, null);
		for (Relation rel : repository.getRelations("file:datafile2.fcs", 2)) {
			Assert.assertTrue(tester.dispatch(rel));
		}
	}
	
	@Test public void testDatafile2DS3() throws Exception {
		TestRelationsVisitor tester = new TestRelationsVisitor("file:standalone-gating.xml", "gate", null, null, null);
		for (Relation rel : repository.getRelations("file:datafile2.fcs", 3)) {
			Assert.assertTrue(tester.dispatch(rel));
		}
	}
	
	@Test public void testDatafile2DS4() throws Exception {
		TestRelationsVisitor tester = new TestRelationsVisitor(null, null, null, null, null);
		for (Relation rel : repository.getRelations("file:datafile2.fcs", 4)) {
			Assert.assertTrue(tester.dispatch(rel));
		}
	}
	
	@Test(expected=DuplicateRelationException.class)
	public void testDatafile3DS1() throws Exception {
		repository.getRelations("file:datafile3.fcs", 1);
		
	}
	
	@Test(expected=DuplicateRelationException.class)
	public void testDatafile3DS2() throws Exception {
		repository.getRelations("file:datafile3.fcs", 2);
		
	}
	
	@Test public void testDatafile4DS1() throws Exception {
		TestRelationsVisitor tester = new TestRelationsVisitor(null, null, null, null, "file:transformation123.xml");
		for (Relation rel : repository.getRelations("file:datafile4.fcs", 1)) {
			Assert.assertTrue(tester.dispatch(rel));
		}
	}
	
	@Test(expected=DuplicateRelationException.class)
	public void testDatafile4DS2() throws Exception {
		repository.getRelations("file:datafile4.fcs", 2);
		
	}
	
	public static class TestRelationsVisitor extends RelationVisitor {
		private String gatingLocation;
		
		private String gateId;
		
		private String compensationLocation;
		
		private String matrixId;
		
		private String transformationLocation;
		
		public TestRelationsVisitor(String gatingLocation, String gateId, String compensationLocation, String matrixId, String transformationLocation) {
			super();
			this.gatingLocation = gatingLocation;
			this.gateId = gateId;
			this.compensationLocation = compensationLocation;
			this.matrixId = matrixId;
			this.transformationLocation = transformationLocation;
		}
		
		public Boolean dispatch(Relation rel) {
			return (Boolean) super.dispatch(rel);
		}

		@VisitMethod public Boolean visit(GatingRelation rel) {
			if (gatingLocation == null) {
				return false;
			}
			
			if (!gatingLocation.equals(rel.getLocation()))
				return false;
					
			
			if (gateId == null) {
				return rel.getGateId() == null;
			}
			
			return gateId.equals(rel.getGateId());
		}
		
		@VisitMethod public Boolean visit(CompensationRelation rel) {
			if (compensationLocation == null) {
				return false;
			}
			
			if (!compensationLocation.equals(rel.getLocation()))
				return false;		
			
			if (matrixId == null) {
				return rel.getMatrixId() == null;
			}
			
			return matrixId.equals(rel.getMatrixId());			
		}

		@VisitMethod public Boolean visit(TransformationRelation rel) {
			if (transformationLocation == null) {
				return false;
			}
			
			return transformationLocation.equals(rel.getLocation())	;
		}

		@Override public Boolean defaultVisit(Relation rel) {
			return true;
		}
		
	}
}
