from payload_automation.artifactor import getExif, getHashes, getOutputType, getPDB
from argparse import ArgumentParser
from os.path import exists


def parseArguments():
    parser = ArgumentParser()
    parser.add_argument('files', nargs='+', help='The files to get metadata for.')
    return parser.parse_args()


def main(args):
    files = args.files
    print(f"========== Parsed Arguments ==========")
    print(f"Files: {', '.join(files)}")
    print()
    for file in files:
        if exists(file):
            exif = getExif(file)
            hashes = getHashes(file)
            outputType = getOutputType(file)
            pdb = getPDB(file)

            output = f"{exif}\nMD5: {hashes[0]}\nSHA1: {hashes[1]}\nSHA256: {hashes[2]}\n\nOutput Type: {outputType}"

            if pdb:
                output += f"\n{pdb}"
        else:
            output = f"[-] '{file}' does not exist"
        
        print(f"========== {file} ==========")
        print(output)


if __name__ == "__main__":
    args = parseArguments()
    main(args)
