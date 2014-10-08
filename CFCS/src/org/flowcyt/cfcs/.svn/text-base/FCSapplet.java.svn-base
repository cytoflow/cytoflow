package org.flowcyt.cfcs;
/*
 * Created on Oct 3, 2005
 *
 * To change the template for this generated file go to
 * Window&gt;Preferences&gt;Java&gt;Code Generation&gt;Code and classesments
 */


import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.File;
import java.lang.reflect.InvocationTargetException;

import javax.swing.BorderFactory;
import javax.swing.JApplet;
import javax.swing.JButton;
import javax.swing.JFileChooser;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.SwingUtilities;
import javax.swing.border.Border;
import javax.swing.border.EtchedBorder;

public class FCSapplet extends JApplet implements ActionListener
{   
	private static final long serialVersionUID = 1347638473321453714L;

	CFCSSystem system;
    JTextField URLfield;
    String writePath;
    JLabel title, URL, errors, keywordLabel, line, line2, countLabel, Count, versionLabel, Version, paramLabel;
    JPanel pane;
    JButton submit, brows, write;
    JFileChooser fc;
    JTextArea ta, params;
    File file;
    JScrollPane jsp, psp;
    Border loweredetched = BorderFactory.createEtchedBorder(EtchedBorder.LOWERED);
    String path;

    public void init()
    {
        try
        {
            SwingUtilities.invokeAndWait(new Runnable()
            {

                public void run()
                {
                    createGUI();
                }
                
            });
        }
        catch (InterruptedException e)
        {
            e.printStackTrace();
        }
        catch (InvocationTargetException e)
        {
            e.printStackTrace();
        }
    }
    
    public void createGUI()
    {
        setSize(550, 500);
        initclassesponents();
        setBackground(new Color(238,238,238));
        pane.setLayout(new GridBagLayout());
        pane.setBorder(loweredetched);
        setGridBag();
        getContentPane().add(pane);
        pane.setVisible(true);
        setVisible(true);
        validate();
    }

    public void initclassesponents()
    {;
        ta = new JTextArea();
        ta.setBorder(loweredetched);
        jsp = new JScrollPane();
        jsp.setViewportView(ta);
        errors = new JLabel();
        write = new JButton("write file");
        write.addActionListener(this);
        params = new JTextArea();
        params.setBorder(loweredetched);
        psp = new JScrollPane();
        paramLabel = new JLabel("parameters: ");
        fc = new JFileChooser();
        pane = new JPanel();
        countLabel = new JLabel("count: ");
        Count = new JLabel();
        versionLabel = new JLabel("version: ");
        Version = new JLabel();
        submit = new JButton("Submit");
        submit.addActionListener(this);
        brows = new JButton("Brows");
        brows.addActionListener(this);
        URLfield = new JTextField();
        URLfield.setBorder(loweredetched);
        line = new JLabel();
        line.setBackground(Color.gray);
        line2 = new JLabel();
        line2.setBackground(Color.gray);
        title = new JLabel("FCS Reader");
        errors.setFont(new Font("TimesRoman", Font.ITALIC, 12));
        errors.setForeground(Color.red);
        countLabel.setFont(new Font("TimesRoman", Font.BOLD, 12));
        Count.setFont(new Font("TimesRoman", Font.BOLD, 12));
        versionLabel.setFont(new Font("TimesRoman", Font.BOLD, 12));
        Version.setFont(new Font("TimesRoman", Font.BOLD, 12));
        title.setFont(new Font("TimesRoman", Font.BOLD, 20));
        params.setFont(new Font("TimesRoman", Font.BOLD, 12));
        ta.setFont(new Font("TimesRoman", Font.BOLD, 12));
        paramLabel.setFont(new Font("TimesRoman", Font.BOLD, 12));
        URL = new JLabel("URL/File Path: ");
        URL.setFont(new Font("TimesRoman", Font.BOLD, 12));
        keywordLabel = new JLabel("keywords: ");
        keywordLabel.setFont(new Font("TimesRoman", Font.BOLD, 12));
        psp.setViewportView(params);
        title.setBackground(Color.LIGHT_GRAY);
    }

