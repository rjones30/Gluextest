#
# osg_job_helper - python utility functions for use in job scripts
#                  to be used for Gluex production on the osg, part
#                  of the gluex_osg_jobscripts package.
#
# author: richard.t.jones at uconn.edu
# version: june 23, 2017
#

import sys
import re
import os
import subprocess

templates = "/cvmfs/oasis.opensciencegrid.org/gluex/templates"
container = "/cvmfs/singularity.opensciencegrid.org/rjones30/gluex:latest"

def usage():
   """
   Print a usage message and exit
   """
   Print("Usage:", jobnames, "command [command arguments]")
   Print(" where command is one of:")
   Print("   info - prints a brief description of this job")
   Print("   status - reports the execution status of the job")
   Print("   submit - submits the job for running on the osg")
   Print("   cancel - cancels the job if it is running on the osg")
   Print("   doslice - executes the job in the present context")
   Print("")
   Print(" info command arguments:")
   Print("   (none)")
   Print(" status command arguments:")
   Print("   -l - optional argument, generates a more detailed listing")
   Print(" submit command arguments:")
   Print("   <start> - first slice to submit to the grid, default 0")
   Print("   <count> - number of slices to submit, starting with <start>")
   Print("   If <count> is 0 or missing then its value is computed to meet")
   Print("   the goal of \"total_events_to_generate\" specified in the")
   Print("   header of this job script.")
   Print(" cancel command arguments:")
   Print("   <start> - first slice to cancel on the grid, default 0")
   Print("   <count> - number of slices to cancel, starting with <start>")
   Print("   If <count> is 0 or missing then its value is computed to meet")
   Print("   the goal of \"total_events_to_generate\" specified in the")
   Print("   header of this job script.")
   Print(" doslice command arguments:")
   Print("   <start> - base slice number for this job, see info for valid range")
   Print("   <offset> - the slice number to generate is <start> + <offset>")
   Print("   Only one slice can be generated per invocation of this script.")
   Print("   Both arguments are mandatory.")
   Print("")
   sys.exit(0)

def Print(*args):
   """
   Custom print statement for this script, to provide immediate
   flushing of stdout after each write, and to simplify eventual
   migration to python 3, where print "msg" no longer works.
   """
   sys.stdout.write(" ".join([str(arg) for arg in args]))
   sys.stdout.write("\n")
   sys.stdout.flush()

def backticks(*args):
   """
   Emulates the `shell_command` behavior of the standard unix shells.
   The shell exit code is available as global variable backticks_errcode.
   """
   request = subprocess.Popen(";".join(args), shell=True,
                              stdout=subprocess.PIPE)
   global backticks_errcode
   backticks_errcode = request.wait()
   return request.communicate()[0].rstrip()

def shellpipe(*args):
   """
   Emulates the `shell_command` behavior of the standard unix shells,
   but returns a pipe from which the output can be read instead of
   capturing it all in memory first. Use this as a replacement for
   backticks if the size of the output might be too large to fit in
   memory at one time.
   """
   p = subprocess.Popen(";".join(args), shell=True, stdout=subprocess.PIPE)
   return p.stdout

def shellcode(*args):
   """
   Executes a sequence of shell commands, and returns the exit code
   from the last one in the sequence. Output is not captured.
   """
   return subprocess.call(";".join(args), shell=True)

def helper_set_slicing(ntotal, nslice):
   """
   Import job slicing parameters from user job context.
   """
   global total_events_to_generate
   total_events_to_generate = ntotal
   global number_of_events_per_slice
   number_of_events_per_slice = nslice

def do_info(arglist):
   """
   Prints a compact summary of information about the job.
   """
   lines = 0
   for line in open(sys.argv[0]):
      lines += 1
      if lines == 1:
         continue
      if re.match(r"^#", line) and lines < 100:
         Print(line.lstrip("#").rstrip())
      else:
         Print("")
         break


