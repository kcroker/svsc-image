#!/usr/bin/python3

# replayer.py - takes 32bit/line ASCII hex encoded dump and replays it
#               to the raterizer

import sys
import argparse
import os
import pdb
import socket

parser = argparse.ArgumentParser(description='Visualize svsc trigger bit frames')
parser.add_argument('-w',
                    dest='window',
                    help='number of frames before and after (inclusive) the trigger frame',
                    type=int)
#parser.add_argument('-r',
#                    dest='resolution',
#                    type=int,
#                    help='resolution of the data in each frame')
#parser.add_argument('offsets',
#                    help='A two-column ascii file giving the integer offsets that map data position in the frame to pixel position in the image')
parser.add_argument('host',
                    help='EEVEE board')

args = parser.parse_args()

# Check for -w 0 (single frame)
if args.window == 0:
    args.window = 1
else:
    args.window *= 2

print("Expecting %d frames" % args.window)

while True:
    data = sys.stdin.buffer.read( (4*2 + args.window*8 + 4)*8 + 19)
    if len(data) < (4*2 + args.window*8 + 4)*8 + 19:
        break
    
    tmp = open("tmp", 'w')
    tmp.buffer.write(data)
    tmp.close()

    os.system("cat tmp | xxd -r -p  | /bin/nc -u %s 1338 -q 0" % (args.host))
 
print("Done.")
