#!/usr/bin/env python

import collections
import ctypes
import os
import sys
import time
from time import gmtime, strftime

# logging
import win32api
import win32con
import win32evtlog
import win32security
import win32evtlogutil
ph = win32api.GetCurrentProcess()
th = win32security.OpenProcessToken(ph, win32con.TOKEN_READ)
my_sid = win32security.GetTokenInformation(th, win32security.TokenUser)[0]
applicationName = "video drive cleaner"
eventID = 1
category = 5	# Shell
myType = win32evtlog.EVENTLOG_WARNING_TYPE

# path constant
video_path = 'F:\\'


def sorted_file(file_path):
    #create a list of files and sizes
    mtime_and_path = {}
    # gets a list of all movies
    for path, subdirs, files in os.walk(file_path):
        for name in files:
            # add to dicitonary in format [m_time, path]
            mtime_and_path[os.stat(os.path.join(path, name)).st_mtime]=os.path.join(path, name)
    #create a new dictionary where the values are sorted by mtime
    sorted_file_dictionary = {}
    for key, value in sorted(mtime_and_path.iteritems(), key=lambda (k,v): (v,k)):
        sorted_file_dictionary[key]=value
    return(sorted_file_dictionary)

def used_space_percentage(file_path):
    _ntuple_diskusage = collections.namedtuple('usage', 'total used free')
    _, total, free = ctypes.c_ulonglong(), ctypes.c_ulonglong(), \
                       ctypes.c_ulonglong()
    if sys.version_info >= (3,) or isinstance(file_path, unicode):
        fun = ctypes.windll.kernel32.GetDiskFreeSpaceExW
    else:
        fun = ctypes.windll.kernel32.GetDiskFreeSpaceExA
    ret = fun(file_path, ctypes.byref(_), ctypes.byref(total), ctypes.byref(free))
    if ret == 0:
        raise ctypes.WinError()
    return((total.value * 1.0 - free.value) / total.value)


# get start_time
start_time = time.time()

# get a list of sorted files
sorted_files=sorted_file(video_path)
initial_used_percentage = used_space_percentage(video_path)

#create a new dictionary where the values of deleted files are stored
deleted_files = []
# get the used space percentage
while used_space_percentage(video_path) >= .95:

    # add deleted files to list
    deleted_files.append(sorted_files.values()[-1])
    # delete file
    os.remove(sorted_files.values()[-1])
    # remove file from list
    sorted_files.pop(sorted_files.keys()[-1])



final_used_percentage = used_space_percentage(video_path)

# what to log
data = 'Date: {0}\nDuration(s): {1}\nFree Percentage Before: {2}\nFree \
Percentage After: {3}\nList of deleted files:\n{4}'.format(strftime("%Y-%m-%d %H:%M:%S"), time.time() - 
start_time, (1 - initial_used_percentage) * 100 , (1 - final_used_percentage) * 100, '\n'.join(deleted_files))

# log to event viewer
descr = ["video drive cleaner ran\n" + data.encode("ascii")]
win32evtlogutil.ReportEvent("video drive cleaner", 16394, eventCategory=9876, 
	eventType=win32evtlog.EVENTLOG_WARNING_TYPE, strings=descr, data=data, sid=my_sid)