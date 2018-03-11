# Created by BallBot SDP, using the Open Source Computer Vision Library
# USAGE: python ball_tracking.py
# (source ~/.profile; workon cv; python /home/pi/SDP/ball-tracking/ball-tracking.py)&

from collections import deque
import cv2
import RPi.GPIO as GPIO
import numpy as np
import imutils
import argparse
import time

ap = argparse.ArgumentParser()
ap.add_argument("-b", "--buffer", type=int, default=64,
                help="max buffer size")
args = vars(ap.parse_args())
pts = deque(maxlen=args["buffer"])
ballCount = 0
lowerColorBound = (29, 86, 6)
upperColorBound = (64, 255, 255)
# lowerColorBound = (29, 24, 6)
# upperColorBound = (72, 255, 255)  # new camera improvements
moveForward = False
ntime = 0


def setup():
    # LED setup
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    # 18 = white, 23 = green, 24 = blue
    GPIO.setup(18, GPIO.OUT)
    GPIO.setup(23, GPIO.OUT)
    GPIO.setup(24, GPIO.OUT)
    GPIO.setup(27, GPIO.OUT)  # Bryce motors
    stop()


def goForward():
    GPIO.output(18, GPIO.LOW)
    GPIO.output(23, GPIO.HIGH)
    GPIO.output(24, GPIO.LOW)
    GPIO.output(27, GPIO.HIGH)
    # print ("forward")


def goLeft():
    GPIO.output(18, GPIO.LOW)
    GPIO.output(23, GPIO.HIGH)
    GPIO.output(24, GPIO.LOW)
    GPIO.output(27, GPIO.LOW)


def goRight():
    GPIO.output(18, GPIO.LOW)
    GPIO.output(23, GPIO.LOW)
    GPIO.output(24, GPIO.LOW)
    GPIO.output(27, GPIO.HIGH)


# TODO
def moveForwardABit():
    # time_end = time.time() +tf
    # while time.time() < time_end:
    # GPIO.output(18, GPIO.LOW)
    # GPIO.output(23, GPIO.HIGH)
    # GPIO.output(24, GPIO.LOW)
    # GPIO.output(27, GPIO.HIGH)
    global ntime
    ntime = time.time()
    print("moveforwardabt", ntime)


# TODO
def roomba():
    # print("roomba")
    GPIO.output(18, GPIO.LOW)
    GPIO.output(23, GPIO.LOW)
    GPIO.output(24, GPIO.LOW)
    GPIO.output(27, GPIO.LOW)


def stop():
    GPIO.output(18, GPIO.LOW)
    GPIO.output(23, GPIO.LOW)
    GPIO.output(24, GPIO.LOW)
    GPIO.output(27, GPIO.LOW)


def shutdown():
    camera.release()
    GPIO.output(18, GPIO.LOW)
    GPIO.output(23, GPIO.LOW)
    GPIO.output(24, GPIO.LOW)
    GPIO.setup(27, GPIO.LOW)
    cv2.destroyAllWindows()


setup()
camera = cv2.VideoCapture(0)  # Capture Video from web cam...
print("Camera warming up ...")

while True:
    (captured, frame) = camera.read()
    if args.get("video") and not captured:
        break

    # resize the frame, and convert it to the HSV color space
    width = 400  # 640 might be reasonable
    frame = imutils.resize(frame, width)
    blurred = cv2.GaussianBlur(frame, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    cv2.imshow("HSV", hsv)

    # construct a mask for the color "yellowish/green", then perform
    # a series of dilations and erosions to remove any small
    # blobs left in the mask
    mask = cv2.inRange(hsv, lowerColorBound, upperColorBound)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    mask_blur = cv2.GaussianBlur(mask, (15, 15), 0)
    cv2.imshow("blurredmask", mask_blur)
    # param1=50, param2=35/15
    hough_circles = cv2.HoughCircles(mask_blur, cv2.HOUGH_GRADIENT, 1, 20, param1=50, param2=25, minRadius=0,
                                     maxRadius=0)

    # find contours in the mask and initialize the current
    # (x, y) center of the ball
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)[-2]
    center = None

    if moveForward:
        print("time!!!!!")
        goForward()
        if time.time() > ntime + .5:
            print(ntime)
            moveForward = False
            stop()

    # only proceed if at least one contour was found
    elif len(cnts) > 0 and hough_circles is not None:
        # find the largest contour in the mask, then use
        # it to compute the minimum enclosing circle and centroid
        c = max(cnts, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        M = cv2.moments(c)
        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        cv2.circle(frame, center, 5, (255, 0, 0), -1)
        # print('center: ', center, 'radius', int(radius))  # outputs coordinate to command line
        leftBound = (width / 2) - (0.15 * width)
        rightBound = (width / 2) + (0.15 * width)

        if leftBound <= center[0] <= rightBound:
            goForward()

        elif center[0] < leftBound:
            goLeft()

        else:
            goRight()

        # draw outer circle if the radius meets a minimum size
        if radius > 0.05 * width:
            # cv2.circle(image, center, radius, color, thickness)
            cv2.circle(frame, (int(x), int(y)), int(radius),
                       (0, 0, 255), 2)

        if radius >= 0.1325 * width:
            # ball is close enough to be retrieved!
            # TODO
            # ballCount = ballCount + 1  # look into this!
            # print('Ball Retrieved ' + str(ballCount))
            print("2time!!!!!")
            moveForwardABit()
            moveForward = True
    else:
        roomba()

    # update the points queue
    pts.appendleft(center)

    # loop over the set of tracked points
    for i in xrange(1, len(pts)):
        if pts[i - 1] is None or pts[i] is None:
            continue
        # otherwise, compute the thickness of the line and draw the connecting lines
        thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 2.5)
        # cv.Line(img, pt1, pt2, color, thickness=1, lineType=8, shift=0)
        cv2.line(frame, pts[i - 1], pts[i], (255, 0, 0), thickness)

    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

    # if the 'q' key is pressed, stop the loop
    if key == ord("q"):
        break

shutdown()
