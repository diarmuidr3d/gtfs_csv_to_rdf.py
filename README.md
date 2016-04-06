# gtfs_csv_to_rdf.py
Python convertor for GTFS data specified in CSV to linked-GTFS using RDFLib

To use this via the command line
```
python gtfs_csv_to_rdf.py http://example.com# file_to_write_to gtfs.zip
```
Where ```http://example.com``` is the URI that entities will be prefixed with, ```file_to_write_to``` is the destination file for the generated Linked-GTFS and ```gtfs.zip``` is the zip file containing the GTFS data.


To use this as a python library
```python
from gtfs_csv_to_rdf import GtfsCsvToRdf

convertor = GtfsCsvToRdf("http://example.com#", "file_to_write_to")
convertor.convert_agency("agency.txt")
convertor.output()
```
