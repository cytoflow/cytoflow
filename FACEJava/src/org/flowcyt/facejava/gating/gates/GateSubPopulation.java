package org.flowcyt.facejava.gating.gates;

import java.util.Collection;

import org.flowcyt.facejava.fcsdata.AbstractOrderedPopulation;
import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Event;
import org.flowcyt.facejava.fcsdata.Population;

/**
 * <p>
 * Contains the results of applying a Gate to a Population from an FCS data file. The result is
 * itself a Population whose parent Population is the analyzed Population (since it contains a
 * subset of the events of the analyzed Population). 
 *  
 * @author echng
 */
public class GateSubPopulation extends AbstractOrderedPopulation {
	// XXX: The fact that the result of applying a gate is another population can be used to
	// implement sequential gating if needed.
	
	/**
	 * The Gate that was applied to the Population.
	 */
	private Gate gate;
	
	/**
	 * The DataRetriever that was used to gate on the gated Population
	 */
	private DataRetriever retriever;
	
	/**
	 * Constructor. Creates a GateSubPopulation which contains a subset of the events in the
	 * given Population (given by insideEvents).
	 *  
	 * @param gatedPopulation The Population that was gated upon/
	 * @param retriever The DataRetriever used during Gating
	 * @param gate The Gate that was applied to the Population.
	 * @param insideEvents The Events in gatedPopulationg that are inside the Gate.
	 */
	public GateSubPopulation(Population gatedPopulation, DataRetriever retriever, Gate gate, Collection<Event> insideEvents) {
		super(gatedPopulation, insideEvents);
		
		this.retriever = retriever;
		this.gate = gate;
	}
	
	/**
	 * @return Returns the Gate used to analyze the Population.
	 */
	public Gate getGate() {
		return gate;
	}
	
	/**
	 * The retriever returned is the same one that the Gated Population was gated with. The
	 * same DataRetriever instance is always returned.
	 */
	public DataRetriever getRetriever() {
		return retriever;
	}
	
	public String toString() {
		StringBuilder builder = new StringBuilder();
		builder.append("Gate \"");
		builder.append(gate.getId());
		builder.append("\"\n");
		return builder.toString();
	}
}
