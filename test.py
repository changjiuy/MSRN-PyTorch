﻿# Function：test.py
# Author：MIVRC
# Time：2018.2.1

import argparse
import torch
from torch.autograd import Variable
import numpy as np
import time, math 
import scipy.io as sio
from os import listdir
from os.path import join
from skimage.measure import compare_ssim

parser = argparse.ArgumentParser(description="SR test")
parser.add_argument("--cuda", action="store_true", help="use cuda?")
parser.add_argument("--model", default="Weights/200.pth", type=str, help="model path")
parser.add_argument("--imagepath", default="/TEST/set14_x4", type=str, help="image path")
parser.add_argument("--scale", default=4, type=int, help="")

opt = parser.parse_args()
cuda = opt.cuda

# PSNR
def PSNR(pred, gt, shave_border=0):
    height, width = pred.shape[:2]
    pred = pred[shave_border:height - shave_border, shave_border:width - shave_border]
    gt = gt[shave_border:height - shave_border, shave_border:width - shave_border]
    imdff = pred - gt
    rmse = math.sqrt(np.mean(imdff ** 2))
    if rmse == 0:
        return 100
    return 20 * math.log10(255.0 / rmse)

# SSIM
def SSIM(pred, gt, shave_border=0):
    height, width = pred.shape[:2]
    pred = pred[shave_border:height - shave_border, shave_border:width - shave_border]
    gt = gt[shave_border:height - shave_border, shave_border:width - shave_border]
    ssim = compare_ssim(gt, pred, data_range=gt.max() - pred.min())
    if ssim == 0:
        return 100
    return ssim

def is_image_file(filename):
    return any(filename.endswith(extension) for extension in [".mat"])

model = torch.load(opt.model)["model"]

if cuda and not torch.cuda.is_available():
    raise Exception("No GPU found, please run without --cuda")

image = [join(opt.imagepath, x) for x in listdir(opt.imagepath) if is_image_file(x)]

sum_bicubic_psnr = 0
sum_predicted_psnr = 0
sum_bicubic_ssim = 0
sum_predicted_ssim = 0
all_use_time = 0

# Test
for _, j in enumerate(image):
    print(j)

    im_gt_y = sio.loadmat(j)['im_gt_y']
    im_b_y = sio.loadmat(j)['im_b_y']
    im_l_y = sio.loadmat(j)['im_l_y']

    im_gt_y = im_gt_y.astype('double')
    im_b_y = im_b_y.astype('double')
    im_l_y = im_l_y.astype('double')

    psnr_bicubic = PSNR(im_gt_y, im_b_y, shave_border=opt.scale)
    sum_bicubic_psnr += psnr_bicubic
    ssim_bicubic = SSIM(im_gt_y, im_b_y, shave_border=opt.scale)
    sum_bicubic_ssim += ssim_bicubic

    im_input = im_l_y / 255.
    im_input = Variable(torch.from_numpy(im_input).float(), volatile=True).view(1
