#!/usr/bin/python3 -u
import sys
import argparse
import os
import pdb
import socket
import select

parser = argparse.ArgumentParser(description='Rasterize svsc frames into ascii matrixen')
parser.add_argument('-w',
                    dest='window',
                    help='number of frames before and after (inclusive) the trigger frame',
                    type=int)
parser.add_argument('-r',
                    dest='resolution',
                    type=int,
                    help='resolution of the data in each frame')
parser.add_argument('offsets',
                    help='A two-column ascii file giving the integer offsets that map data position in the frame to pixel position in the image')
parser.add_argument('host',
                    help='EEVEE board')

args = parser.parse_args()

# Check for -w 0 (single frame)
if args.window == 0:
    args.window = 1
else:
    args.window *= 2

# Rasterizes based on Keefe's format
masks = {}

for line in open(args.offsets):
    try:
        vals = list(map(int, line.split()))
    except Exception:
        print("Skipped garbage:\n\t'%s'" % line, file=sys.stderr)
        continue

    # ugh, use zero-indexing plz
    masks[vals[0]] = 1 << (vals[1]-1)

# Now we have the bitmasks
#print(masks)

# Make a matrix file for gnuplot
matrix = []

streamBreak = False

try:
    host = socket.gethostbyname(args.host)
    
except Exception as e:
    print("TROUBLE: could not resolve %s" % args.host, e)
    raise
        
# Try to set up a socket
try:
    src = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Hardcode for now
    src.bind((host, 1338))
except Exception as e:
    print("TROUBLE: could not grab a datagram socket", e)
    raise

# Grab a window*64-bit frames
while True:
    raster = open("frame_pipe", 'w')

    # Socket select
    # ready = select.select([src], [], [], 0)
                
    # Get an entire frame
    # XXX This is stupid, because it won't generalize...
    #     need to re-engineer.
    data, addr = src.recvfrom(4*2 + (1+args.window)*8 + 4)

    # Echo it out
    # print(data)
    
    # Grab a header and timestamp
    header = int.from_bytes(data[:4], byteorder='big')
    timestamp = int.from_bytes(data[4:8], byteorder='big')

    # Rasterize
    for win in range(0, args.window):
        rawread = data[8 + win*16:8 + win*16 + 8] #sys.stdin.buffer.read(8)
        frame = int.from_bytes(rawread, byteorder='big')
        if len(rawread) < 8:
            # We've hit end of file
            streamBreak = True
            break
        
        # print(frame)

        for i in range(0, 8):
            for j in range(0, 8):
                position = 1 + 8*i + j
                print("%d " % (1 if (frame & masks[position]) > 0 else 0), file=raster, end='')
            print(file=raster)
        print(file=raster)

    # Check for stream break
    if streamBreak:
        raster.close()
        break
        
    # Now read in a footer
    footer = int.from_bytes(data[-4:], byteorder='big')

    # print("Footer read")
    raster.close()

    # Sanity check this
    os.system("cat svsc.gpt | sed 's/__WINDOWS__/%s/g' | sed 's/__FILENAME__/%.8d/g' | gnuplot" % (args.window, timestamp))
