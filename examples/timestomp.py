from automation.Artifactor import timestomp, getExif
from argparse import ArgumentParser
from os.path import exists
from datetime import datetime


def parseArguments():
    parser = ArgumentParser()
    parser.add_argument('file', help='The file to timestomp.')
    parser.add_argument('datetimestamp', help='The datetime to stomp the file with. This format can be YYYY-MM-DD HH:MM:SS-Z (output of exiftools) or YYYYMMDDHHMM.SS')
    return parser.parse_args()


def main(args):
    file = args.file
    datetimestamp  = args.datetimestamp
    print(f"========== Parsed Arguments ==========")
    print(f"File: {file}")
    print(f"Datetimestamp: {datetimestamp}")
    print()

    output = str()
    formattedTimestamp = formatTimestamp(datetimestamp)
    if exists(file) and formattedTimestamp is not None:
        output += getExif(file)
        timestomp(file, timestamp=formattedTimestamp)
        output += "\n"
        output += "[*] Changed to:\n"
        output += "\n"
        output += getExif(file)

    elif not exists(file):
        output = f"[-] '{file}' does not exist"
    else:
        output = f"[-] '{datetimestamp}' did not match either 'YYYY-MM-DD HH:MM:SS-Z' or 'YYYYMMDDHHMM.SS'"
    
    print(f"========== {file} ==========")
    print(output)


def formatTimestamp(datetimestamp):
    exifFormat = "%Y:%m:%d %H:%M:%S%z"
    touchFormat = "%Y%m%d%H%M.%S"

    datetimeObject = formatDatetime(datetimestamp, exifFormat)
    if datetimeObject:
        # Need to convert to touch format
        datetimestamp = datetimeObject.strftime(touchFormat)

    datetimeObject = formatDatetime(datetimestamp, touchFormat)
    if datetimeObject:
        return datetimestamp

    else:
        return None


def formatDatetime(datetimestamp, formatString):
    try:
        return datetime.strptime(datetimestamp, formatString)

    except ValueError:
        return None


if __name__ == "__main__":
    args = parseArguments()
    main(args)
