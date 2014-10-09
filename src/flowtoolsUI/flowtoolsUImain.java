package flowtoolsUI;

import java.io.File;
import java.io.IOException;
import java.net.URISyntaxException;
import java.util.List;

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
		int imageHeight = 400;
		int imageWidth = 400;
		Image image = new Image(display, new Rectangle(0, 0, imageWidth, imageHeight));
		GC gc = new GC(image);
		File testfile = new File("test.fcs");
		//System.out.println(testfile.size());
		try {
			FcsDataFile testfcsfile= test.read(testfile);
			FcsDataSet fcsdata = testfcsfile.get(0);
			DataRetriever dataRet = fcsdata.getRetriever();
			List<Parameter> params = dataRet.getAllParameters();
			PopulationStatistics stats = fcsdata.getStatistics();
			PopulationParameterStatistics param1stats = stats.getParameterStatistics(params.get(0));
			PopulationParameterStatistics param2stats = stats.getParameterStatistics(params.get(3));
			double maxX = param1stats.getMax();
			double maxY = param2stats.getMax();
			for (int i=0;i<fcsdata.size();i++){
				try{
					
					double x = dataRet.getScale(params.get(0),fcsdata.get(i));
					double y = dataRet.getScale(params.get(3),fcsdata.get(i));
					//System.out.println(fcsdata.get(i));
					//System.out.println(y);
					x = imageWidth*x/maxX;
					y = imageHeight*(1-y/maxY);
					//System.out.println(x);
					//System.out.println(y);
					gc.drawLine((int)x,(int)y,(int)x,(int)y);
				}
				catch (DataRetrievalException f){
					f.printStackTrace();
				}
			}
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

}
