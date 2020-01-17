import cv2 as cv
import sys
from CellPointDetector import pointInCell, allContourPoints
from skeletonize import find_skeleton
import statistics as st
import numpy as np

# Reads the videofile
# Select the videofile
if (len(sys.argv) < 2):
    data_file = input('Name of the file: ')
else:
    data_file = sys.argv[1]


v = cv.VideoCapture(data_file)

# Checks if the videofile is opened
if not v.isOpened():
    print('File couldn\'t be opened')
    exit()

# Extracts each frame
stop = -1
while stop == -1:
    raw_image_state, raw_img = v.read()
    if not raw_image_state:
        v.release()
        break

    gray_img = cv.cvtColor(raw_img, cv.COLOR_BGR2GRAY)
    blur_img = cv.GaussianBlur(gray_img, (9,9), 0)      # Eliminates noise
    binary_img = cv.adaptiveThreshold(blur_img, 255,
                                     cv.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv.THRESH_BINARY,11,-1)
    
    blob_params = cv.SimpleBlobDetector_Params()
    blob_params.filterByArea = True
    blob_params.minArea = 150
    
    blob_detector = cv.SimpleBlobDetector(blob_params)
    cell_keypoints = blob_detector.detect(binary_img)
    
    im_with_keypoints = cv.drawKeypoints(raw_img, cell_keypoints, [])
    
    skeleton, _ = find_skeleton(binary_img)
    
    cv.imshow('Skeleton', skeleton)
    cv.imshow('original', gray_img)

    stop = cv.waitKey(100)

cv.destroyAllWindows()