    public void setGridBag()
    {
        GridBagConstraints c = new GridBagConstraints();
        c.fill = GridBagConstraints.CENTER;
        c.weighty = 25;
        c.gridx = 0;
        c.gridy = 0;
        c.gridwidth = 5;
        pane.add(title, c);
        line.setMinimumSize(new Dimension(500, 2));
        line2.setMinimumSize(new Dimension(500, 2));
        line.setPreferredSize(new Dimension(500, 2));
        line2.setPreferredSize(new Dimension(500, 2));
        brows.setMinimumSize(new Dimension(100, 20));
        submit.setMinimumSize(new Dimension(100, 20));
        write.setMinimumSize(new Dimension(100, 20));
        brows.setPreferredSize(new Dimension(100, 20));
        submit.setPreferredSize(new Dimension(100, 20));
        write.setPreferredSize(new Dimension(100, 20));
        jsp.setPreferredSize(new  Dimension(300,100));
        jsp.setMinimumSize(new  Dimension(300,100));
        psp.setPreferredSize(new  Dimension(300,100));
        psp.setMinimumSize(new  Dimension(300,100));
        c.fill = GridBagConstraints.HORIZONTAL;
        c.gridx = 0;
        c.gridy = 1;
        pane.add(line2, c);
        c.weighty = 15;
        c.gridwidth = 1;
        c.gridx = 0;
        c.gridy = 2;
        pane.add(URL, c);
        c.gridwidth = 4;
        c.gridx = 1;
        c.gridy = 2;
        pane.add(URLfield, c);
        c.gridwidth = 1;
        c.gridx = 0;
        c.gridy = 3;
        pane.add(brows, c);
        c.gridx = 2;
        c.gridy = 3;
        pane.add(submit, c);
        c.gridx = 4;
        c.gridy = 3;
        pane.add(write, c);
        c.gridx = 0;
        c.gridy = 4;
        c.gridwidth = 5;
        pane.add(line, c);
        c.gridwidth = 1;
        c.weightx = 0;
        c.gridx = 0;
        c.gridy = 5;
        pane.add(countLabel, c);
        c.gridwidth = 2;
        c.gridx = 1;
        c.gridy = 5;
        pane.add(Count, c);
        c.gridwidth = 1;
        c.gridx = 0;
        c.gridy = 6;
        pane.add(versionLabel, c);
        c.gridwidth = 2;
        c.gridx = 1;
        c.gridy = 6;
        pane.add(Version, c);
        c.gridx = 0;
        c.gridy = 7;
        pane.add(keywordLabel, c);
        c.gridx = 1;
        c.gridy = 7;
        c.gridwidth = 2;
        pane.add(jsp, c);
        c.gridwidth = 1;
        c.gridx = 0;
        c.gridy = 8;
        pane.add(paramLabel, c);
        c.gridwidth = 2;
        c.gridx = 1;
        c.gridy = 8;
        pane.add(psp, c);
        c.gridwidth = 5;
        c.gridx = 0;
        c.gridy = 9;
        pane.add(errors, c);
    }

    public void actionPerformed(ActionEvent e)
    {
        if (e.getSource() == brows)
        {
            fc.showOpenDialog(this);
            file = fc.getSelectedFile();
            if (file != null)
                URLfield.setText(file.getAbsolutePath());
        }
        else if (e.getSource() == submit)
        {
            getData();
            ta.select(0, 0);
            params.select(0, 0);
        }
        else if (e.getSource() == write)
        {
            fc.showSaveDialog(this);
                file = fc.getSelectedFile();
                if (file != null)
                    writePath = file.getAbsolutePath();
                writeData();
        }

    }

