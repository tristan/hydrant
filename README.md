Hydrant
=======

Note: This project has been idle since 2008. Changes with jython, django and the kepler project may mean this code is unusable now.

Install Instructions
====================

Prerequisites
-------------

### Jython 2.5.2

http://jython.org/

install the jython jar into your local maven repository

    mvn install:install-file -DgroupId=org.jython -DartifactId=jython -Dversion=2.5.2 -Dpackaging=jar -Dfile=/path/to/jython.jar

### Django-Jython

http://packages.python.org/django-jython/

### ImageJ

http://rsbweb.nih.gov/ij/download.html

install the jar into your local maven repository (you may want to change the version numbers here and in the `pom.xml`)

    mvn install:install-file -DgroupId=imagej -DartifactId=imagej -Dversion=1.45 -Dpackaging=jar -Dfile=/path/to/ij.jar

### Maven

http://maven.apache.org/

### Ptolemy II actor IO extensions

http://github.com/tristan/ptII-actorio

### Kepler 1.0.0

PROBLEMS!

I can't find a verson of kepler 1.0.0 that I can do anything with.

Below are some attempts

Download 1.0.0 from `https://kepler-project.org/users/downloads/?page=Downloads`

Problem: download link times out.

Download the kepler 1.0.0 jar from `https://code.kepler-project.org/code/kepler/tags/kepler-1.0-jar-tag/kepler-1.0.jar`

Problem: does not contain the org.geon classes

Use svn to grab the 1.0.0 version using this command:

    svn co https://code.kepler-project.org/code/kepler/tags/kepler-1.0.0-tag-release/

you should have the PTII env set from installing the actor IO extensions, but you still need to set the kepler env variable

    export KEPLER=/home/tristan/projects/kepler-1.0.0-tag-release

Build kepler

Open up `build.xml` in your favorite editor and add the following like the the excludes at `line 271`

    <exclude name="ptolemy/vergil/erg/**"/>

then run

    ant full-clean ptolemy compile

Problem: compilation fails

Use updated build system

    mkdir kepler
    cd kepler
    svn co https://code.kepler-project.org/code/kepler/trunk/modules/build-area
    cd build-area
    ant change-to -Dsuite=kepler-1.0

Problem: kepler jar still doesn't have org.geon packages

### Django-Servlet

Unable to get to the point where I can test this now, so I can't give instructions

http://github.com/tristan/django-servlet

Getting Hydrant
---------------

Download using git or grab the zip from github. See http://github.com/tristan/hydrant for details

Setting up Hydrant
------------------

Unable to get to the point where I can test this now so no Instructions