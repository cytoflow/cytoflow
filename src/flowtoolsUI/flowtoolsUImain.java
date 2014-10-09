package flowtoolsUI;

import java.io.File;
import java.io.IOException;
import java.net.URISyntaxException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.eclipse.swt.SWT;
import org.eclipse.swt.widgets.Display;
import org.eclipse.swt.widgets.Shell;
import org.flowcyt.facejava.fcsdata.DataRetriever;
import org.flowcyt.facejava.fcsdata.Parameter;
import org.flowcyt.facejava.fcsdata.exception.*;
import org.flowcyt.facejava.fcsdata.impl.FcsDataFile;
import org.flowcyt.facejava.fcsdata.impl.FcsDataSet;
import org.flowcyt.facejava.fcsdata.io.CFCSInput;
import org.flowcyt.facejava.fcsdata.statistics.*;
import org.eclipse.swt.widgets.FileDialog;
import org.eclipse.swt.events.PaintEvent;
import org.eclipse.swt.events.PaintListener;
import org.eclipse.swt.graphics.*;

public class flowtoolsUImain {

	protected Shell shell;

	/**
	 * Launch the application.
	 * @param args
	 */
	public static void main(String[] args) {
		try {
			flowtoolsUImain window = new flowtoolsUImain();
			window.open();
		} catch (Exception e) {
			e.printStackTrace();
		}
	}

	/**
	 * Open the window.
	 */
	public void open() {
		Display display = Display.getDefault();
		createContents();
		CFCSInput test = new CFCSInput();
		
		File testfile = new File("test.fcs");
		//System.out.println(testfile.size());
		try {
			FcsDataFile testfcsfile= test.read(testfile);
			FcsDataSet fcsdata = testfcsfile.get(0);
			DataRetriever dataRet = fcsdata.getRetriever();
			
			PopulationStatistics stats = fcsdata.getStatistics();
			Image image = makeColoredDotPlot(fcsdata, stats, dataRet, display);
			shell.addPaintListener(new PaintListener(){ 
		        public void paintControl(PaintEvent e){ 
		            GC gc = e.gc;
		            gc.drawImage(image, 50, 50);
		            gc.dispose(); 
				    image.dispose();
		        } 
		    }); 
			
			
		} catch (IOException | InvalidDataSetsException | DataRetrievalException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		
		shell.open();
		shell.layout();
		while (!shell.isDisposed()) {
			if (!display.readAndDispatch()) {
				display.sleep();
			}
		}
	}

	/**
	 * Create contents of the window.
	 */
	protected void createContents() {
		shell = new Shell();
		shell.setSize(500, 500);
		shell.setText("SWT Application");
		
	}
	
	private Image makeColoredDotPlot(FcsDataSet fcsdata, PopulationStatistics stats, DataRetriever dataRet, Display display){
		int imageHeight = 400;
		int imageWidth = 400;
		int binSize =2;
		Map<Integer, Integer> pointCounts = new HashMap<Integer, Integer>();
		Map<Integer, List<Integer[]>> pointBins = new HashMap<Integer, List<Integer[]>>();
		List<Parameter> params = dataRet.getAllParameters();
		Image image = new Image(display, new Rectangle(0, 0, imageWidth, imageHeight));
		GC gc = new GC(image);
		PopulationParameterStatistics param1stats = stats.getParameterStatistics(params.get(0));
		PopulationParameterStatistics param2stats = stats.getParameterStatistics(params.get(3));
		double maxX = param1stats.getMax();
		double maxY = param2stats.getMax();
		Integer maxPointCount = 1;
		for (int i=0;i<fcsdata.size();i++){
			try{
				
				double x = dataRet.getScale(params.get(0),fcsdata.get(i));
				double y = dataRet.getScale(params.get(3),fcsdata.get(i));
				
				//System.out.println(fcsdata.get(i));
				//System.out.println(y);
				x = x/maxX;
				y = (1-y/maxY);
				//System.out.println(x);
				//System.out.println(y);
				Integer[] point = {(int)(imageWidth*x), (int)(imageHeight*y)};
				Integer key = (int)(x *imageWidth/binSize) + (int)(imageWidth/binSize*(int)(y*imageHeight/binSize));
				if (!pointCounts.containsKey(key)){
					pointCounts.put(key, 1);
					List<Integer[]> newList = new ArrayList<Integer[]>();
					newList.add(point);
					pointBins.put(key, newList);
				}
				else{
					Integer newPointCount = pointCounts.get(key)+1;
					if (newPointCount>maxPointCount){
						maxPointCount = newPointCount;
					}
					pointCounts.put(key, newPointCount);
					pointBins.get(key).add(point);
				}
			}
			catch (DataRetrievalException f){
				f.printStackTrace();
			}
		}
		for (Integer key:pointCounts.keySet()){
			double colorTolerance = 1.01;
			Double colorValue = 1-Math.pow(colorTolerance, -(double)pointCounts.get(key));
			
			Color currColor;
			if (colorValue>1||colorValue<0){
				throw new RuntimeException("color value is " + colorValue);
			}
			if (colorValue <0.5){
				currColor = new Color(display, 0, (int)((2*colorValue)*255), (int)((2*(0.5-colorValue))*255));
			}
			else {
				currColor = new Color(display, (int)((2*(colorValue-0.5))*255), (int)((2*(1-colorValue))*255), 0);
			}
			gc.setForeground(currColor);
			for (Integer[] pointToDraw :pointBins.get(key)){
				gc.drawLine(pointToDraw[0], pointToDraw[1], pointToDraw[0], pointToDraw[1]);
			}
		}

		System.out.println("returned");
		return image;
	}

}
