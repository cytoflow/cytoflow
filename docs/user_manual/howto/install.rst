.. _user_install:


Installation instructions
=========================

Windows
^^^^^^^

TODO


MacOS
^^^^^

TODO


Linux
^^^^^

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
