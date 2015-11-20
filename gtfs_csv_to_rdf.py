from rdflib import Graph

__author__ = 'Diarmuid'

class gtfs_csv_to_rdf:

    def __init__(self, format, uri=None):
        self.graph = Graph(identifier=uri)
        self.uri = uri
        self.format = format

    def convert_agency(csv_filename, output_filename):
        print(csv_filename, " ", output_filename)