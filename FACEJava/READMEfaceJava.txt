*** FACEJava ***

To compile the sources you will need:

1. CFCS -- Optional.

   Needed if CFCS is used for FCS file I/O. If CFCS(In/Out)put are not used and
   FCS I/O is needed, then another library that is able to read and write FCS
   files (and the corresponding implementations of FCS(In/Out)put) must be
   provided.

   The svn url for CFCS source codes is 
   https://svn.sourceforge.net/svnroot/flowcyt/FACEJava/trunk/CFCS.

   Alternatively, a precompiled version can be obtained from the binary distribution 
   of FACEJava (in the facejava-1.0B1.zip)


2. Archimedes MathJ 0.5 - For MathML and Universal Transformations in
                          transformation.

   http://www.abcwebdesign.com/archimedes/index.html
   
   License: Free for non-commercial use but non-redistributable. 
            License file can be obtained from the downloaded distribution.
   
   Required JAR
   - mathj.jar
   - castor.jar
   - jargs.jar
   
   NOTE: This library is non-redistributable. Users will have to download a
         copy for themselves. FACEFlow will look for the libraries in the
         lib/mathml folder.
         
   No alternative libraries have been found which have the same capabilities as
   MathJ. The various Math systems (e.g., Mathematica, Maple, etc.) all have
   support for MathML but of course, are not easily used as libraries.



Please read the README.txt file in FACEJava directory for more details!
   
