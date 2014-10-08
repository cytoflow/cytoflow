package org.flowcyt.facejava.gating.gates.bool;

import java.util.Set;

import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.Population;
import org.flowcyt.facejava.fcsdata.exception.DataRetrievalException;
import org.flowcyt.facejava.gating.exception.InvalidGateDescriptionException;
import org.flowcyt.facejava.gating.gates.AbstractGate;
import org.flowcyt.facejava.gating.gates.Gate;
import org.flowcyt.facejava.gating.gates.GateSet;
import org.flowcyt.facejava.gating.gates.GateSubPopulation;

/**
 * <p>
 * ProxyGates are used when a BooleanGate refers to a Gate that may not have been
 * created yet. It should only be used when Gating-ML files are being loaded since
 * if Gates are being created programmatically it should not be a problem to sequence
 * Gate creation such that the BooleanGates only use gates that are already created.
 * 
 * <p>
 * ProxyGate's are given the id of the gate being referred to and the GateSet to use
 * to map the id to the actual Gate. Thus, the GateSet <b>must</b> contain the referred
 * to Gate when this ProxyGate is used for any analysis. All method calls are 
 * delegated to the referred to gate. Also, the id of this gate is the same as the
 * referred to Gate. Thus, the ProxyGate and the Gate it refers to are equal in 
 * identity and behaviour.  
 * 
 * <p>
 * ProxyGates <i>must</i> not be added to GateSets since they are for internal use by
 * BooleanGates.
 * 
 * @author echng
 */
public class ProxyGate extends AbstractGate {
	
	/**
	 * The GateSet to use to lookup the referred to Gate by the gate id.
	 */
	private GateSet resolver;
	
	/**
	 * We'll cache the Gate that's looked up.
	 */
	private Gate resolvedGate;
	
	/**
	 * Constructor. Creates a ProxyGate which uses the Gate with the given id that is,
	 * or will be, in the given GateSet for all its behaviour. 
	 *  
	 * @param gateRefId The id of the gate being referred to.
	 * @param resolver The GateSet the referred to Gate is, or will be, in. It will
	 * be used to perform the lookup by gate id. 
	 */
	public ProxyGate(String gateRefId, GateSet resolver) {
		super(gateRefId);
		this.resolver = resolver;
	}
	
	/**
	 * @return Resolves the gate reference using the GateSet and returns the referred
	 * to Gate.
	 */
	private Gate getResolvedGate() {
		if (resolvedGate == null) {
			resolvedGate = resolver.get(this.getId());
		}
		return resolvedGate;
	}

	public Set<Gate> getDirectDependencies() {
		return getResolvedGate().getDirectDependencies();
	}

	public GateSubPopulation isInside(Population population) throws DataRetrievalException {
		return getResolvedGate().isInside(population);
	}

	public GateSubPopulation isInside(Population population, DataRetriever retriever) throws DataRetrievalException {
		return getResolvedGate().isInside(population, retriever);
	}

	public boolean isInside(Event ev, DataRetriever retriever) 	throws DataRetrievalException {
		return getResolvedGate().isInside(ev, retriever);
	}

	public void validate() throws InvalidGateDescriptionException {
		getResolvedGate().validate();
	}

	public String toString() {
		return getResolvedGate().toString();
	}
}
