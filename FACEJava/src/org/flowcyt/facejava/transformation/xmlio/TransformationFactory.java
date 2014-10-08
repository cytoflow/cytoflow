package org.flowcyt.facejava.transformation.xmlio;

import org.flowcyt.facejava.fcsdata.ParameterReference;
import org.flowcyt.facejava.transformation.BiExponentialTransformation;
import org.flowcyt.facejava.transformation.HyperlogTransformation;
import org.flowcyt.facejava.transformation.LinearTransformation;
import org.flowcyt.facejava.transformation.LnTransformation;
import org.flowcyt.facejava.transformation.LogTransformation;
import org.flowcyt.facejava.transformation.LogicleTransformation;
import org.flowcyt.facejava.transformation.QuadraticTransformation;
import org.flowcyt.facejava.transformation.SplitScaleTransformation;
import org.flowcyt.facejava.transformation.Transformation;
import org.flowcyt.facejava.transformation.UniversalTransformation;
import org.flowcyt.facejava.transformation.exception.InvalidTransformationException;
import org.flowcyt.facejava.transformation.jaxb.BiExponential;
import org.flowcyt.facejava.transformation.jaxb.Hyperlog;
import org.flowcyt.facejava.transformation.jaxb.Linear;
import org.flowcyt.facejava.transformation.jaxb.Ln;
import org.flowcyt.facejava.transformation.jaxb.Log;
import org.flowcyt.facejava.transformation.jaxb.Logicle;
import org.flowcyt.facejava.transformation.jaxb.ParameterTransformation;
import org.flowcyt.facejava.transformation.jaxb.PreDefined;
import org.flowcyt.facejava.transformation.jaxb.Quadratic;
import org.flowcyt.facejava.transformation.jaxb.SplitScale;
import org.flowcyt.facejava.transformation.jaxb.Universal;

/**
 * <p>
 * Used to create Tranformation objects given the transformation element that has been
 * mapped to a JAXB class.
 * 
 * @author echng
 */
public class TransformationFactory {
		
	/**
	 * Creates the transformation.
	 * 
	 * @param trans The JAXB ParameterTranformation element.
	 * @return Returns a Transformation object for the given element.
	 * @throws InvalidTransformationException Thrown if the Transformation couldn't be
	 * created for some reason.
	 */
	public static Transformation createTransformation(ParameterTransformation trans) throws InvalidTransformationException {
		Transformation rv = null;
		if (trans.getPreDefined() != null) {
			rv = createPreDefinedTransformation(trans.getNewName(), trans.getPreDefined());
		} else if (trans.getUniversal() != null) {
			rv = createUniversal(trans.getNewName(), trans.getUniversal());
		} else
			throw new InvalidTransformationException("Neither PreDefined nor Universal transformation specified");
		
		return rv;
	}
	
	/**
	 * Creates a Transformation objects for one of the Pre-Defined transformation elements.
	 * 
	 * @param name The newName attribute of the ParameterTransformation element
	 * @param trans The JAXB PreDefined element.
	 * @return Returns the created Transformation.
	 * @throws InvalidTransformationException Thrown if the Transformation couldn't be
	 * created for some reason.
	 */
	private static Transformation createPreDefinedTransformation(String name, PreDefined trans) throws InvalidTransformationException {
		Transformation rv;
		if (trans.getBiExponential() != null) {
			rv = createBiexponential(name, trans.getBiExponential());
		} else if (trans.getHyperlog() != null) {
			rv = createHyperlog(name, trans.getHyperlog());
		} else if (trans.getLinear() != null) {
			rv = createLinear(name, trans.getLinear());
		} else if (trans.getLn() != null) {
			rv = createLn(name, trans.getLn());
		} else if (trans.getLog() != null) {
			rv = createLog(name, trans.getLog());
		} else if (trans.getLogicle() != null) {
			rv = createLogicle(name, trans.getLogicle());
		} else if (trans.getQuadratic() != null) {
			rv = createQuadratic(name, trans.getQuadratic());
		} else if (trans.getSplitScale() != null) {
			rv = createSplitScale(name, trans.getSplitScale());
		} else
			throw new InvalidTransformationException("No Pre-Defined Transformation was defined.");
		
		return rv;
	}
	
	// Actual Gate creation methods here. Should be straightforward.
	
	private static BiExponentialTransformation createBiexponential(String name, BiExponential biex) {
		return new BiExponentialTransformation(name, new ParameterReference(biex.getParameter()), biex.getA(), biex.getB(), biex.getC(), biex.getD(), biex.getF());
	}
	
	private static HyperlogTransformation createHyperlog(String name, Hyperlog hlog) {
		return new HyperlogTransformation(name, new ParameterReference(hlog.getParameter()), hlog.getB(), hlog.getD(), hlog.getR());		
	}
	
	private static LinearTransformation createLinear(String name, Linear lin) {
		return new LinearTransformation(name, new ParameterReference(lin.getParameter()), lin.getA(), lin.getB());
	}
	
	private static LnTransformation createLn(String name, Ln ln) {
		return new LnTransformation(name, new ParameterReference(ln.getParameter()), ln.getR(), ln.getD());
	}
	
	private static LogicleTransformation createLogicle(String name, Logicle logi) throws InvalidTransformationException  {
		return new LogicleTransformation(name, new ParameterReference(logi.getParameter()), logi.getT(), logi.getW(), logi.getM());
	}
	
	private static LogTransformation createLog(String name, Log log) {
		return new LogTransformation(name, new ParameterReference(log.getParameter()), log.getR(), log.getD(), log.getLogbase());
	}
	
	private static QuadraticTransformation createQuadratic(String name, Quadratic quad) {
		return new QuadraticTransformation(name, new ParameterReference(quad.getParameter()), quad.getA(), quad.getB(), quad.getC());
	}
	
	private static SplitScaleTransformation createSplitScale(String name, SplitScale ss) {
		return new SplitScaleTransformation(name, new ParameterReference(ss.getParameter()), ss.getR(), ss.getMaxValue(), ss.getTransitionChannel());
	}
	
	/**
	 * All the Universal Transformations shenanigans we have to go through for Archimedes MathJ
	 * is in the UniversalTransformation Factory.
	 */
	private static UniversalTransformation createUniversal(String name, Universal uni) throws InvalidTransformationException {
		return UniversalTransformationFactory.createUniversal(name, uni.getMath());
	}
}
