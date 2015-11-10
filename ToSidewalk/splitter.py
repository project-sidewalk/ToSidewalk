import os


def split_osm_file(filename):
    """Splits a large OSM files

    :param filename:
    :return:
    """
    command = "java -Xmx4000M -jar ./lib/splitter/splitter.jar --output=xml --output-dir=data --max-nodes=15000 " + filename + " > splitter.log"
    os.system(command)


def main():
    filename = "../resources/DCStreets/DCStreets-separated.osm"
    split_osm_file(filename)


if __name__ == "__main__":
    main()