def do_status(arglist):
   """
   Prints a report on the execution status of the job.
   There is one optional argument, "-l" for a detailed listing.
   """
   logdir = jobname + ".logs"
   logfile = logdir + "/" + jobname + ".log"
   batchfile = logdir + "/" + "batches.log"
   if not os.path.exists(logfile) or not os.path.exists(batchfile):
      Print("No record exists of this job ever having been submitted.")
      sys.exit(0)
   longlisting = 0
   if len(arglist) > 0:
      if len(arglist) == 1 and arglist[0] == "-l":
         longlisting = 1
      else:
         usage()
   batch_start = {}
   batch_count = {}
   min_start = 9e9
   max_count = 0
   for line in open(batchfile):
      fields = line.rstrip().split()
      batch = int(fields[0])
      batch_start[batch] = int(fields[1])
      if batch_start[batch] < min_start:
         min_start = batch_start[batch]
      batch_count[batch] = int(fields[2])
      if batch_count[batch] > max_count:
         max_count = batch_count[batch]
   state = {}
   cout = shellpipe("condor_userlog " + logfile)
   for line in cout:
      line = line.rstrip()
      m = re.match(r"^([0-9]+)\.([0-9]+) (.*)%$", line)
      if m:
         batch = int(m.group(1))
         if not batch in batch_start:
            Print("Error - cluster", batch, "in the condor log was not",
                  "recorded in the batches.log file, skipping this line!")
            continue
         offset = int(m.group(2))
         sliceno = batch_start[batch] + offset
         fields = m.group(3).split()
         #  WallTime GoodTime CpuUsage AvgAlloc  AvgLost Goodput  Util.
         wall = fields[0]
         good = fields[1]
         cpu = fields[2]
         alloc = fields[3]
         lost = fields[4]
         goodput = fields[5]
         util = fields[6]
         if wall == "0+00:00":
            state[sliceno] = "queued"
         elif good != "0+00:00":
            state[sliceno] = "completed"
         elif good == "0+00:00":
            state[sliceno] = "running"
         else:
            state[sliceno] = "evicted"
      if longlisting:
         Print(line)
   queued = 0
   completed = 0
   running = 0
   failed = 0
   total = 0
   for sliceno in state:
      total += 1
      if state[sliceno] == "queued":
         queued += 1
      elif state[sliceno] == "completed":
         completed += 1
      elif state[sliceno] == "running":
         running += 1
      elif state[sliceno] == "failed":
         failed += 1
   Print("Total statistics for job", jobname, ":")
   Print("  slices queued: ", queued)
   Print("  slices completed: ", completed)
   Print("  slices running: ", running)
   Print("  slices failed: ", failed)
   Print("For more details, do condor_userlog", logfile)

def do_submit(arglist):
   """
   Submit this job for execution on the osg, assuming it is not already running.
   Arguments are:
     1) <start> - first slice number to be executed in this submission
     2) <count> - number of slices to be executed, starting with <start>
   Both arguments are optional, defaulting to 0 and full slice count.
   """
   try:
      if len(arglist) > 0:
         start = int(arglist[0])
      else:
         start = 0
      if len(arglist) > 1:
         count = int(arglist[1])
      else:
         count = 0
   except:
      usage()
   if count == 0:
      nchunk = number_of_events_per_slice
      nslices = int((total_events_to_generate + nchunk - 1) / nchunk)
      count = nslices - count
   if start < 0:
      Print("Error - start slice is less than zero!")
      Print("Nothing to do, quitting...")
      sys.exit(1)
   if count <= 0:
      Print("Error - start slice is greater than the job max slice count!",
            "Nothing to do, quitting...")
      sys.exit(1)
   logdir = jobname + ".logs"
   logfile = logdir + "/" + jobname + ".log"
   batchfile = logdir + "/" + "batches.log"
   batch = 0
   if os.path.exists(batchfile):
      for line in open(batchfile):
         if len(line) > 0:
            batch += 1
   submitfile = logdir + "/" + jobname + ".sub" + str(batch)
   if not os.path.isdir(logdir):
      os.makedirs(logdir)
   submit_out = open(submitfile, "w")
   for line in open(templates + "/osg-condor.sub"):
      line = line.rstrip()
      if re.match(r"^Requirements = ", line):
         submit_out.write("Requirements = (HAS_SINGULARITY == TRUE)")
         submit_out.write(" && (HAS_CVMFS_oasis_opensciencegrid_org == True)")
         submit_out.write("\n")
      elif re.match(r"^\+SingularityImage = ", line):
         submit_out.write("+SingularityImage = \"" + container + "\"\n")
         submit_out.write("+SingularityBindCVMFS = True\n")
         submit_out.write("+SingularityAutoLoad = True\n")
      elif re.match(r"\+SingularityBindCVMFS = ", line):
         pass
      elif re.match(r"\+SingularityAutoLoad = ", line):
         pass
      elif re.match(r"^transfer_input_files = ", line):
         submit_out.write("transfer_input_files = " + jobname + ".py\n")
      elif re.match(r"^x509userproxy = ", line):
         if shellcode("voms-proxy-info -exists -valid 24:00") != 0:
            Print("Error - your grid certificate must be valid, and have",
                  "at least 24 hours left in order for you to submit this job.")
            sys.exit(1)
         proxy = backticks("voms-proxy-info -path")
         submit_out.write("x509userproxy = " + proxy + "\n")
      elif re.match(r"^initialdir = ", line):
         submit_out.write("initialdir = " + os.getcwd() + "\n")
      elif re.match(r"^output = ", line):
         submit_out.write("output = " + logdir + "/$(CLUSTER).$(PROCESS).out\n")
      elif re.match(r"^error = ", line):
         submit_out.write("error = " + logdir + "/$(CLUSTER).$(PROCESS).err\n")
      elif re.match(r"^log = ", line):
         submit_out.write("log = " + logdir + "/" + jobname + ".log\n")
      elif re.match(r"^executable =", line):
         submit_out.write("executable = osg-container.sh\n")
      elif re.match(r"^arguments = ", line):
         submit_out.write("arguments = ./" + jobname + ".py" +
                          " doslice " + str(start) + " $(PROCESS)\n")
      elif re.match(r"^queue", line):
         submit_out.write("queue " + str(count) + "\n")
      else:
         submit_out.write(line + "\n")
   submit_out = 0
   shellcode("condor_submit " + submitfile)
   # todo: actually submit the job to condor
   cluster = 9876 + batch
   if os.path.exists(batchfile):
      batches_out = open(batchfile, "a")
   else:
      batches_out = open(batchfile, "w")
   batches_out.write(str(cluster) + " " + str(start) + " " + str(count) + "\n")
   batches_out = 0

