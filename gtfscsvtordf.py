from rdflib import Graph, Namespace, RDF, Literal, XSD, URIRef
from csv import DictReader
from rdflib.namespace import FOAF, DC
from rdflib.resource import Resource

__author__ = 'Diarmuid'

class gtfsCsvToRdf:

    def __init__(self, format, uri=None):
        self.graph = Graph(identifier=uri)
        self.GTFS = Namespace("http://vocab.gtfs.org/terms#")
        self.graph.bind("gtfs", self.GTFS)
        self.uri = uri
        self.format = format

    def convert_agency(self, csv_filename):
        read_agency = DictReader(open(csv_filename))
        for row in read_agency:
            url = row['agency_url']
            agency = Resource(self.graph, URIRef(url))
            agency.add(RDF.type, self.GTFS.Agency)
            name = Literal(row['agency_name'], datatype=XSD.string)
            agency.add(FOAF.name, name)
            timezone = Literal(row['agency_timezone'], datatype=XSD.string)
            agency.add(self.GTFS.timeZone, timezone)
            if 'agency_lang' in row:
                language = Literal(row['agency_lang'], datatype=XSD.string)
                agency.add(DC.language, language)
            if 'agency_phone' in row:
                phone = Literal(row['agency_phone'], datatype=XSD.string)
                agency.add(FOAF.phone, phone)
            if 'agency_fare_url' in row:
                fare_url = URIRef(row['agency_fare_url'])
                agency.add(self.GTFS.fareUrl, fare_url)

