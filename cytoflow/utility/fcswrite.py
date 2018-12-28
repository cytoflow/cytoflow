#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
fcswrite.py
-----------

Write .fcs files for flow cytometry

Adapted from https://github.com/ZELLMECHANIK-DRESDEN/fcswrite

"""
from __future__ import print_function, unicode_literals, division

import numpy as np
import struct

def write_fcs(filename, chn_names, chn_ranges, data,
              compat_chn_names=True,
              compat_percent=True,
              compat_negative=True,
              compat_copy=True,
              verbose=0,
              **kws):
    """
    Write numpy data to an .fcs file (FCS3.0 file format)
    
    
    Parameters
    ----------
    filename: str
        Path to the output .fcs file
        
    chn_names: list of str, length C
        Names of the output channels
        
    chn_ranges: dictionary
        Keys: channel names.  Values: ranges
        
    data: 2d ndarray of shape (N,C)
        The numpy array data to store as .fcs file format. 
        
    compat_chn_names: bool
        Compatibility mode for 3rd party flow analysis software:
        The characters " ", "?", and "_" are removed in the output
        channel names.
        
    compat_percent: bool
        Compatibliity mode for 3rd party flow analysis software:
        If a column in `data` contains values only between 0 and 1,
        they are multiplied by 100.
        
    compat_negative: bool
        Compatibliity mode for 3rd party flow analysis software:
        Flip the sign of `data` if its mean is smaller than zero.
        
    compat_copy: bool
        Do not override the input array `data` when modified in
        compatibility mode.

    kwargs : Str
        Additional keyword arguments are written as keyword/value pairs in
        the TEXT segment of the FCS file.

    Notes
    -----
    These commonly used unicode characters are replaced: "µ", "²"

    """
    if not isinstance(data, np.ndarray):
        data = np.array(data)
    
    msg="length of `chn_names` must match length of 2nd axis of `data`"
    assert len(chn_names) == data.shape[1], msg

    rpl = [["µ", "u"],
           ["²", "2"],
          ]
    
    if compat_chn_names:
        # Compatibility mode: Clean up headers.
        rpl += [[" ", ""],
                ["?", ""],
                ["_", ""],
                ]

    for i in range(len(chn_names)):
        for (a, b) in rpl:
            chn_names[i] = chn_names[i].replace(a, b)

    if compat_percent:
        # Compatibility mode: Scale values b/w 0 and 1 to percent
        toscale = []
        for ch in range(data.shape[1]):
            if data[:,ch].min() > 0 and data[:,ch].max() < 1:
                toscale.append(ch)
        if len(toscale):
            if compat_copy:
                # copy if requested
                data = data.copy()
            for ch in toscale:
                data[:,ch] *= 100

    if compat_negative:
        toflip = []
        for ch in range(data.shape[1]):
            if np.mean(data[:,ch]) < 0:
                toflip.append(ch)
        if len(toflip):
            if compat_copy:
                # copy if requested
                data = data.copy()
            for ch in toflip:
                data[:,ch] *= -1
        

    # DATA segment
    data1 = data.flatten().tolist()
    DATA = struct.pack('>%sf' % len(data1), *data1)

    # TEXT segment
    # fix length of TEXT to 4 kilo bytes
    ltxt = 4096
    ver='FCS3.0'
    textfirst= '{0: >8}'.format(256)
    datafirst= '{0: >8}'.format(256+ltxt)
    datalast = '{0: >8}'.format(256+ltxt+len(DATA)-1)
    anafirst = '{0: >8}'.format(0)
    analast  = '{0: >8}'.format(0)
    # use little endian
    #byteord = '1,2,3,4'
    # use big endian
    byteord = '4,3,2,1'
    TEXT ='/$BEGINANALYSIS/0/$ENDANALYSIS/0'
    TEXT+='/$BEGINSTEXT/0/$ENDSTEXT/0'
    TEXT+='/$BEGINDATA/{0}/$ENDDATA/{1}'.format(256+ltxt, 256+ltxt+len(DATA)-1)
    TEXT+='/$BYTEORD/{0}/$DATATYPE/F'.format(byteord)
    TEXT+='/$MODE/L/$NEXTDATA/0/$TOT/{0}'.format(data.shape[0])
    TEXT+='/$PAR/{0}'.format(data.shape[1])

    for i in range(data.shape[1]):
        pnrange = chn_ranges[chn_names[i]]
        # TODO:
        # - Set log/lin 
        TEXT+='/$P{0}B/32/$P{0}E/0,0/$P{0}N/{1}/$P{0}R/{2}/$P{0}D/Linear'.format(i+1, chn_names[i], pnrange)

    for kw, val in kws.items():
        kw = kw.replace('/', '//')
        val = val.replace('/', '//')
        TEXT+='/{0}/{1}'.format(kw, val)

    TEXT += '/'
    
    if len(TEXT) > ltxt:
        raise RuntimeError("TEXT segment is too long; specify fewer keywords")

    textlast = '{0: >8}'.format(len(TEXT)+256-1)
    TEXT = TEXT.ljust(ltxt, ' ')

    # HEADER segment
    HEADER = '{0: <256}'.format(ver+'    '+
                                textfirst +
                                textlast  +
                                datafirst +
                                datalast  +
                                anafirst  +
                                analast)

    # Write data
    with open(filename, "wb") as fd:
        fd.write(HEADER.encode("ascii"))
        fd.write(TEXT.encode("ascii"))
        fd.write(DATA)
        fd.write(b'00000000')

