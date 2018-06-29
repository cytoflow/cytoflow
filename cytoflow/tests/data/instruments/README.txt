Informal README by Josef Spidlen 
Points that may help developers implement robust FCS readers
************************************************************

- Generally speaking, older instruments used mostly 16 bit integers and newer instruments use 32 bit floating points. Make sure to apply a mask if $DATATYPE/I/ and $PnR is less than 2^$PnB. It is not very common, but I have seen an FCS file where the manufacturer stored custom information in the extra bits. For example, if $PnB/16/ and $PnR/1024/, then there are 6 unused bits in each value and you should set these to 0 after reading the value from FCS or else you could see some surprises.
- $DATATYPE/A/ is virtually never used, $MODE is virtually always /L/; you can just check those and refuse reading the file in an odd case that this is not true.
- $BYTEORD is virtually always either big or little endian. Some other weird byte orders have been seen historically in like the 80s, but I don't think you need to worry about those any more. However, expect that some instruments write just /1,2/ rather than /1,2,3,4/ for little endian and /2,1/ instead of /4,3,2,1/ for big endian.
- Beware that some instruments are off by one byte when specifying the offset of the end of the TEXT segment (i.e., they may point just behind the TEXT segment rather than to the last byte of the TEXT segment.)
- Whenever you are reading an ASCII-encoded numeric value in the TEXT segment or in the HEADER, strip out white spaces and also make sure leading zeros will not be a problem for you.
- In most cases (except for "LMD" files), there is only one dataset in an FCS datafile. LMD files tend to store 2 datasets, but these contain the "same" data - one is usually FCS2.0 and the other FCS3.0, possibly compensated and somehow "polished".
- $BEGIN.... $END.... keywords in FCS >= 3.0 are sometimes missing or set to 0, which is wrong, but you may want to just use the offset information from the header in those cases.

