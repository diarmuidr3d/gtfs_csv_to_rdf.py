from datetime import datetime
from rdflib import Graph, Namespace, RDF, Literal, XSD, URIRef
from csv import DictReader
from rdflib.namespace import FOAF, DC, DCTERMS
from rdflib.resource import Resource

__author__ = 'Diarmuid'

class GtfsCsvToRdf:

    GEO = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")
    SCHEMA = Namespace("http://schema.org/")
    GTFS = Namespace("http://vocab.gtfs.org/terms#")

    def __init__(self, uri, output_file, format='n3'):
        self.output_file = output_file
        self.graph = Graph(identifier=uri)
        self.graph.bind("gtfs", self.GTFS)
        self.graph.bind("geo", self.GEO)
        self.graph.bind("schema", self.SCHEMA)
        self.uri = uri
        self.format = format
        self.agency_ids = {}

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
                agency.add(DCTERMS.language, Literal(row['agency_lang'], datatype=XSD.string))
            if 'agency_phone' in row:
                agency.add(FOAF.phone, Literal(row['agency_phone'], datatype=XSD.string))
            if 'agency_fare_url' in row:
                agency.add(self.GTFS.fareUrl, URIRef(row['agency_fare_url']))
            if 'agency_id' in row:
                self.agency_ids[row['agency_id']] = agency
                agency.add(DCTERMS.identifier, Literal(row['agency_id'], datatype=XSD.string))

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
                stop.add(DCTERMS.description, Literal(row['stop_desc'], datatype=XSD.string))
            if 'zone_id' in row:
                stop.add(self.GTFS.zone, self.get_zone(row['zone_id']))
            if 'stop_url' in row:
                stop.add(FOAF.page ,Literal(row['stop_url'], datatype=XSD.string))
            if 'location_type' in row and row['location_type'] is "1":
                stop.set(RDF.type, self.GTFS.Station)
            else:
                stop.set(RDF.type, self.GTFS.Stop)
            if 'parent_station' in row:
                if row['parent_station'] is not "":
                    stop.add(self.GTFS.parentStation, self.get_stop(row['parent_station']))
            if 'stop_timezone' in row:
                stop.add(self.GTFS.timeZone, Literal(row['stop_timezone'], datatype=XSD.string))
            if 'wheelchair_boarding' in row:
                accessibility = self.get_wheelchair_accessible(row['wheelchair_boarding'])
                stop.add(self.GTFS.wheelchairAccesssible, accessibility)

    def convert_routes(self, csv_filename):
        route_types = [self.GTFS.LightRail, self.GTFS.Subway, self.GTFS.Rail, self.GTFS.Bus, self.GTFS.Ferry, self.GTFS.CableCar, self.GTFS.Gondola, self.GTFS.Funicular]
        read_routes = DictReader(open(csv_filename))
        print(read_routes.fieldnames)
        for row in read_routes:
            route = self.get_route(row["route_id"])
            route.add(self.GTFS.shortName, Literal(row["route_short_name"], datatype=XSD.string))
            route.add(self.GTFS.longName, Literal(row["route_long_name"], datatype=XSD.string))
            route.add(self.GTFS.routeType, route_types[int(row["route_type"])])
            if "agency_id" in row:
                route.add(self.GTFS.agency, self.agency_ids[row["agency_id"]])
            if "route_desc" in row:
                route.add(DCTERMS.description, Literal(row["route_desc"], datatype=XSD.string))
            # not implemented yet
            # if "route_url" in row:
            #     route.add(self.GTFS.routeUrl, row["route_url"])
            if "route_color" in row:
                route.add(self.GTFS.color, Literal(row["route_color"], datatype=XSD.string))
            if "route_text_color" in row:
                route.add(self.GTFS.textColor, Literal(row["route_text_color"], datatype=XSD.string))

    def convert_trips(self, csv_filename):
        read_trips = DictReader(open(csv_filename))
        print(read_trips.fieldnames)
        for row in read_trips:
            trip = self.get_trip(row["trip_id"])
            trip.add(self.GTFS.route, self.get_route(row["route_id"]))
            trip.add(self.GTFS.service, self.get_service(row["service_id"]))
            if "trip_headsign" in row:
                trip.add(self.GTFS.headsign, Literal(row["trip_headsign"], datatype=XSD.string))
            if "trip_short_name" in row:
                trip.add(self.GTFS.shortName, Literal(row["trip_short_name"], datatype=XSD.string))
            if "direction_id" in row:
                trip.add(self.GTFS.direction, Literal(row["direction_id"], datatype=XSD.boolean))
            if "block_id" in row:
                trip.add(self.GTFS.block, Literal(row["block_id"], datatype=XSD.nonNegativeInteger))
            if "shape_id" in row:
                trip.add(self.GTFS.shape, self.get_shape(row["shape_id"]))
            if "wheelchair_accessible" in row:
                accessibility = self.get_wheelchair_accessible(row['wheelchair_accessible'])
                trip.add(self.GTFS.wheelchairAccessible, accessibility)
            if "bikes_allowed" in row:
                bikes = self.get_bikes_allowed(row["bikes_allowed"])
                trip.add(self.GTFS.bikesAllowed, bikes)

    def convert_stop_times(self, csv_filename):
        stop_time_num = 0
        read_stop_times = DictReader(open(csv_filename))
        print(read_stop_times.fieldnames)
        for row in read_stop_times:
            stop_time = Resource(self.graph, URIRef(self.uri + "StopTIme" + str(stop_time_num)))
            stop_time.set(RDF.type, self.GTFS.StopTime)
            stop_time.add(self.GTFS.trip, self.get_trip(row["trip_id"]))
            stop_time.add(self.GTFS.arrivalTime, Literal(row["arrival_time"], datatype=XSD.string))
            stop_time.add(self.GTFS.departureTime, Literal(row["departure_time"], datatype=XSD.string))
            stop_time.add(self.GTFS.stop, self.get_stop(row["stop_id"]))
            stop_time.add(self.GTFS.stopSequence, Literal(row["stop_sequence"], datatype=XSD.nonNegativeInteger))
            if "stop_headsign" in row:
                stop_time.add(self.GTFS.headsign, Literal(row["stop_headsign"], datatype=XSD.string))
            if "pickup_type" in row:
                pickup_type = self.get_stop_type(row["pickup_type"])
                stop_time.add(self.GTFS.pickupType, pickup_type)
            if "drop_off_type" in row:
                dropoff_type = self.get_stop_type(row["drop_off_type"])
                stop_time.add(self.GTFS.dropOffType, dropoff_type)
            if "shape_dist_traveled" in row:
                # stop_time.add(self.GTFS.distanceTraveled, Literal(float(row["shape_dist_traveled"]), datatype=XSD.nonNegativeInteger))
                stop_time.add(self.GTFS.distanceTraveled, Literal(float(row["shape_dist_traveled"])))
            # if "timepoint" in row:
                #do something... this predicate is not implemented yet

    def convert_calendar(self, csv_filename):
        read_calendar = DictReader(open(csv_filename))
        print(read_calendar.fieldnames)
        for row in read_calendar:
            service = self.get_service(row["service_id"])
            calendar = Resource(self.graph, URIRef(self.uri + row["service_id"] + "_cal"))
            service.add(self.GTFS.serviceRule, calendar)
            calendar.set(RDF.type, self.GTFS.CalendarRule)
            calendar.set(self.GTFS.monday, Literal(int(row["monday"]), datatype=XSD.boolean))
            calendar.set(self.GTFS.tuesday, Literal(int(row["tuesday"]), datatype=XSD.boolean))
            calendar.set(self.GTFS.wednesday, Literal(int(row["wednesday"]), datatype=XSD.boolean))
            calendar.set(self.GTFS.thursday, Literal(int(row["thursday"]), datatype=XSD.boolean))
            calendar.set(self.GTFS.friday, Literal(int(row["friday"]), datatype=XSD.boolean))
            calendar.set(self.GTFS.saturday, Literal(int(row["saturday"]), datatype=XSD.boolean))
            calendar.set(self.GTFS.sunday, Literal(int(row["sunday"]), datatype=XSD.boolean))
            temporal = Resource(self.graph, URIRef(str(calendar) + "_temporal"))
            temporal.set(RDF.type, DCTERMS.temporal)
            temporal.add(self.SCHEMA.startDate, self.get_date_literal(row["start_date"]))
            temporal.add(self.SCHEMA.endDate, self.get_date_literal(row["end_date"]))

    def convert_calendar_dates(self, csv_filename):
        read_dates = DictReader(open(csv_filename))
        print(read_dates.fieldnames)
        for row in read_dates:
            service = self.get_service(row["service_id"])
            calendarDate = Resource(self.graph, URIRef(self.uri + row["service_id"] + "_cal" + "_" + row["date"]))
            service.add(self.GTFS.serviceRule, calendarDate)
            calendarDate.set(RDF.type, self.GTFS.CalendarDateRule)
            calendarDate.add(DCTERMS.date, self.get_date_literal(row["date"]))
            exception_type = row["exception_type"]
            if exception_type is "2":
                exception_type = "0"
            calendarDate.add(self.GTFS.dateAddition, Literal(exception_type, datatype=XSD.boolean))

    def output(self):
        self.graph.serialize(destination=self.output_file, format=self.format)

    def get_stop(self, id):
        stop = Resource(self.graph, URIRef(self.uri + id))
        stop.set(DCTERMS.identifier, Literal(id, datatype=XSD.string))
        return stop

    def get_zone(self, id):
        the_zone = Resource(self.graph, URIRef(self.uri + id))
        the_zone.set(RDF.type, self.GTFS.Zone)
        the_zone.set(DCTERMS.identifier, Literal(id, datatype=XSD.string))
        return the_zone

    def get_route(self, id):
        route = Resource(self.graph, URIRef(self.uri + id))
        route.set(RDF.type, self.GTFS.Route)
        route.set(DCTERMS.identifier, Literal(id, datatype=XSD.string))
        return route

    def get_trip(self, id):
        trip = Resource(self.graph, URIRef(self.uri + id))
        trip.set(RDF.type, self.GTFS.Trip)
        trip.set(DCTERMS.identifier, Literal(id, datatype=XSD.string))
        return trip

    def get_service(self, id):
        service = Resource(self.graph, URIRef(self.uri + id))
        service.set(RDF.type, self.GTFS.Service)
        service.set(DCTERMS.identifier, Literal(id, datatype=XSD.string))
        return service

    def get_shape(self, id):
        shape = Resource(self.graph, URIRef(self.uri + id))
        shape.set(RDF.type, self.GTFS.Shape)
        shape.set(DCTERMS.identifier, Literal(id, datatype=XSD.string))
        return shape

    def get_wheelchair_accessible(self, wheelchair):
        if wheelchair is "1":
            accessibility = self.GTFS.WheelchairAccessible
        elif wheelchair is "2":
            accessibility = self.GTFS.NotWheelchairAccessible
        else:
            accessibility = self.GTFS.CheckParentStation
        return accessibility

    def get_bikes_allowed(self, code):
        bikes = 0
        if code is "0" or "2":
            bikes = 0
        elif code is "1":
            bikes = 1
        return Literal(bikes, datatype=XSD.boolean)

    def get_stop_type(self, code):
        if code is 0:
            pickup_type = self.GTFS.Regular
        elif code is 1:
            pickup_type = self.GTFS.NotAvailable
        elif code is 2:
            pickup_type = self.GTFS.MustPhone
        elif code is 3:
            pickup_type = self.GTFS.MustCoordinateWithDriver
        else:
            pickup_type = self.GTFS.NotAvailable
        return pickup_type

    def get_date_literal(self, date):
        return Literal(datetime.strptime(date, "%Y%m%d").strftime("%Y-%m-%d"), datatype=XSD.date)