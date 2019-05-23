#!/usr/bin/python3
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
parser.add_argument('offsets',
                    help='A two-column ascii file giving the integer offsets that map data position in the frame to pixel position in the image')
parser.add_argument('server',
                    help='IP address to bind (for listening. Uses port 1338)')

args = parser.parse_args()

# Check for -w 0 (single frame)
if args.window == 0:
    args.window = 1
else:
    args.window *= 2

print("Expecting %d frames" % args.window)
print("Getting the data -> pixel map...")
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
print("Data to pixel maps acquired.")

# Make a matrix file for gnuplot
matrix = []

streamBreak = False

try:
    server = socket.gethostbyname(args.server)
    
except Exception as e:
    print("TROUBLE: could not resolve %s" % args.server, e)
    raise
        
# Try to set up a socket
try:
    src = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Hardcode for now
    src.bind((server, 1338))
except Exception as e:
    print("TROUBLE: could not bind the server datagram socket", e)
    raise

print("Socket open and listening for frames...")

timestamp = 0
packetCount = 0

# Grab a window*64-bit frames
while True:
    raster = open("frame_pipe", 'w')

    # Get an entire frame
    # UDP semantics: UNIX reads out everything that came in all at once.
    #                we only expect single packets to arrive, so read out
    #                exactly the size of a single packet
    # Use this line for actual live mode collecting data from the board
    data, addr = src.recvfrom(4*2 + args.window*8 + 4)

    print("Beginning packet %d..." % packetCount)
    
    # Grab a header and timestamp
    header = int.from_bytes(data[:4], byteorder='big')
    timestamp += 1 # int.from_bytes(data[4:8], byteorder='big')

    # Rasterize
    for win in range(0, args.window):
        print("\tReading bytes %d -> %d: " % (8 + win*8, 8 + win*8 + 8), end='')
        
        rawread = data[8 + win*8:8 + win*8 + 8] #sys.stdin.buffer.read(8)
        frame = int.from_bytes(rawread, byteorder='big')
        if len(rawread) < 8:
            # We've hit end of file
            print("Hit end of stream?  At window %d, read %d bytes" % (win, len(rawread)))
            streamBreak = True
            break
        
        print(frame)

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

    print("Footer read.  Packet %d complete" % packetCount)
    raster.close()
    packetCount += 1
    
    # Render the packet
    os.system("cat svsc.gpt | sed 's/__WINDOWS__/%s/g' | sed 's/__FILENAME__/%.8d/g' | gnuplot" % (args.window, timestamp))
