.. _user_beads:

HOWTO: Use beads to correct for day-to-day variation
====================================================

Flow cytometers are complex instruments, and the precise numerical values
they report depend not only on the fluorescence of the sample, but also
on the illumination intensity, optical setup, gain of the detectors (ie PMT
voltages), and even things such as whether the flow cell has been cleaned
recently.  We often want to compare data that was collected on different
days, and this instrument *drift* can make these comparisons difficult.

Many cytometers, especially those used in a clinical setting, use a daily
calibration to counter these effects.  However, these calibrations are intended
for standardized protocols that are run regularly, not the one-off experiments 
that many investigators run.

One approach to this problem is to *calibrate* each day's measurements using
a stable calibrant.  The idea is straightforward: each day, in addition to 
your experimental samples, you measure a sample of stable fluorescent particles
(of known fluorescence), then use these calibrant measurements to convert the
arbitrary units (au) for your experimental samples to the known units for your
calibrant.  For example, if your particles have a fluorescence of 1000 molecules of
fluoresceine (MEFL), and you measure their brightness to be 5000 au, then you 
know that an experimental sample with a brightness of 10,000 au is equivalent to 2,000
MESF.  This relationship holds even if tomorrow the laser is a little dimmer or
the fluidics are a little dirty.

While there are a number of different kinds of stable calibrants that might be
used this way, we have had very good success with 
`Spherotech's Rainbow Calibration Particles <https://www.spherotech.com/CalibrationParticles.htm>`_.
(We usually refer to these particles as "beads".)  Because they're made of 
polystyrine with the fluorophores "baked in" (not on the surface), they 
are ridiculously stable.  Spherotech also provides enough technical data 
about their fluorescence to make it easy to determine a calibration curve
and apply it to experimental data.  Below, you can find the process for 
doing so using ``Cytoflow``.

.. note:: It is often considered "best practice" only to compare data that was
          on the same instrument with the same detector gain settings.  Using
          beads this way can help you get around the "same detector gain
          settings" requirement -- for example, if you have a really bright sample
          and a really dim sample -- but it is *not* a good idea to try to 
          compare between different instruments unless those instruments have
          *exactly* the same optical configuration (lasers, filters, and from
          the same vendor.)
          
Procedure
---------

#. Collect a sample of beads *on the same day, and with the same settings,*
   as your experimental samples.
   
#. Import your data into ``Cytoflow``.  Do *not* import your bead control. 
   In the example below, we'll have three fluorescence channels -- *Pacific Blue-A*, 
   *FITC-A* and *PE-Tx-Red-YG-A* -- in addition to the forward and side-scatter channels.
   
   .. image:: images/bleedthrough2.png
   
#. Add the **Beads** operation to your workflow.  It's the |BEADS| icon.

#. Choose the beads you used, *including the specific lot*, from the drop-down
   list.
   
   .. note:: If the beads you want to use are not in the list, please submit a bug
             report.  Adding a new set of beads is pretty trivial.
                          
#. Specify the file containing the data from the beads.

#. Click **Add a channel** for every channel you want to calibrate. In the
   **Channels** list, specify both the *channel* you want to calibrate and
   the *units* you want to calibrate it.
   
   .. note:: It works best to choose units of a fluorophore that is spectrally
             matched to the channel that you're calibrating.  Here are the beads
             that ``Cytoflow`` knows about (including the laser and filter sets
             used to characterize the beads):

             - Spherotech ACP 30-2K
             - Spherotech RCP-30-5A Lot AN04, AN03, AN02, AN01, AM02, AM01, AL01, AK04, AK03 & AK02**
             - Spherotech RCP-30-5A (Euroflow) Lot EAM02 & EAM01
             - Sphreotech RCP-30-5A (Euroflow) Lot EAK01, EAG01, EAE01 & EAF01
             - Spherotech RCP-30-5A Lot AK01, AJ01, AH02, AH01, AF02, AF01, AD04 & AE01
             - Spherotech RCP-30-5A Lot AG01
             - Spherotech RCP-30-5A Lot AA01, AA02, AA03, AA04, AB01, AB02, AC01 & GAA01-R
             - Spherotech RCP-30-5A Lot AC02, AC03 & AD01
             - Spherotech RCP-30-5A Lot Z02 and Z03
             - Spherotech RCP-30-5 Lot AA01, AB01, AB02, AC01 & AD01
             - Spherotech RCP-30-5 Lot AM02, AM01, AL01, AH01, AG01, AF01 & AD03
             - Spherotech RCP-60-5
             - Spherotech URCP 38-2K
             - Spherotech URCP 38-2K Lot AN01, AM01, AL02, AL01, AK03, AK02, AK01, AJ02 & AJ03
             - Spherotech URCP 50-2K Lot AM01 & AJ01
             - Spherotech URCP 50-2K
    
             The Spherotech fluorophore labels and the laser / filter sets used to measure them
             (that I know about) are:
    
             - **MECSB** (Cascade Blue, 405 --> 450/50)
             - **MEBFP** (BFP, 405 --> 530/40)
             - **MEFL** (Fluroscein, 488 --> 530/40)
             - **MEPE** (Phycoerythrin, 488 --> 575/25)
             - **MEPTR** (PE-Texas Red, 488 --> 613/20)
             - **MECY** (Cy5, 488 --> 680/30)
             - **MEPCY7** (PE-Cy7, 488 --> 750 LP)
             - **MEAP** (APC, 633 --> 665/20)
             - **MEAPCY7** (APC-Cy7, 635 --> 750 LP)
             
               
#. Click **Estimate!**  Check the diagnostic plots to make sure that each
   peak in your data was found, and that you have a fairly linear relationship
   between the (measured) peaks and the (known) calibration.
   
   .. image:: images/beads2.png
   
   .. note:: If not all of the peaks were identified, try messing around with
             the peak-finding parameters.
             
.. note:: Bead calibration is particularly powerful when combined with the 
          autofluorescence correction and bleedthrough compensation 
          described in :ref:`user_bleedthrough`.  They're so useful when
          done together that this sequence of operations has its own module --
          see :ref:`user_tasbe`.
  
  
  
.. |BEADS| image:: images/beads1.png
  