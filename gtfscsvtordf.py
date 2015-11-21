from rdflib import Graph, Namespace, RDF, Literal, XSD, URIRef
from csv import DictReader
from rdflib.namespace import FOAF, DC
from rdflib.resource import Resource

__author__ = 'Diarmuid'

class gtfsCsvToRdf:

    def __init__(self, uri, output_file, format='n3'):
        self.output_file = output_file
        self.graph = Graph(identifier=uri)
        self.GTFS = Namespace("http://vocab.gtfs.org/terms#")
        self.graph.bind("gtfs", self.GTFS)
        self.GEO = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")
        self.graph.bind("geo", self.GEO)
        self.uri = uri
        self.format = format
        self.agency_ids = {}
        self.stop_ids = {}

    def convert_agency(self, csv_filename):
        read_agency = DictReader(open(csv_filename))
        print(read_agency.fieldnames)
        for row in read_agency:
            url = row['agency_url']
            agency = Resource(self.graph, URIRef(url))
            agency.add(RDF.type, self.GTFS.Agency)
            name = Literal(row['agency_name'], datatype=XSD.string)
            agency.add(FOAF.name, name)
            timezone = Literal(row['agency_timezone'], datatype=XSD.string)
            agency.add(self.GTFS.timeZone, timezone)
            if 'agency_lang' in row:
                agency.add(DC.language, Literal(row['agency_lang'], datatype=XSD.string))
            if 'agency_phone' in row:
                agency.add(FOAF.phone, Literal(row['agency_phone'], datatype=XSD.string))
            if 'agency_fare_url' in row:
                agency.add(self.GTFS.fareUrl, URIRef(row['agency_fare_url']))
            if 'agency_id' in row:
                self.agency_ids[row['agency_id']] = agency
                agency.add(DC.identifier, Literal(row['agency_id'], datatype=XSD.string))

    def convert_stops(self, csv_filename):
        read_stops = DictReader(open(csv_filename))
        print(read_stops.fieldnames)
        for row in read_stops:
            stop = self.get_stop(row['stop_id'])
            stop.add(FOAF.name, Literal(row['stop_name'], datatype=XSD.string))
            stop.add(self.GEO.long, Literal(row['stop_lon'], datatype=XSD.string))
            stop.add(self.GEO.lat, Literal(row['stop_lat'], datatype=XSD.string))
            if 'stop_code' in row:
                stop.add(self.GTFS.code, Literal(row['stop_code'], datatype=XSD.string))
            if 'stop_desc' in row:
                stop.add(DC.description, Literal(row['stop_desc'], datatype=XSD.string))
            if 'zone_id' in row:
                stop.add(self.GTFS.zone, self.get_zone(row['zone_id']))
            if 'stop_url' in row:
                stop.add(FOAF.page ,Literal(row['stop_url'], datatype=XSD.string))
            if 'location_type' in row and row['location_type'] is "1":
                stop.set(RDF.type, self.GTFS.Station)
            else:
                stop.set(RDF.type, self.GTFS.Stop)
            if 'parent_station' in row:
                parent_id = row['parent_station']
                if parent_id in self.stop_ids:
                    stop.add(self.GTFS.parentStation, self.stop_ids[parent_id])
                elif parent_id is not "":
                    stop.add(self.GTFS.parentStation, self.get_stop(parent_id))
            if 'stop_timezone' in row:
                stop.add(self.GTFS.timeZone, Literal(row['stop_timezone'], datatype=XSD.string))
            if 'wheelchair_boarding' in row:
                wheelchair = row['wheelchair_boarding']
                if wheelchair is "1":
                    accessibility = self.GTFS.WheelchairAccessible
                elif wheelchair is "2":
                    accessibility = self.GTFS.NotWheelchairAccessible
                else:
                    accessibility = self.GTFS.CheckParentStation
                stop.add(self.GTFS.wheelchairAccesssible, accessibility)

    def output(self):
        self.graph.serialize(destination=self.output_file,format=self.format)

    def get_stop(self, id):
        stop = Resource(self.graph, URIRef(self.uri + id))
        self.stop_ids[id] = stop
        stop.set(DC.identifier, Literal(id, datatype=XSD.string))
        return stop

    def get_zone(self, id):
        the_zone = Resource(self.graph, URIRef(self.uri + id))
        the_zone.add(RDF.type, self.GTFS.Zone)
        the_zone.add(DC.identifier, Literal(id, datatype=XSD.string))
        return the_zone