from punk import Punk
import os
import logging
punk = Punk()

def chunkInject(chunk,dest,base='base.png'):
    with open(base, 'rb') as src, open(dest, 'ab') as dst: dst.write(src.read())
    with open(chunk, 'rb') as src, open(dest, 'ab') as dst: dst.write(src.read())
    # try:
    #     punk.encode(dest,open(chunk,'rb+').read())
    # except BaseException:
    #     logging.exception('error')
    # return dest

def decode(in_file,out_file):
    punk.decode(in_file,out_file)