    public void getData()
    {
        //create a new instance of CFCSSystem in order to open, read, and write FCS files
        system = new CFCSSystem();
        //The Following code is to retreive FCS files from a URLs
        //the URL is retreived from the URLfield text field.
        if (!URLfield.getText().startsWith("http://") && URLfield.getText().startsWith("www"))
        {
            URLfield.setText("http://" + URLfield.getText());
            try
            {
                system.open(URLfield.getText());
            }
            catch (CFCSError error)
            {
                if (failIfError(error) != 0)
                {
                    errors.setText("" + error);
                    return;
                }
            }
        }
        else if (URLfield.getText().startsWith("http://"))
        {
            try
            {
                system.open(URLfield.getText());
            }
            catch (CFCSError error)
            {
                if (failIfError(error) != 0)
                {
                    errors.setText("" + error);
                    return;
                }
            }
        }
        //The Following Code is to retreive FCS files from the file system
        //the path is retreived from the brows buttons returned path.
        else
        {
            try
            {
                system.open(URLfield.getText());
            }
            catch (CFCSError error)
            {
                if (failIfError(error) != 0)
                {
                    errors.setText("" + error);
                    return;
                }
            }
        }

        errors.setText("");
        int nDataSets = system.getCount();
        //Loop through each event in the FCS file
        for (int iSet = 0; iSet < nDataSets; iSet++)
        {
            CFCSDataSet set = null;
            // The following code if for getting a list of Keywords
            CFCSKeywords fcsKeywords = null;
            CFCSListModeData listModeData = null;
            try
            {
                set = system.getDataSet(iSet);
                listModeData = (CFCSListModeData) set.getData();
                fcsKeywords = set.getKeywords();
                Count.setText(Integer.toString(listModeData.getCount()));
                Version.setText(set.getVersion());
            }
            catch (CFCSError error)
            {
                if (failIfError(error) != 0)
                    break;
            }

            int count = fcsKeywords.getCount();
            //loop through each keyword in the FCS file
            for (int idx = 0; idx < count; idx++)
            {
                CFCSKeyword keyword = fcsKeywords.getKeyword(idx);
                String keyName = keyword.getKeywordName();
                String keyValue = keyword.getKeywordValue();

                ta.append(keyName + ": " + keyValue + "\n");
            }
            if (iSet < nDataSets - 1)
                System.out.println();
            // the following code is for getting a list of Parameters
            CFCSParameters fcsParameters = null;

            try
            {
                set = system.getDataSet(iSet);
                fcsParameters = set.getParameters();
            }
            catch (CFCSError error)
            {
                if (failIfError(error) != 0)
                    break;
            }

            count = fcsParameters.getCount();
            int paramarray[] = new int[count];
            int paramValues[] = new int[count];
            int nEvents = ((CFCSListModeData) set.getData()).getCount();
            //loop through each parameter in the FCS file.
            //gets event values for each parameter
            //the following 'for' statement gets an array for each event that contains
            //the event value for each parameter
            for (int i = 0; i < nEvents; i++)
            {
                //gets event 'i' and writes event data for each parameter into 'paramarray'
                listModeData.getEvent(i, paramarray);
                //final int[] row = (int[]) data.get(i);
                
                //loops through each array value in paramarray and ads it to the same index
                //value in paramValues.
                //this is done to get a total value of events for each parameter in the FCS file
                //Later on this is divided by total events to get mean for each parameter.
                //Note that the mean value does not seem to be correct when compared to flowjo for 
                //the mac and pc. 
                //possible solutions could be chaneltoscale conversion but no luck yet.
                for (int j = 0; j < count; j++)
                {
                    paramValues[j] = paramValues[j] + paramarray[j];
                }
            }
            //loop through each parameter and write its information to the parameter text area
            for (int idx = 0; idx < count; idx++)
            {
                CFCSParameter parameter = fcsParameters.getParameter(idx);
                String fullName = null, shortName = null;
                try
                {
                    fullName = parameter.getFullName();
                }
                catch (CFCSError error)
                {
                    fullName = "";
                }

                try
                {
                    shortName = "(" + parameter.getShortName() + ")";
                }
                catch (CFCSError error)
                {
                    shortName = "";
                }
                params.append(fullName + " " + shortName + "\n");
                double meanValue = (double) paramValues[idx] / (double) nEvents;
                params.append("           Mean: " + meanValue + "\n");//this value does not seem right
                // Required parameters:
                params.append("           tField Size: " + parameter.getFieldSize() + "\n");
                params.append("           tRange: " + parameter.getRange() + "\n");
                try
                {
                    params.append("           tLog Decades: " + parameter.getLogDecades() + "\n");
                    params.append("           tOffset: " + parameter.getOffset() + "\n");
                }
                catch (CFCSError error)
                {
                    if (error.errorNumber < 0)
                        break;
                }

                // Optional parameters:

                try
                {
                    params.append("           tFilter: " + parameter.getFilter() + "\n");
                }
                catch (CFCSError error)
                {
                    if (error.errorNumber < 0)
                        break;
                }

                try
                {
                    params.append("           tDetector Type: " + parameter.getDetectorType() + "\n");
                }
                catch (CFCSError error)
                {
                    if (error.errorNumber < 0)
                        break;
                }

                try
                {
                    params.append("           tGain: " + parameter.getGain() + "\n");
                }
                catch (CFCSError error)
                {
                }

                try
                {
                    params.append("           tLaser Power: " + parameter.getLaserPower() + "\n");
                }
                catch (CFCSError error)
                {
                    if (error.errorNumber < 0)
                        break;
                }

                try
                {
                    params.append("           tEmitted Percent: " + parameter.getEmittedPercent() + "\n");
                }
                catch (CFCSError error)
                {
                    if (error.errorNumber < 0)
                        break;
                }

                try
                {
                    params.append("           tVoltage: " + parameter.getVoltage() + "\n");
                }
                catch (CFCSError error)
                {
                    if (error.errorNumber < 0)
                        break;
                }

                try
                {
                    params.append("           tExcitation Wavelength: " + parameter.getExcitationWavelength() + "\n");
                }
                catch (CFCSError error)
                {
                    if (error.errorNumber < 0)
                        break;
                }

                if (idx < count)
                    System.out.println();
            }
            if (iSet < nDataSets - 1)
                System.out.println();
        }
    }

    public void writeData()
    {
        try
        {   
            if(!URLfield.getText().equals(null) && !URLfield.getText().equals(""))
            {
                //system.createLocal was created to create a local file stream
                //system.closeLocal() takes information read into the applet from 
                //an FCS file and writes it to a new FCS file.
                //Manipulation could be done here to change the FCS file to you needs.
                system.createLocal(writePath);
                system.closeLocal();
            }
        }
        catch (CFCSError error)
        {
            if (failIfError(error) != 0)
            {
                errors.setText("" + error);
                return;
            }
        }
    }

    public int failIfError(CFCSError error)
    {
        int errorType = 0;
        while (error != null)
        {
            errors.setText("" + error);
            if (error.errorNumber < 0)
            {
                errorType = -1;
            }
            else if (error.errorNumber > 0 && errorType == 0)
            {
                errorType = 1;
            }
            error = error.nextError;
        }
        return errorType;
    }
}
