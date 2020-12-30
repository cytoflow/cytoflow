import sys, re, os, glob

r = re.compile(sys.argv[1])
for f in glob.glob(sys.argv[3]):
    new_f = r.sub(sys.argv[2], f)
    print("{} --> {}".format(f, new_f))
    os.rename(f, new_f)



