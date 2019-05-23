TRIGGER CAMERA MODE
-------------------------

# Listening for frames
Tell it the window +/- using -w and give it an IP address to listen on.
It will listen on UDP 1338.
You also need to give it the mappings.
For example

```bash
$ ./rasterize.py -w 4 svsc-triggercam.maps 10.0.5.3
```

will listen on 10.0.5.3 port 1338 for SVSC frames.
It will write them to sequentially numbered PNG files, in the directory where you run the command.

# Making a movie

To turn the output PNG into a "movie," use

```bash
$ ffmpeg -r 1 -i %08d.png -c:v libx264 -vf fps=1 -pix_fmt yuv420p out_50_muon.mp4
```

Here `-r` says 1 frame a second, and the desired filename for the movie is at the end.

# Replaying stashed data

If you have stashed frames in ASCII using

1. netcat
2. xxd -p -c 4 > stashed_data

you can replay them to your running rasterizer on 10.0.5.3 by

```bash
$ cat stashed_data | ./replayer.py -w 4 10.0.5.3
```




