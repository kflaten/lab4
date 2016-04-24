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
    if len(lst) == 1:
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


def write_out_file(lst, code_dict, bin_string):
    with open("compression.bin", "wb") as out_file:
        hash = hashlib.md5(open(sys.argv[1], "rb").read()).hexdigest()

        size = len(lst)

        header = {'size': size, 'hash': hash}
        json.dump(header, out_file)
        out_file.write("\n")
        code_dict = dict((ord(k), v)  for k, v in code_dict.items())
        json.dump(code_dict, out_file)
        out_file.write("\n")
        out_file.write(char2bin(bin_string))


def bin_string_offset(code_dict):
    bin_string = huff_encode(code_dict, sys.argv[1])
    rem = (len(bin_string) % 8)
    bin_string += "0" * (8 - rem)

    return bin_string


def decompress_bin_string():
    # in_file = open(sys.argv[1], "rb")
    in_file = open("compression.bin", "rb")
    header = json.loads(in_file.readline())
    huffman_code = json.loads(in_file.readline())
    decode_dict = {v.encode(): chr (int (k)) for k, v in huffman_code.iteritems()}
    # print decode_dict
    binary_data = in_file.read()
    binary_string = ""
    for byte in binary_data:
        binary_string += format(ord(byte), '08b')
    # print binary_string

    decoded_data = ""
    while len(decoded_data) != header['size']:
        sub_str = ""
        i = 0
        # print len(decoded_data)
        while sub_str not in decode_dict:
            # print i
            # print sub_str
            sub_str = binary_string[0:i]
            i += 1
        decoded_data += decode_dict[sub_str]
        binary_string = binary_string[i-1:]

    if hashlib.md5(decoded_data).hexdigest() == header['hash']:
        f = open(sys.argv[2], 'wb')
        f.write(decoded_data)
        f.close()
        print "MD hash mathced. Wrote %i bytes to %s" %(len(decoded_data), sys.argv[2])
    else:
        print "MD5 hash mismatch"

    return binary_string



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
    show(im)
    # get height and width
    (height, width) = im.shape
    wavelet = args.wavelet
    q = args.quantize

    LL, (LH, HL, HH) = pywt.dwt2(im, wavelet, mode='periodization')
    # print height * width
    flat_LL = LL.flatten()
    # print len(flat_LL)

    flat_LL2 = np.insert(flat_LL, 0, 0.0)
    diff_flat_LL2 = np.diff(flat_LL2)
    cum_flat_LL = np.cumsum(diff_flat_LL2)

    HLq = HL / q
    LHq = LH / q
    HHq = HH / q

    HLq_np = np.array(HLq)
    HLq_int = HLq_np.astype(int)
    HLq_lst = list(HLq_int)    

    HHq_np = np.array(HHq)
    HHq_int = HHq_np.astype(int)
    HHq_lst = list(HHq_int)

    LHq_np = np.array(LHq)
    LHq_int = LHq_np.astype(int)
    LHq_lst = list(LHq_int)

    flat_LL_lst = list(cum_flat_LL)

    img_lst = flat_LL_lst + LHq_lst + HLq_lst + HHq_lst

    sorted_list = char_count(img_lst)

    code_dict = construct_code_dict(sorted_list)

    bin_string = bin_string_offset(code_dict)

    write_out_file(lst, code_dict, bin_string)

    decompressed_bin = decompress_bin_string()

    header = {'version': 'CMiCv1', 'height': height, 'width': width, 'wavelet': wavelet, 'q': quantization}
    json.dump(header, out_file)
    out_file.write("\n")
    code_dict = dict((ord(k), v)  for k, v in code_dict.items())
    json.dump(code_dict, out_file)
    out_file.write("\n")
    out_file.write(char2bin(bin_string))

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
