*** FACEJava ******************************************************************
*******************************************************************************

(This is the developer README. For info about how to use FACEFlow, the user
FACEFlow application README is at FACEFlow.README.txt.)

The FACEJava project has 5 different parts split into five distinct packages
(there's one more packaage containing utility classes shared by the other
packages. Each of the 5 packages corresponds to one of the proposed file
standards. However, not all the packages are interrelated (more info about
each pacakage are given in their section) so it is possible (see the Ant build
script) to produce libraries which comprise only a portion of FACEJava.

CFCS is separate from FACEJava since it was developed elsewhere. See its 
README for more info.

(Note that since everything is in org.flowcyt.facejava, it'll often be omitted
since I'm lazy.)

First, a note about the Java Runtime ...

#######
# Java JRE 5.0 (1.5) is required for all of FACEJava. It is not compatible with
# previous runtimes.
#######

and now, we'll work from the bottom up...

*** org.flowcyt.facejava.fcsdata (FCS -- but also more general) ***************
*******************************************************************************

The fcsdata package is used to represent cytometry data, in general. It is the
base package that all other parts of FACEJava depend on (since they *all* 
operate on cytometry data!). Of course, implementations are provided which
represent data from FCS files (in the fcsdata.impl package).

Note that although the FCS files play an important role (since they're the main
source fo cytometry data) the library's main task is to *represent* the data,
and *not* in performing FCS file I/O. To actually open and read an FCS file,
external libraries are required.

To interface with the external libraries easily, an FcsInput interface is 
provided which allows for any library which reads in FCS files to be supported
by this library. Merely implement the interface using your library of choice
(by using the library to read the data from the FCS file and create the
corresponding fcsdata representation of the file). CFCSInput, an implementation
of the FCSInput interface that uses the CFCS library, has been provided. If it
is used, the CFCS library must be in the classpath.

Analogously to FCSInput, writing FCS files is supported through the FcsOutput
interface. Concrete implementations can be created that use a library which can
write FCS files. A implemenatation using CFCS, CFCSOutput, is provided.

The main API consists of the classes in the fcsdata package. Implementations 
hich are for representing FCS files (i.e., a FCS Data File, FCS Data Set, and
FCS Parameters) are in fcsdata.impl. Unless, a client specifically needs to
operate on cytometry data from only FCS files (e.g., compensation must
compensate FCS file data, but any cytometry data can be gated), it should work
with the abstractions and more general super-types in the fcsdata package.

# FACEJava Package dependencies
################################

1. CFCS -- Optional.

   Needed if CFCS is used for FCS file I/O. If CFCS(In/Out)put are not used and
   FCS I/O is needed, then another library that is able to read and write FCS
   files (and the corresponding implementations of FCS(In/Out)put) must be
   provided.

*** org.flowcyt.fcsdata.utils *************************************************
*******************************************************************************

The utils pacakage contains (as the name implies) common code used by the other
packages but does not belong in any of them. 

utils.schemas contains a utility class, JAXBReader, which handles the generic
portions of validation and unmarshalling using JAXB. It can be reused by
projects that need to load an XML file which has had JAXB classes generated for
it.

NOTE: The resources folder must be on the classpath for the utils.schemas to
      work properly (since ClassLoader.getResource()) is used to obtain the 
      Schemas).

# FACEJava Package dependencies
################################

None.
   
*** org.flowcyt.facejava.compensation (Compensation-ML) ***********************
*******************************************************************************

The compensation package carries out compensations on FCS data (only!) using
spillover values from Compensation-ML files. The underlying data in the FCS 
data is not changed but instead new events are created. Thus, different
compensations can be applied to the same data set easily.

Note that the library only handles reading Compensation-ML files and does not
handle writing files directly. However, one could use the JAXB classes and
create the JAXB Marhsaller if needed.

# FACEJava Package dependencies
################################

1. fcsdata

   Compensations are calculated on FCS data sets. 

2. utils

   The JAXBReader class in utils.schemas contains the common JAXB validating 
   and unmarshalling code used by the pacakgages which use JAXB to read XML
   files.
   
*** org.flowcyt.facejava.transformation (Transformation-ML) *******************
*******************************************************************************

The transformation pacakage library handles cytometry Parameter Transforamtions
which are given in Transformation-ML files. It creates Transformation
Parameters (i.e., Parameter sub-types) that can be used to retrieve transformed
data from events.

This library does not handle the creation of Transformation-ML files directly.
However, one could use the JAXB classes and create their own Marshaller to 
write files.

# MathML and Universal Transformations
#######################################

Transformation-ML uses MathML for universal (arbitrary) transformations. 
However, our MathML support is spotty at best. We use Archimedes MathJ for all
our MathML needs and it only supports the following:

   - MathML 1 (we target MathML 2.0)
   - plus, divide, times, minus, root (only roots that have a <degree> of 2),
     power, factorial, sum, and product (along with the requried elements to
     make sum/product work). It also supports some other elements which are
     less useful for our purposes.

When making a universal transformation, parameters to be transformed must have
their names ($PnN) or parameter numbers in a <ci> element. However, since <ci>
is also used to declare bound variables (e.g., for a sum or product), any <ci>
whose immediate parent is a <bvar> is not considered to be a parameter

NOTE: In the case that there are multiple top-level <apply> elements in the
      <math> element, only the last <apply> is carried out.
      
If a new library is found with more comprehensive support for evaluating MathML
2.0 content markup, then we should replace MathJ. Specifically, at a minimum we
would like support for:
   
   - all arithmetic elements (<plus>, <divide>, etc., and <power>, <root>, etc.
     and preferably <quotient>, <remainder>, etc.)  
   - <piecewise>, <piece>, <otherwise> (Many of the pre-defined transformations
     are separated into cases.)
   - elementary classical functions (<log>, <ln>, <exp>, <sin>, <cos>, etc.)
   - <condition> and all basic boolean operations (needed for <piecewise>
     support) -- preferably, as many boolean operations as possible are     
     supported.
   - <inverse> (we could do without it but it would be helpful since we can see
     that three of the predefined transformations use inverses -- the ones
     which require root finding)
   - any elements that are needed to support the above (e.g., <cn>, <ci>,
     <bvar>, etc.)
     
# JAXB Schema Compilation
##########################

Unlike the other packages which use JAXB, there are some sticky points when
compiling the Transformation-ML schema with xjc.

The bindings.xjb JAXB bindings file in resources/schemas/Transformation-ML.v1.0
must be used when using xjc to compile the Transformation-ML schema to
workaround some naming issues that JAXB has with MathML. To give it to xjc, use
the -b option.

Also, in JAXB 2.0.2 the proper namespace doesn't seem to be included when the
MathML math element is referenced by a universal element. This will result in
a problem when reading Transformation-ML files that have universal
transformations. The Unmarshaller will report that a math element in the
Transformation-ML namespace is expected rather than the MathML namespace. The
offending line in org.flowcyt.transformation.jaxb.Universal.java is:

 @XmlElement(required = true)

(just before the MathType math field in the class) and it should be:

 @XmlElement(namespace = "http://www.w3.org/1998/Math/MathML", required = true)
    
Making the change after compiling with xjc will allow files to be read
correctly. 

NOTE: This change must be made everytime the Transformation-ML schema is
      re-compiled. Since all manual changes are lost.

# FACEJava Package dependencies
################################

1. fcsdata

   Transformations are modelled as Parameters. As such, DataRetrievers from
   fcsdata should be used to obtain the transformed data.

2. utils

   The JAXBReader class in utils.schemas contains the common JAXB validating 
   and unmarshalling code used by the pacakgages which use JAXB to read XML
   files.

*** org.flowcyt.facejava.gating (Gating-ML) ***********************************
*******************************************************************************

The gating package is used to perform gating operations on cytometry data using
gates from Gating-ML files.

The package is Transformations-agnostic. It merely uses Parameters (which may
be Transformations) to retrieve event data from the FCS Data to perform the
gating on. So to use transformations, the Transformation (parameters) need to
be in the DataRetriever that is used during gating.

This library is also Compensation-agnostic. It will gate on whatever event data
is in a Population. So to gate on compensated data, apply the compensation to
the data set then pass the CompensatedDataSet in for analysis.

This library does not handle the creation of Gating-ML files directly. However,
one could use the JAXB classes and create their own Marshaller to write files.


# FACEJava Package dependencies
################################

1. fcsata

   Gating is done on cytometry data!

2. utils

   The JAXBReader class in utils.schemas contains the common JAXB validating 
   and unmarshalling code used by the pacakgages which use JAXB to read XML
   files.
   
*** org.flowcyt.facejava.faceflow (Flow RElations RDF + User Application) *****
*******************************************************************************

FACEFlow brings together all the different parts of the FACEJava project and
lets the different packages work together. For example, with FACEFlow, one can
gate on a compensated data set or gate with some transformed parameters. To do
this, FACEFlow works with "relations" where a relation is some information 
(metadata) associated with a FCS data set. For example, a gating relation may
exist between a Gating-ML file and a data set meaning that the data set should
be gated upon with the Gates specified in the file. Corresponding relations
exist for compensations and transformations.

FACEFlow accepts these user specified relations, in two forms. The principal
method of describing relations is through a Flow Relations RDF file. More
information can be found in the FlowRDF standard. FACEFlow also allows users
to manually relate a FCS file with one (optionally, for each) Gating-ML,
Transformation-ML and Compensation-ML file through the command line when
starting the FACEFlow application. This method however limits the flexibility
as only one FCS file can be inputted and only the whole file can paraticipate
in relations, while the RDF file supports multiple files and relations with
specific data sets within a FCS file.

# FACEFlow, The Relations Framework
####################################

FACEFlow provides a general framework for working with Relations. This code
is in all the subpackages in faceflow except for the faceflow.application 
subpackage. The framework supports:

1. Querying for Relations related to a given data set through the
   RelationsRepository interface.
2. Reading and writing relations from a Flow Relations RDF file through the
   classes in the org.flowcyt.relations.rdf package.
3. A generic framework for providing new functionality when processing
   Relations through RelationsVisitor, DataSetRelationsVisitor and
   DataSetRelations. By providing new implementations for RelationsVisitor or
   DataSetRelationsVisitor, new functionality can be easily provided.

New Relation types can be added as well, without change to existing code. To
add a new Relation, one needs to:

1. Create a new class for the relation which implements the Relation interface
   and stores whatever information the Relation has.
2. To process the Relation, extend whichever RelationsVisitor is used for
   processing Relations and add a method which accepts one argument of the new
   Relation type and annotate the method with @VisitMethod. Implement whatever
   behaviour is needed to process the Relation.

If the Relation should be able to be stored as a statement in a Flow Relations
RDF file, one must also:  
 
3. Create a new RelationCreator class which can create the new Relation class
   using the RDF statement. Then, register the new RelationCreator with the
   RdfRelationsFactory instance used by the RdfRelationsRepository using the
   RDF statement's property.
4. Add a @VisitMethod for the new Relation class to a StatementFactoryVisitor
   which can create the appropriate RDF statement given the new Relation. 
   Set the RdfRelationsRepository to use an instance of the new
   StatementFactoryVisitor.
   
RelationsVisitor uses annotations to provide a double-dispatch mechanism which
is far more easily extendable with new visitable elements than the standard 
GoF Visitor pattern way of doing double-dispatch. Much more detailed
information is in the javadoc.

# FACEFlow, The Application
############################

As an application, FACEFlow is a command-line tool which accepts relations,
processes them and outputs new FCS files for each of the resulting analyses.
All code specific to the application only is in the faceflow.application
package and its subpackages. The application makes use of the general
Relations framework, which may be useful as an example.

More detail about how to use the application (e.g., what options are
available) are in FACEFlow.README.txt.

# FACEJava Pacakge Dependencies
################################

1. fcsdata

Needed to read and model the FCS data so that it can be analyzed through the
different types of Relations.

2. compmensation

Used when a Compensation-ML file is related to a FCS data set to read in the
file and compensate the data set.

3. transformation

Used when a Transformation-ML file is related to a FCS data set to read in the
file and create the Transformations for the data set parameters.

4. gating

Used when a Gating-ML file is related to a FCS data set to read in the file,
create and gate on the data set using the Gates in the file.

*** Source Control ************************************************************
*******************************************************************************

Code at the BCCRC is stored on the beagle server in a Subversion repository at
svn://beagle/flowcyt. The code is in the FACEJava folder. CFCS and FACEJava are
stored in two different folders under trunk
(svn://beagle/flowcyt/FACEJava/trunk) since CFCS is not fully ours.


*** FACEJava Third-Party Libraries ********************************************
*******************************************************************************

The copies used of all the third-party libraries are under source control in
the lib folder. If new libraries are used, their readmes and licenses should
also be added.

Some of the libraries used depend on Xerces. Since their are multiple
libraries making use of it, we have eliminated the duplicates and distribute
one shared copy. (Thus, the xerces jars in the external libraries'
distributions are not included.)

This product includes software developed by the Apache Software Foundation
(http://www.apache.org/).

1. JAXB 2.0.2 RI - For reading the Gating-ML, Transformation-ML, 
                   Compensation-ML files. faceflow also uses it since it needs
                   access to the JAXBException class (to deal with problems
                   reading in the ML files).

   https://jaxb.dev.java.net/
   
   License: Common Development and Distribution License 
      
       http://www.opensource.org/licenses/cddl1.php
   
   Required JARs:
   - activation.jar
   - jaxb-api.jar
   - jaxb-impl.jar
   - jsr173_1.0_api.jar
   
   NOTE: The JAXB generated classes in FACEJava (they are all in some *.jaxb
         package) must be recompiled with a change in the corresponding schema
         and sometimes with a change in the version of JAXB used. To recompile,
         the command
     
     xjc -d {Workspace_dir}/FACEJava/src -p {package_name} {schema_file}.xsd
     
         can be used, where workspace_dir is the Eclipse workspace directory
         (this will overwrite the old JAXB classes in the workspace),
         package_name is the pacakage to place the JAXB classes (e.g., 
         org.flowcyt.facejava.gating.jaxb for the Gating-ML schema) and 
         schema_file is the path to the schema being compiled. For
         Transformations, extra options need to be given (see its section).

2. Commons Math 1.1 - For root finding in transformation, compensation
                      calculations, and computing population statistics in
                      fcsdata.
   
   http://jakarta.apache.org/commons/math/
   
   License: Apache Software License
   
       http://www.opensource.org/licenses/apachepl.php
   
   Required Jar:
   - commons-math-1.1.jar

3. JENA 2.4 - For reading in RDF Files and querying against the RDF model.

   http://jena.sourceforge.net/
   
   License: http://jena.sourceforge.net/license.html
   
   Required Jars:
   - antlr-2.7.5.jar
   - arq.jar
   - commons-logging.jar
   - concurrent.jar
   - icu4j_3_4.jar
   - iri.jar
   - jena.jar
   - json.jar
   - log4j-1.2.12.jar
   - stax-api-1.0.jar
   - wstx-asl-2.8.jar
   
4. args4j -- For parsing command line arguments in FACEFlow
   
   https://args4j.dev.java.net/
   
   License: The MIT License
   
       http://www.opensource.org/licenses/mit-license.php
   
   Required JARs:
   - args4j-2.0.6.jar
   
   Note: No license can be found.
   
5. JTS Topology Suite 1.7.2 -- For Polygon Gates and 2D Polytope Gates (convex
                               hull) in gating.
   
   http://www.jump-project.org/project.php?PID=JTS&SID=OVER
   
   License: LGPL -- Note that no license was included in the JTS distribution
                    but their website (http://www.vividsolutions.com/jts/jtshome.htm)
                    states that, "JTS is open source (under the LGPL  license)."
   
   
   Required JARs:
   - jts-1.7.2.jar
   - jtsio-1.7.2.jar
   - jdom.jar
   - Acme.jar
   
   Note: No license can be found.

6. Archimedes MathJ 0.5 - For MathML and Universal Transformations in
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

7. QSOpt -- For >= 3D Polytope gates (where inside-ness is determined using LP)

   http://www2.isye.gatech.edu/~wcook/qsopt/
   
   License: Normally, free for research or education use,.
   
            The QSopt authors have granted FACEJava permission to use and
            redistribute QSopt as part of FACEJava. Developers using FACEJava
            as a library are also allowed to include QSopt in their
            distributions but are not allowed to use the QSopt library in any 
            other way. That is, they may not use QSopt directly. If they wish
            to make use of QSopt for other LP problems, they must accept the
            QSopt license. 
            
   
   Required JAR:
   - qsopt.jar
         
   QSOpt was chosen because it was a freely downloadable native Java LP library
   available. There are other LP libraries which are either commercial or use
   JNI to interface with native versions of the libraries (e.g., in C or C++).
   The latter restriction would mean that we would have to create different
   distributions for each type of system ... removing one of the reasons Java 
   was picked.
   
   Possible alternatives are:
   
   * lp_solve -- http://groups.yahoo.com/group/lp_solve/
        
        A LGPL library which is callable from Java using JNI.
   
   * GLPK (GNU Linear Programming Kit) -- http://www.gnu.org/software/glpk/
     GLPK JNI interface -- http://bjoern.dapnet.de/glpk/index.htm
        
        A GPL library which also callable through JNI.
   
   * WebCab Optimization -- http://www.webcabcomponents.com/Java/api/optimization/index.shtml
   
        A commercial library optimization library with LP support.
   
   * Solver (from Frontline Systems, Inc.) -- http://www.solver.com/sdkplatform.htm
   
        Another commercial library optimization library with LP support.
    
   NOTE: None of these libraries have actually been used by us to solve the
         LPs for Polytopes. These are only provided as possible alternatives to
         the QSOpt library used by FACEJava and is by no means an exhaustive 
         list.

8. Xerces-J 2.8 -- Used by some of the third-party libraries to parse XML files

   http://xerces.apache.org/xerces2-j/

   License: Apache Software License
   
       http://www.opensource.org/licenses/apachepl.php
       
   Required JARs:
   - xercesImpl.jar
   - xml-apis.jar
   
8. JUnit 4.1 - For testing.

   Only needed to run tests.
   
