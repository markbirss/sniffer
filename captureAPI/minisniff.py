#!/usr/bin/env python

#----------------------------------------------------------------------
# Name:        minisniff.py
# Purpose:     example of running the sniffer hardware via a DLL/SO
#
# Author:      Tim
#
# Created:     01/10/2018
# Copyright:   (c) Tim 2018
# Licence:     see the LICENSE.txt file
#----------------------------------------------------------------------

from __future__ import print_function

import sys, ctypes, time, os.path

from ctypes import *

##---------------------------------------------------------
INIT_OK                       =  0
E_SNIFFER_NOT_FOUND           = -1
E_CANNOT_CONFIGURE_HARDWARE   = -2
E_SNIFFER_LICENSE_INVALID     = -3
E_NOT_INITIALIZED             = -4
E_BUFFER_ALLOCATION_FAILED    = -5

##---------------------------------------------------------
# note that this DLL/SO uses false=0, true=1
def main():
  sniffer = None
  try:

    dll_name = "libsniff_min.dll"
    # dllabspath = os.path.dirname(os.path.abspath(__file__))
    # dllabspath += os.path.sep + dll_name
    try:
      mini = ctypes.CDLL(dll_name)    # or dllabspath
    except OSError:
      try:
        mini = ctypes.CDLL("libsniff_min.so")
      except OSError:
        print('libsniff_min.dll or libsniff_min.so is missing - exiting')
        return

    buff = create_string_buffer(256)
    rv = mini.version(buff, sizeof(buff))
    print('Using library version: %s\n' % repr(buff.value))

    # beeps from your computer as drivers are loaded :)
    sniffer = c_int(mini.sniffInit())
    
    # loop while waiting for the OS to do its thing
    snifferStatus = E_SNIFFER_NOT_FOUND 
    for i in range(0, 6):
      stat = c_int(mini.getHardwareStatus(sniffer))
      snifferStatus = stat.value
      if snifferStatus != E_SNIFFER_NOT_FOUND:
        break
      time.sleep(1)    

    if snifferStatus != INIT_OK:        # probably timed out
      print('problem !!!!')
      mini.sniffEnd(sniffer)
      return

    # here when the sniffer is found OK
    # disconnect
    mini.setConnect(sniffer, 0)
    needed = 16 * 1024                  # easily covers setup
    mini.setNeeded(sniffer, needed)  
    # reconnect and run
    mini.setRun(sniffer, 1)

    # loop until finished
    # capture first
    while True:
      cc    = mini.getCaptureCount(sniffer)
      cdone = mini.getCaptureDone(sniffer)
      print(cc, ' ', sep='')
      if cdone:
        break
      time.sleep(1)    

    # then decode
    print(' ---> ')
    mini.startDecode(sniffer);
    while True:
      dc    = mini.getDecodedCount(sniffer)
      ddone = mini.getDecodeDone(sniffer)
      print(dc, ' ', sep='')
      if ddone:
        break
      time.sleep(1)    

    # get packet data plus decoded transactions, etc.
    lineCount = mini.getPacketDataRowCount(sniffer) 
    print(lineCount, 'decoded rows')

    ofile = open('pyoutput.txt', 'w')
    # a huge buffer..
    rowBuf = create_string_buffer(10 * 1024)    

    for i in range(0, lineCount):
      mini.getPacketDataRow(sniffer, i, rowBuf, sizeof(rowBuf))
      # decoded rows are terminated with \n\0
      # now you can split the data, analyze it any way you want...
      # this program just writes out a file
      ofile.write(rowBuf.value)

    ofile.close()      

    mini.sniffEnd(sniffer)

  except:
    e = sys.exc_info()[0]
    print('\nException caught %s\n' % e)

##---------------------------------------------------------
if __name__ == '__main__':
  print('====================hello==========================')
  main()
  print('\n==================== bye ==========================')

##---------------------------------------------------------
# in C++ this becomes:
#
#int mainx(sniffHandle sniffer) {
#  int stat = E_SNIFFER_NOT_FOUND;
#
#  for (unsigned ix = 0; ix < 10; ix++) {
#    std::this_thread::sleep_for(std::chrono::seconds(1));
#    stat = getHardwareStatus(sniffer);
#    if (stat != E_SNIFFER_NOT_FOUND)
#      break;
#    }
#
#  if (stat != INIT_OK)
#    return EXIT_FAILURE;
#
#  setConnect(sniffer, false);
#  setNeeded(sniffer, 16 * 1024);
#  setRun(sniffer, true);
#
#  // capture
#  while (true) {
#    std::cout << getCaptureCount(sniffer) << ' ';
#    if (getCaptureDone(sniffer))
#      break;
#    std::this_thread::sleep_for(std::chrono::seconds(2));
#    }
#
#  // then decode
#  std::cout << " ---> ";
#  startDecode(sniffer);
#  while (true) {
#    std::cout << getDecodedCount(sniffer) << ' ';
#    if (getDecodeDone(sniffer))
#      break;
#    std::this_thread::sleep_for(std::chrono::seconds(1));
#    }
#
#  std::ofstream ofile("experiment.txt");
#  auto lineCount = getPacketDataRowCount(sniffer);
#  char buf[1024 * 10];
#  for (unsigned i = 0; i < lineCount; i++) {
#    getPacketDataRow(sniffer, i, buf, sizeof(buf));
#    ofile << buf;
#    }
#  return EXIT_SUCCESS;
#  }
#
#//--------------------------------------------
#int main() {
#  std::cout << "\n";
#  auto sniffer = sniffInit();
#
#  char buff[256];
#  version(buff, sizeof(buff));
#  std::cout << "\nUsing " << buff << '\n';
#
#  int ret = mainx(sniffer);
#
#  sniffEnd(sniffer);
#  std::cout << "--------\n\n";
#  return ret;
#  }
#
# EOF -----------------------------------------------------------------
