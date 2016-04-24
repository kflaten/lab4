#CMiC Image Compressor Starter file
#first some imports
import sys
import scipy
import scipy.ndimage
import numpy as np
import PIL
import pywt
import argparse
#wrapper for showing np.array() as an image
def show(image):
	scipy.misc.toimage(image).show()

#open the image and take the 2D DWT
#After that, it's up to you!
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
	#get height and width
	(height, width) = im.shape
	wavelet = args.wavelet
	q = args.quantize
	
	LL, (LH, HL, HH) = pywt.dwt2(im, wavelet, mode='periodization')
	
	'''the following block of code will let you look at the decomposed image. Uncomment it if you'd like
	'''
	dwt = np.zeros((height, width))
	dwt[0:height/2, 0:width/2] = LL
	dwt[height/2:,0:width/2] = HL
	dwt[0:height/2, width/2:] = LH
	dwt[height/2:,width/2:] = HH
	show(dwt)
	

if __name__ == '__main__':
	main()