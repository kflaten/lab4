# CMiC Image Compressor Starter file
# first some imports
import sys
import scipy
import scipy.ndimage
import numpy as np
import PIL
import pywt
import argparse
import struct
import json
import hashlib
import os
from collections import Counter



# wrapper for showing np.array() as an image
def show(image):
    scipy.misc.toimage(image).show()

def char_count(lst):
    char_dict = {}
    input_char_array = []

    for char in lst:
        key = char
        if key in char_dict:
            char_dict[key] += 1
        else:
            char_dict[key] = 1

    char_list = char_dict.items()

    return char_list


def huff(lst, side, code):
    if type(lst) is np.int64:
        code.append((lst, side))
    else:
        left = huff(lst[0], side + "0", code)
        right = huff(lst[1], side + "1", code)


def char2bin(input):
    binary = ""
    for i in range(0, len(input) / 8):
        bits = input[i * 8:i * 8 + 8]
        b = 0
        powers = range(0, 8)
        powers.reverse()

        for i in range(len(bits)):
            b += int(bits[i]) * pow(2, powers[i])

        binary += struct.pack("B", b)

    return binary


def huff_encode(code_dict, lst):
    coded_string = ""

    for byte in lst:
        for key, value in code_dict.iteritems():
            if byte == key:
                coded_string += value
    return coded_string


def construct_code_dict(sorted_list):
    while len(sorted_list) > 1:
        v = sorted_list[0][1] + sorted_list[1][1]
        k = [sorted_list[0][0], sorted_list[1][0]]
        sorted_list = sorted_list[2:]
        sorted_list.append([k, v])
        sorted_list = sorted(sorted_list, key=lambda y: y[1])

    tree = sorted_list[0][0]
    code = []
    huff(tree, "", code)

    return dict(code)


def write_out_file(code_dict, bin_string, height, width, wavelet, q):
    with open("output.cmic", "wb") as out_file:
        header = {'version': 'CMiCv1', 'height': height, 'width': width, 'wavelet': wavelet, 'q': q}
        json.dump(header, out_file)
        out_file.write("\n")
        code_dict = dict((k, v)  for k, v in code_dict.items())
        json.dump(code_dict, out_file)
        out_file.write("\n")
        out_file.write(char2bin(bin_string))


def bin_string_offset(code_dict, lst):
    bin_string = huff_encode(code_dict, lst)
    rem = (len(bin_string) % 8)
    bin_string += "0" * (8 - rem)

    return bin_string

# open the image and take the 2D DWT
# After that, it's up to you!
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_image")
    parser.add_argument("output_file")
    parser.add_argument("--wavelet", help="wavelet name to use. Default=haar", default="haar")
    parser.add_argument("--quantize", help="quantization level to use. Default=4", type=int, default=4)
    args = parser.parse_args()

    input_file_name = args.input_image
    try:
        im = scipy.ndimage.imread(input_file_name, flatten=True, mode="L")
        print "Attempting to open %s..." % input_file_name
    except:
        print "Unable to open input image. Qutting."
        quit()
    #show(im)
    # get height and width
    (height, width) = im.shape
    wavelet = args.wavelet
    q = args.quantize

    LL, (LH, HL, HH) = pywt.dwt2(im, wavelet, mode='periodization')
    #show(LL)
    flat_LL = LL.astype(int).flatten()


    flat_LL2 = np.insert(flat_LL, 0, 0)
    diff_flat_LL2 = np.diff(flat_LL2)
    #cum_flat_LL = np.cumsum(diff_flat_LL2)

    HLq = HL / q
    LHq = LH / q
    HHq = HH / q

    HLq_lst = list(HLq.flatten().astype(int))
    HHq_lst = list(HHq.flatten().astype(int))
    LHq_lst = list(LHq.flatten().astype(int))  

    flat_LL_lst = list(diff_flat_LL2)

    #img_lst = list(cum_flat_LL.astype(int), LHq.flatten().astype(int), HLq.flatten().astype(int), HHq.flatten().astype(int))

    img_lst = flat_LL_lst + LHq_lst + HLq_lst + HHq_lst
    print img_lst
    #print img_lst
    #quit()

    sorted_list = dict(Counter(img_lst)).items()
    
    code_dict = construct_code_dict(sorted_list)

    bin_string = bin_string_offset(code_dict, img_lst)

    write_out_file(code_dict, bin_string, height, width, wavelet, q)
    

    '''the following block of code will let you look at the decomposed image. Uncomment it if you'd like
    dwt = np.zeros((height, width))
    dwt[0:height / 2, 0:width / 2] = LL
    dwt[height / 2:, 0:width / 2] = HL
    dwt[0:height / 2, width / 2:] = LH
    dwt[height / 2:, width / 2:] = HH
    show(dwt)
    '''


if __name__ == '__main__':
    main()
