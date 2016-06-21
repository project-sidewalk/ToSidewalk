import csv

from collections import namedtuple
from itertools import groupby


Availability = namedtuple('Availability', ['lat', 'lng', 'street_edge_id', 'available'])


def main(filename):
    with open(filename, 'rb') as f:
        # skip the header, then map each line of a csv file to Availability
        next(f)
        availabilities = map(lambda row: Availability(lat=float(row[0]), lng=float(row[1]), street_edge_id=int(row[2]), available=True if row[3] == "AVAILABLE" else False), csv.reader(f))

    # Sort and group the availabilities by street_edge_id. Each group should have 2 records.
    availabilities = sorted(availabilities, key=lambda x: x.street_edge_id)
    for k, g in groupby(availabilities, lambda x: x.street_edge_id):
        g = list(g)
        print g

    # List groups' ids where you only have one r
    one_availability = [k for k, g in groupby(availabilities, lambda x: x.street_edge_id) if len(list(g)) < 2]
    print one_availability

if __name__ == '__main__':
    main('../../resources/StreetViewAvailability/StreetViewAvailability.csv')