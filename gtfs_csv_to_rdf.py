from datetime import datetime
from rdflib import Graph, Namespace, RDF, Literal, XSD, URIRef
from csv import DictReader
from rdflib.namespace import FOAF, DCTERMS
from rdflib.resource import Resource

__author__ = 'Diarmuid'


class GtfsCsvToRdf:

    GEO = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")
    SCHEMA = Namespace("http://schema.org/")
    GTFS = Namespace("http://vocab.gtfs.org/terms#")

    def __init__(self, uri, output_file, serialize='n3'):
        self.output_file = output_file
        self.graph = Graph(identifier=uri)
        self.graph.bind("gtfs", self.GTFS)
        self.graph.bind("geo", self.GEO)
        self.graph.bind("schema", self.SCHEMA)
        self.uri = uri
        self.serialize = serialize
        self.next_fare_rule_num = 0

    def convert_agency(self, csv_filename):
        read_agency = DictReader(open(csv_filename), skipinitialspace=True)
        print(read_agency.fieldnames)
        for row in read_agency:
            if "agency_id" in row:
                agency = self.get_agency(str.strip(row["agency_id"]))
            else:
                agency = Resource(self.graph, URIRef(row['agency_url']))
                agency.add(RDF.type, self.GTFS.Agency)
            name = Literal(row['agency_name'], datatype=XSD.string)
            agency.add(FOAF.name, name)
            timezone = Literal(row['agency_timezone'], datatype=XSD.string)
            agency.add(self.GTFS.timeZone, timezone)
            if 'agency_lang' in row and str.strip(row["agency_lang"]) != "":
                agency.add(DCTERMS.language, Literal(row['agency_lang'], datatype=XSD.string))
            if 'agency_phone' in row and str.strip(row["agency_phone"]) != "":
                agency.add(FOAF.phone, Literal(row['agency_phone'], datatype=XSD.string))
            if 'agency_fare_url' in row and str.strip(row["agency_fare_url"]) != "":
                agency.add(self.GTFS.fareUrl, URIRef(row['agency_fare_url']))

    def convert_stops(self, csv_filename):
        read_stops = DictReader(open(csv_filename), skipinitialspace=True)
        print(read_stops.fieldnames)
        for row in read_stops:
            stop = self.get_stop(row['stop_id'])
            stop.add(FOAF.name, Literal(row['stop_name'], datatype=XSD.string))
            stop.add(self.GEO.long, Literal(row['stop_lon'], datatype=XSD.string))
            stop.add(self.GEO.lat, Literal(row['stop_lat'], datatype=XSD.string))
            if 'stop_code' in row and str.strip(row["stop_code"]) != "":
                stop.add(self.GTFS.code, Literal(row['stop_code'], datatype=XSD.string))
            if 'stop_desc' in row and str.strip(row["stop_desc"]) != "":
                stop.add(DCTERMS.description, Literal(row['stop_desc'], datatype=XSD.string))
            if 'zone_id' in row and str.strip(row["zone_id"]) != "":
                stop.add(self.GTFS.zone, self.get_zone(row['zone_id']))
            if 'stop_url' in row and str.strip(row["stop_url"]) != "":
                stop.add(FOAF.page, Literal(row['stop_url'], datatype=XSD.string))
            if 'location_type' in row and row['location_type'] is "1":
                stop.set(RDF.type, self.GTFS.Station)
            else:
                stop.set(RDF.type, self.GTFS.Stop)
            if 'parent_station' in row and str.strip(row["parent_station"]) != "":
                stop.add(self.GTFS.parentStation, self.get_stop(row['parent_station']))
            if 'stop_timezone' in row and str.strip(row["stop_timezone"]) != "":
                stop.add(self.GTFS.timeZone, Literal(row['stop_timezone'], datatype=XSD.string))
            if 'wheelchair_boarding' in row and str.strip(row["wheelchair_boarding"]) != "":
                accessibility = self.get_wheelchair_accessible(row['wheelchair_boarding'])
                stop.add(self.GTFS.wheelchairAccesssible, accessibility)

    def convert_routes(self, csv_filename):
        route_types = [self.GTFS.LightRail, self.GTFS.Subway, self.GTFS.Rail, self.GTFS.Bus, self.GTFS.Ferry,
                       self.GTFS.CableCar, self.GTFS.Gondola, self.GTFS.Funicular]
        read_routes = DictReader(open(csv_filename), skipinitialspace=True)
        print(read_routes.fieldnames)
        for row in read_routes:
            route = self.get_route(str.strip(row["route_id"]))
            route.add(self.GTFS.shortName, Literal(str.strip(row["route_short_name"]), datatype=XSD.string))
            route.add(self.GTFS.longName, Literal(str.strip(row["route_long_name"]), datatype=XSD.string))
            route.add(self.GTFS.routeType, route_types[int(str.strip(row["route_type"]))])
            if "agency_id" in row and str.strip(row["agency_id"]) != "":
                route.add(self.GTFS.agency, self.get_agency(str.strip(row["agency_id"])))
            if "route_desc" in row and str.strip(row["route_desc"]) != "":
                route.add(DCTERMS.description, Literal(str.strip(row["route_desc"]), datatype=XSD.string))
            # not implemented yet
            # if "route_url" in row:
            #     route.add(self.GTFS.routeUrl, str.strip(row["route_url"]))
            if "route_color" in row and str.strip(row["route_color"]) != "":
                route.add(self.GTFS.color, Literal(str.strip(row["route_color"]), datatype=XSD.string))
            if "route_text_color" in row and str.strip(row["route_text_color"]) != "":
                route.add(self.GTFS.textColor, Literal(str.strip(row["route_text_color"]), datatype=XSD.string))

    def convert_trips(self, csv_filename):
        read_trips = DictReader(open(csv_filename), skipinitialspace=True)
        print(read_trips.fieldnames)
        for row in read_trips:
            trip = self.get_trip(str.strip(row["trip_id"]))
            trip.add(self.GTFS.route, self.get_route(str.strip(row["route_id"])))
            trip.add(self.GTFS.service, self.get_service(str.strip(row["service_id"])))
            if "trip_headsign" in row and str.strip(row["trip_headsign"]) != "":
                trip.add(self.GTFS.headsign, Literal(str.strip(row["trip_headsign"]), datatype=XSD.string))
            if "trip_short_name" in row and str.strip(row["trip_short_name"]) != "":
                trip.add(self.GTFS.shortName, Literal(str.strip(row["trip_short_name"]), datatype=XSD.string))
            if "direction_id" in row and str.strip(row["direction_id"]) != "":
                trip.add(self.GTFS.direction, Literal(str.strip(row["direction_id"]), datatype=XSD.boolean))
            if "block_id" in row and str.strip(row["block_id"]) != "":
                trip.add(self.GTFS.block, Literal(str.strip(row["block_id"]), datatype=XSD.nonNegativeInteger))
            if "shape_id" in row and str.strip(row["shape_id"]) != "":
                trip.add(self.GTFS.shape, self.get_shape(str.strip(row["shape_id"])))
            if "wheelchair_accessible" in row and str.strip(row["wheelchair_accessible"]) != "":
                accessibility = self.get_wheelchair_accessible(row['wheelchair_accessible'])
                trip.add(self.GTFS.wheelchairAccessible, accessibility)
            if "bikes_allowed" in row and str.strip(row["bikes_allowed"]) != "":
                bikes = self.get_bikes_allowed(str.strip(row["bikes_allowed"]))
                trip.add(self.GTFS.bikesAllowed, bikes)

    def convert_stop_times(self, csv_filename):
        stop_time_num = 0
        read_stop_times = DictReader(open(csv_filename), skipinitialspace=True)
        print(read_stop_times.fieldnames)
        for row in read_stop_times:
            stop_time = Resource(self.graph, URIRef(self.uri + "StopTime_" + str(stop_time_num)))
            stop_time.set(RDF.type, self.GTFS.StopTime)
            stop_time.add(self.GTFS.trip, self.get_trip(str.strip(row["trip_id"])))
            stop_time.add(self.GTFS.arrivalTime, Literal(str.strip(row["arrival_time"]), datatype=XSD.string))
            stop_time.add(self.GTFS.departureTime, Literal(str.strip(row["departure_time"]), datatype=XSD.string))
            stop_time.add(self.GTFS.stop, self.get_stop(str.strip(row["stop_id"])))
            stop_time.add(self.GTFS.stopSequence, Literal(str.strip(row["stop_sequence"]), datatype=XSD.nonNegativeInteger))
            if "stop_headsign" in row:
                stop_time.add(self.GTFS.headsign, Literal(str.strip(row["stop_headsign"]), datatype=XSD.string))
            if "pickup_type" in row:
                pickup_type = self.get_stop_type(str.strip(row["pickup_type"]))
                stop_time.add(self.GTFS.pickupType, pickup_type)
            if "drop_off_type" in row:
                dropoff_type = self.get_stop_type(str.strip(row["drop_off_type"]))
                stop_time.add(self.GTFS.dropOffType, dropoff_type)
            if "shape_dist_traveled" in row:
                # stop_time.add(self.GTFS.distanceTraveled,
                # Literal(float(str.strip(row["shape_dist_traveled"])), datatype=XSD.nonNegativeInteger))
                stop_time.add(self.GTFS.distanceTraveled, Literal(float(str.strip(row["shape_dist_traveled"]))))
            # if "timepoint" in row:
                # do something... this predicate is not implemented yet

    def convert_calendar(self, csv_filename):
        read_calendar = DictReader(open(csv_filename), skipinitialspace=True)
        print(read_calendar.fieldnames)
        for row in read_calendar:
            service = self.get_service(str.strip(row["service_id"]))
            calendar = Resource(self.graph, URIRef(self.uri + str.strip(row["service_id"]) + "_cal"))
            service.add(self.GTFS.serviceRule, calendar)
            calendar.set(RDF.type, self.GTFS.CalendarRule)
            calendar.set(self.GTFS.monday, Literal(str.strip(row["monday"]), datatype=XSD.boolean))
            calendar.set(self.GTFS.tuesday, Literal(str.strip(row["tuesday"]), datatype=XSD.boolean))
            calendar.set(self.GTFS.wednesday, Literal(str.strip(row["wednesday"]), datatype=XSD.boolean))
            calendar.set(self.GTFS.thursday, Literal(str.strip(row["thursday"]), datatype=XSD.boolean))
            calendar.set(self.GTFS.friday, Literal(str.strip(row["friday"]), datatype=XSD.boolean))
            calendar.set(self.GTFS.saturday, Literal(str.strip(row["saturday"]), datatype=XSD.boolean))
            calendar.set(self.GTFS.sunday, Literal(str.strip(row["sunday"]), datatype=XSD.boolean))
            temporal = Resource(self.graph, URIRef(self.uri + str.strip(row["service_id"]) + "_cal" + "_temporal"))
            temporal.set(RDF.type, DCTERMS.temporal)
            temporal.add(self.SCHEMA.startDate, self.get_date_literal(str.strip(row["start_date"])))
            temporal.add(self.SCHEMA.endDate, self.get_date_literal(str.strip(row["end_date"])))

    def convert_calendar_dates(self, csv_filename):
        read_dates = DictReader(open(csv_filename), skipinitialspace=True)
        print(read_dates.fieldnames)
        for row in read_dates:
            service = self.get_service(str.strip(row["service_id"]))
            calendar_date = Resource(self.graph, URIRef(self.uri + str.strip(row["service_id"]) + "_cal" + "_" + str.strip(row["date"])))
            service.add(self.GTFS.serviceRule, calendar_date)
            calendar_date.set(RDF.type, self.GTFS.CalendarDateRule)
            calendar_date.add(DCTERMS.date, self.get_date_literal(str.strip(row["date"])))
            exception_type = str.strip(row["exception_type"])
            if exception_type is "2":
                exception_type = "0"
            calendar_date.add(self.GTFS.dateAddition, Literal(exception_type, datatype=XSD.boolean))

    def convert_fare_attributes(self, csv_filename):
        read_fares = DictReader(open(csv_filename), skipinitialspace=True)
        print(read_fares.fieldnames)
        for row in read_fares:
            fare = self.get_fare(str.strip(row["fare_id"]))
            fare.set(self.SCHEMA.price, Literal(str.strip(row["price"])))
            fare.set(self.GTFS.priceCurrency, Literal(str.strip(row["currency_type"])))
            fare.set(self.GTFS.paymentMethod, self.get_payment_method(str.strip(row["payment_method"])))
            fare.set(self.GTFS.transfers, self.get_transfers(str.strip(row["transfers"])))
            if "transfer_duration" in row and str.strip(row["transfer_duration"]) != "":
                fare.set(self.GTFS.transferExpiryTime,
                         Literal(str.strip(row["transfer_duration"]), datatype=XSD.nonNegativeInteger))

    def convert_fare_rules(self, csv_filename):
        read_fares = DictReader(open(csv_filename), skipinitialspace=True)
        print(read_fares.fieldnames)
        for row in read_fares:
            fare = self.get_fare(str.strip(row["fare_id"]))
            fare_rule = Resource(self.graph, URIRef(self.uri + str.strip(row["fare_id"]) + "_rule_" + str(self.next_fare_rule_num)))
            self.next_fare_rule_num += 1
            fare_rule.set(RDF.type, self.GTFS.FareRule)
            fare_rule.set(self.GTFS.fareClass, fare_rule)
            if "route_id" in row and str.strip(row["route_id"]) != "":
                fare_rule.add(self.GTFS.route, self.get_route(str.strip(row["route_id"])))
            if "origin_id" in row and str.strip(row["origin_id"]) != "":
                fare_rule.add(self.GTFS.originZone, self.get_zone(str.strip(row["origin_id"])))
            if "destination_id" in row and str.strip(row["destination_id"]) != "":
                    fare_rule.add(self.GTFS.destinationZone, self.get_zone(str.strip(row["destination_id"])))
            if "contains_id" in row and str.strip(row["contains_id"]) != "":
                fare_rule.add(self.GTFS.zone, self.get_zone(str.strip(row["contains_id"])))

    def convert_shapes(self, csv_filename):
        read_shapes = DictReader(open(csv_filename), skipinitialspace=True)
        print(read_shapes.fieldnames)
        for row in read_shapes:
            shape = self.get_shape(str.strip(row["shape_id"]))
            shape_point = Resource(self.graph, URIRef(str(shape.identifier) + "_" + str.strip(row["shape_pt_sequence"])))
            shape.add(self.GTFS.shapePoint, shape_point)
            shape_point.set(RDF.type, self.GTFS.ShapePoint)
            shape_point.set(self.GEO.long, Literal(str.strip(row["shape_pt_lon"]), datatype=XSD.string))
            shape_point.set(self.GEO.lat, Literal(str.strip(row["shape_pt_lat"]), datatype=XSD.string))
            shape_point.set(self.GTFS.pointSequence, Literal(str.strip(row["shape_pt_sequence"]), datatype=XSD.nonNegativeInteger))
            if "shape_dist_traveled" in row and str.strip(row["shape_dist_traveled"]) != "":
                shape_point.set(self.GTFS.distanceTraveled, Literal(str.strip(row["shape_dist_traveled"]),
                                                                    datatype=XSD.nonNegativeInteger))

    def convert_frequencies(self, csv_filename):
        read_freqs = DictReader(open(csv_filename), skipinitialspace=True)
        print(read_freqs.fieldnames)
        for row in read_freqs:
            freq = Resource(self.graph, URIRef(self.uri + str.strip(row["trip_id"]) + str.strip(row["start_time"]) + str.strip(row["end_time"])))
            freq.set(RDF.type, self.GTFS.Frequency)
            freq.add(self.GTFS.trip, self.get_trip(str.strip(row["trip_id"])))
            freq.add(self.GTFS.startTime, Literal(str.strip(row["start_time"]), datatype=XSD.string))
            freq.add(self.GTFS.endTime, Literal(str.strip(row["end_time"]), datatype=XSD.string))
            freq.add(self.GTFS.headwaySeconds, Literal(str.strip(row["headway_secs"]), datatype=XSD.nonNegativeInteger))
            if "exact_times" in row:
                exact = False
                if str.strip(row["exact_times"]) == "1":
                    exact = True
                freq.add(self.GTFS.exactTimes, Literal(exact, datatype=XSD.boolean))

    def convert_transfers(self, csv_filename):
        read_transfers = DictReader(open(csv_filename), skipinitialspace=True)
        print(read_transfers.fieldnames)
        for row in read_transfers:
            from_stop = str.strip(row["from_stop_id"])
            to_stop = str.strip(row["to_stop_id"])
            transfers = Resource(self.graph, URIRef(self.uri + "_" + from_stop + "_" + to_stop))
            transfers.set(RDF.type, self.GTFS.TransferRule)
            transfers.add(self.GTFS.originStop, self.get_stop(from_stop))
            transfers.add(self.GTFS.destinationStop, self.get_stop(to_stop))
            transfers.add(self.GTFS.transferType, self.get_transfer_type(str.strip(row["transfer_type"])))
            if "min_transfer_time" in row and str.strip(row["min_transfer_time"]):
                transfers.add(self.GTFS.minimumTransferTime, Literal(str.strip(row["min_transfer_time"]), datatype=XSD.nonNegativeInteger))

    def output(self):
        self.graph.serialize(destination=self.output_file, format=self.serialize)

    def get_agency(self, agency_id):
        agency = Resource(self.graph, URIRef(self.uri + "agency_" + agency_id))
        agency.add(RDF.type, self.GTFS.Agency)
        agency.set(DCTERMS.identifier, Literal(agency_id, datatype=XSD.string))
        return agency

    def get_stop(self, stop_id):
        stop = Resource(self.graph, URIRef(self.uri + "stop_" + stop_id))
        stop.set(DCTERMS.identifier, Literal(stop_id, datatype=XSD.string))
        return stop

    def get_zone(self, zone_id):
        the_zone = Resource(self.graph, URIRef(self.uri + "zone_" + zone_id))
        the_zone.set(RDF.type, self.GTFS.Zone)
        the_zone.set(DCTERMS.identifier, Literal(zone_id, datatype=XSD.string))
        return the_zone

    def get_route(self, route_id):
        route = Resource(self.graph, URIRef(self.uri + "route_" + route_id))
        route.set(RDF.type, self.GTFS.Route)
        route.set(DCTERMS.identifier, Literal(route_id, datatype=XSD.string))
        return route

    def get_trip(self, trip_id):
        trip = Resource(self.graph, URIRef(self.uri + "trip_" + trip_id))
        trip.set(RDF.type, self.GTFS.Trip)
        trip.set(DCTERMS.identifier, Literal(trip_id, datatype=XSD.string))
        return trip

    def get_service(self, service_id):
        service = Resource(self.graph, URIRef(self.uri + "service_" + service_id))
        service.set(RDF.type, self.GTFS.Service)
        service.set(DCTERMS.identifier, Literal(service_id, datatype=XSD.string))
        return service

    def get_shape(self, shape_id):
        shape = Resource(self.graph, URIRef(self.uri + "shape_" + shape_id))
        shape.set(RDF.type, self.GTFS.Shape)
        shape.set(DCTERMS.identifier, Literal(shape_id, datatype=XSD.string))
        return shape

    def get_fare(self, fare_id):
        fare = Resource(self.graph, URIRef(self.uri + "fare_" + fare_id))
        fare.set(RDF.type, self.GTFS.FareClass)
        fare.set(DCTERMS.identifier, Literal(fare_id, datatype=XSD.string))
        return fare

    def get_wheelchair_accessible(self, wheelchair):
        if wheelchair is "1":
            accessibility = self.GTFS.WheelchairAccessible
        elif wheelchair is "2":
            accessibility = self.GTFS.NotWheelchairAccessible
        else:
            accessibility = self.GTFS.CheckParentStation
        return accessibility

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

    def get_payment_method(self, code):
        if code is "0":
            return self.GTFS.OnBoard
        else:
            return self.GTFS.BeforeBoarding

    def get_transfers(self, code):
        if int(code) is 0:
            return self.GTFS.NoTransfersAllowed
        elif int(code) is 1:
            return self.GTFS.OneTransfersAllowed
        elif int(code) is 2:
            return self.GTFS.TwoTransfersAllowed
        else:
            return self.GTFS.UnlimitedTransfersAllowed

    def get_transfer_type(self, code):
        if int(code) == 3:
            return self.GTFS.NoTransfer
        elif int(code) is 1:
            return self.GTFS.EnsuredTransfer
        elif int(code) is 2:
            return self.GTFS.MinimumTimeTransfer
        else:
            return self.GTFS.RecommendedTransfer

    @staticmethod
    def get_bikes_allowed(code):
        bikes = 0
        if code is "0" or "2":
            bikes = 0
        elif code is "1":
            bikes = 1
        return Literal(bikes, datatype=XSD.boolean)

    @staticmethod
    def get_date_literal(date):
        return Literal(datetime.strptime(date, "%Y%m%d").strftime("%Y-%m-%d"), datatype=XSD.date)