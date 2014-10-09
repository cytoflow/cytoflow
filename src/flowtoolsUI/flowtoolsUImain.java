package flowtoolsUI;

import java.io.File;
import java.io.IOException;
import java.net.URISyntaxException;

import org.eclipse.swt.SWT;
import org.eclipse.swt.widgets.Display;
import org.eclipse.swt.widgets.Shell;
import org.flowcyt.facejava.fcsdata.exception.InvalidDataSetsException;
import org.flowcyt.facejava.fcsdata.io.CFCSInput;
import org.eclipse.swt.widgets.FileDialog;

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
		shell.setSize(450, 300);
		shell.setText("SWT Application");
		CFCSInput test = new CFCSInput();
		File testfile = new File("test.fcs");
		try {
			test.read(testfile);
		} catch (IOException | InvalidDataSetsException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

}