def do_cancel(arglist):
   """
   Cancel execution of this job on the osg, assuming it is already running.
   Arguments are:
     1) <start> - first slice number to be cancelled by this request
     2) <count> - number of slices to be cancelled, starting with <start>
   Both arguments are optional, defaulting to 0 and full slice count.
   """
   try:
      if len(arglist) > 0:
         start = int(arglist[0])
      else:
         start = 0
      if len(arglist) > 1:
         count = int(arglist[1])
      else:
         count = 0
   except:
      usage()
   if count == 0:
      nchunk = number_of_events_per_slice
      nslices = int((total_events_to_generate + nchunk - 1) / nchunk)
      count = nslices - count
   if start < 0:
      Print("Error - start slice is less than zero!",
            "Nothing to do, quitting...")
      sys.exit(1)
   if count <= 0:
      Print("Error - start slice is greater than the job max slice count!",
            "Nothing to do, quitting...")
      sys.exit(1)
   logdir = jobname + ".logs"
   batchfile = logdir + "/" + "batches.log"
   if not os.path.exists(batchfile):
      Print("Error - no record exists of this job ever having been submitted!")
      sys.exit(1)
   cancel_range = {}
   for line in open(batchfile):
      fields = line.rstrip().split()
      batch = int(fields[0])
      first = int(fields[1])
      number = int(fields[2])
      lim0 = start - first
      lim1 = lim0 + count
      if lim0 < 0:
         lim0 = 0
      if lim1 > number:
         lim1 = number
      cancel_range[batch] = (lim0, lim1)
      if lim1 > lim0:
         Print("todo: condor_rm", str(batch) + "." + str(lim0) + "-" + str(lim1))

def validate_customizations():
   """
   Check that this script has been properly customized by the user,
   otherwise refuse to continue.
   """
   lines = 0
   for line in open(sys.argv[0]):
      if re.search(r"TEMPLATE JOB SCRIPT FOR GLUEX OSG PRODUCTION", line) or\
         re.search(r"YOU MUST REPLACE .* ABOVE WITH A UNIQUE NAME", line) or\
         re.search(r"CUSTOMIZE THE SCRIPT SO THE JOB DOES WHAT YO", line) or\
         re.search(r"HEADER LINES (THE ONES BETWEEN THE ===) WITH", line) or\
         re.search(r"WHAT IT DOES, AND SAVE IT UNDER THE NEW NAME", line) or\
         re.search(r"^# jobname: gridjob-template", line) or\
         re.search(r"^# author: gluex.experimenter@jlab.org", line) or\
         re.search(r"# created: jan 1, 1969",line):
         return 1
      lines += 1
      if lines > 30:
         break
   return 0

def execute(args, do_slice):
   """
   This method is normally the only one that the user job script will need
   to invoke directly. It provides the core functionality of the user job
   script through a uniform interface.
   """
   global jobnames
   jobnames = os.path.basename(args[0])
   global jobname
   jobname = re.sub(r"\.py$", "", jobnames)

   if validate_customizations() != 0:
      Print("Error - this job script is a template;",
            "it must be customized before you can run it.")
      Print("At the very minimum, you must update the author and date fields",
            "in the header,")
      Print("and fill in some descriptive text between the === lines.")
      sys.exit(1)

   if len(args) < 2:
      usage()
   elif args[1] == "info":
      retcode = do_info(args[2:])
   elif args[1] == "status":
      retcode = do_status(args[2:])
   elif args[1] == "submit":
      retcode = do_submit(args[2:])
   elif args[1] == "cancel":
      retcode = do_cancel(args[2:])
   elif args[1] == "doslice":
      retcode = do_slice(args[2:])
   else:
      usage()
   sys.exit(retcode)
