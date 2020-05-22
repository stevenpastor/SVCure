SVCure
======

App for team-focused annotation of variants.


Up-Front Requirements
-------

* python3
* Up-to-date Firefox, Chrome, or Safari browser


VENV and Pip Install
-------

::

    # clone the repository
    $ git clone https://github.com/stevenpastor/SVCure
    $ cd SVCure

Create a virtualenv and activate it::

    $ python3 -m venv venv
    $ . venv/bin/activate

Or on Windows cmd::

    $ py -3 -m venv venv
    $ venv\Scripts\activate.bat

Install SVCure::

    $ pip install -r requirements.txt
    $ mkdir instance


VENV and Pip Run::

    $ export FLASK_APP=svcure
    $ export FLASK_ENV=development
    $ flask init-db
    $ flask run --host 0.0.0.0 --port 5000

Or on Windows cmd::

    > set FLASK_APP=svcure
    > set FLASK_ENV=development
    > flask init-db
    > flask run --host 0.0.0.0 --port 5000


* Before opening your browser to 0.0.0.0:5000, go to the "File Input" section below to load your files for annotation. 


Docker Install
-------

* Before installing, see the "File Input" section and copy your files to the mentioned directory before installation.

::

    $ docker build . -t svcure:v1
    $ docker run -t -d --name svcure svcure:v1
    $ docker run -i -t svcure:v1 flask init-db
    $ docker run -i -t -p 5000:5000 svcure:v1 flask run --host=0.0.0.0
    # go to 0.0.0.0:5000 in browser


File Input
-------

* After installation, you will have to make a directory to place alignment files (bam/cram), their respective indices (bai/crai), your SV calls (bed format), and the reference fasta files used for alignment (fasta format).
* Then, edit the setup.csv file, of which a template is provided.
* In this file, fill in all columns.
* For an example, see the svcure/static/data/example directory - properly formatted files and setup.csv are included.
* The commands for loading your files are below.

::

    $ mkdir -p svcure/static/data/public
    # Move your files (bam/cram, bai/crai, bed, ref.fa) to this directory

* In the case of the Docker installation, make the directory as above and place your files in the directory.
* The files will get copied over to the container upon installing per the instructions above.


Browser
-------

* After installation and file input steps have been completed, go to your browser at 0.0.0.0:5000 for venv installation or Docker installation.
* You will be asked to register and login.
* After logging in, check the example dataset to familiarize yourself with the annotation process and how the app basically works.
* Click the "Loaded Datasets" button on the homepage to begin annotating your loaded data.
* If you encounter any errors, please be sure to double-check your setup.csv file (located in the SVCure parent directory) and ensure all files are in SVCure/svcure/static/data/public/.


Test
-------

::

    $ pip install '.[test]'
    $ pytest

Run with coverage report::

    $ coverage run -m pytest
    $ coverage report
    $ coverage html  # open htmlcov/index.html in a browser


Notes
-------

    # If rename or add any BAM and/or BED files, you will have to reinitialize the db.

