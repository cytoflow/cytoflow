.. _user_install:


HOWTO: Install Cytoflow
=======================

Windows
-------

On Windows, you can use a graphical to install Cytoflow.

#. Browse to `<https://cytoflow.github.io/>`_

#. Download the Windows binaries by clicking the button at the top of the page.

   .. image:: images/install9.png
   
#. Even though I've signed the Windows app, Windows doesn't recognize me as a
   "certified" developer.  (It's EXPENSIVE -- even more so than becoming an
   Apple developer.)  So you'll get a ``Windows protected your PC`` message:
   
   .. image:: images/install10.png
   
   However, if you click "More information", then you can verify that the
   installer is signed "Open Source Developer, Brian Teague" (that's me!)
   and then click "Run anyway."
   
   .. image:: images/install11.png
   
   Note that signing this application costs me about $150 a year. 
   Help me defray some of those costs by tossing me a few bucks
   at `<https://ko-fi.com/bteague>`_?
   
#. Follow the instructions in the installer.  Once you've completed the
   installation, you should be able to find ``Cytoflow`` in your Start
   menu.


MacOS
-----

These instructions were developed using OSX Catalina.  I don't own a Mac or
use one on a regular basis, so if these instructions could be improved, please
let me know.  Also, these binaries were almost certainly built on an Intel Mac,
so they may not work on an A1 mac.

#. Browse to `<https://cytoflow.github.io/>`_

#. Download the MacOS binaries by clicking the button at the top of the page.

   .. image:: images/install3.png
  
#. Using Finder, browse to your Downloads folder.

   .. image:: images/install4.png
  
#. Right-click on the .ZIP file you downloaded and choose "Open With -->
   Archive Utility."
   
   .. image:: images/install5.png
   
   This will extract the application from the archive.
   
#. Double-click the new application.  Because I am paying Apple $150 per year,
   you should not see a security warning -- the app should "just work."
   
   (Consider helping me defray some of that cost by donating a few bucks
   at `<https://ko-fi.com/bteague>`_?)
   
#. (Optional) Move the Cytoflow application to somewhere else "permanent",
   like the desktop or your Applications folder.
   

Linux
-----

These instructions were developed on Ubuntu 20.04 -- they should work on
any modern Linux desktop system.  However, they do require some comfort with
the command line.  If they don't work for you, or you are desparate for a 
point-and-click installer, please file a bug (or better, a patch or
pull-request.)

This results in a program that you can launch from your desktop launcher
-- the "Programs" menu or similar.

#. Browse to `<https://cytoflow.github.io/>`_

#. Download the Linux binaries by clicking the button at the top of the page.

   .. image:: images/install1.png
   
#. Extract the archive:

   .. image:: images/install2.png
   
#. Move the resulting directory to a "permanent" home.  I like to drop such
   things in ``~/.local/lib``, but you may prefer to put it elsewhere.
   
   **The remaining steps should be completed from the command line, starting**
   **in the directory containing the extracted files.**
   
   If you would like to launch ``Cytoflow`` from the command line, you can do
   so by navigating to this directory and running the executable ``cytoflow``.
   
#. Update the location of the icon in the ``.desktop`` file by calling the 
   ``set_launcher_icon`` script::
   
   $ ./set_launcher_icon
   
#. Link ``cytoflow.desktop`` into the ``~/.local/share/applications`` directory::

   $ ln -s $PWD/cytoflow.desktop $HOME/.local/share/applications/cytoflow.desktop
   
#. Update the database of desktop entries::

   $ update-desktop-database ~/.local/share/applications
