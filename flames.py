#!/usr/bin/env python

"""flames.py - Realtime Fire Effect Demo
Pete Shinners, April 3, 2001

Ok, this is a pretty intense demonstation of using
the surfarray module and numeric. It uses an 8bit
surfaces with a colormap to represent the fire. We
then go crazy on a separate Numeric array to get
realtime fire. I'll try to explain my methods here...

This flame algorithm is very popular, and you can find
it for just about all graphic libraries. The fire effect
works by placing random values on the bottom row of the
image. Then doing a simplish blur that is weighted to
move the values upward. Then slightly darken the image
so the colors get darker as they move up. The secret is
that the blur routine is "recursive" so when you blur
the 2nd row, the values there are used when you blur
the 3rd row, and all the way up.

This fire algorithm works great, but the bottom rows
are usually a bit ugly. In this demo we just render
a fire surface that has 3 extra rows at the bottom we
just don't use.

Also, the fire is rendered at half the resolution of
the full image. We then simply double the size of the
fire data before applying to the surface.

Several of these techniques are covered in the pygame
surfarray tutorial. doubling an image, and the fancy
blur is just a modified version of what is in the tutorial.

This runs at about 40fps on my celeron-400
"""


import pygame
from pygame.surfarray import *
from pygame.locals import *
#from Numeric import *
#from RandomArray import *

from numpy import *
from numpy.random import random_integers as randint

import time
from gamelib import librgb
from gamelib.vector import Vector

RES = array((8,12))
displayScale = 8

MAX = 246
RESIDUAL = 86
HSPREAD, VSPREAD = 26, 78
VARMIN, VARMAX = -2, 3

def main():
    "main function called when the script is run"
    #first we just init pygame and create some empty arrays to work with    
    pygame.init()
    screen = pygame.display.set_mode(RES*8, 0, 8)
    print screen.get_flags()
    cmap = setpalette(screen)
    flame = zeros(RES + (0,3), dtype=integer)
    print flame.shape
    scaledDisplay = zeros(RES*displayScale, dtype=integer)
    #randomflamebase(flame)    

    print "Connecting to display ..."
    #rgb = librgb.RGB("127.0.0.1")
    rgb = librgb.RGB("192.168.0.17")
    rgb.invertedX = False
    rgb.invertedY = True
    rgb.clear((0,0,0))

    flame[3:5,8:10] = randint(0, MAX, 4).reshape((2,2))
    #the mainloop is pretty simple, the work is done in these funcs
    while not pygame.event.peek((QUIT,KEYDOWN,MOUSEBUTTONDOWN)):
        modifyflamebase(flame)
        #flame[3:5,8:10] += randint(VARMIN, VARMAX, 4).reshape((2,2))
        #flame[:] = where(flame > MAX, 0, flame)

        #flame[4,8] += 32

        processflame(flame)
        #blitdouble(screen, flame, doubleflame)
        scaledDisplay = flame[:,:-3].repeat(displayScale, axis=0).repeat(displayScale, axis=1)
        blit_array(screen, scaledDisplay)
        pygame.display.flip()

        flame = clip(flame, 0, 255)
        set_plasma_buffer(rgb, cmap, flame)
        rgb.send()

        time.sleep(0.05)


def setpalette(screen):
    "here we create a numeric array for the colormap"
    gstep, bstep = 75, 150
    cmap = zeros((256, 3))
    cmap[:,0] = minimum(arange(256)*3, 255)
    cmap[gstep:,1] = cmap[:-gstep,0]
    cmap[bstep:,2] = cmap[:-bstep,0]
    screen.set_palette(cmap)
    return cmap


def randomflamebase(flame):
    "just set random values on the bottom row"
    flame[:,-1] = randint(0, MAX, flame.shape[0])
    #print flame[:,-1]


def modifyflamebase(flame):
    "slightly change the bottom row with random values"
    bottom = flame[:,-1]
    mod = randint(VARMIN, VARMAX, bottom.shape[0])
    add(bottom, mod, bottom)
    maximum(bottom, 0, bottom)
    #if values overflow, reset them to 0
    #bottom[:] = choose(greater(bottom,MAX), (bottom,0))
    bottom[:] = where(bottom > MAX, 0, bottom)


def processflame(flame):
    "this function does the real work, tough to follow"
    notbottom = flame[:,:-1]  

    #first we multiply by about 60%
    multiply(notbottom, 146, notbottom)
    right_shift(notbottom, 8, notbottom)

    #work with flipped image so math accumulates.. magic!
    flipped = flame[:,::-1]

    #all integer based blur, pulls image up too
    tmp = flipped * 20
    right_shift(tmp, 8, tmp)
    tmp2 = tmp >> 1
    add(flipped[1:,:], tmp2[:-1,:], flipped[1:,:]) # blur unten
    add(flipped[:-1,:], tmp2[1:,:], flipped[:-1,:]) # blur oben
    add(flipped[1:,1:], tmp[:-1,:-1], flipped[1:,1:]) # blur rechts unten
    add(flipped[:-1,1:], tmp[1:,:-1], flipped[:-1,1:]) # blur rechts oben

    tmp = flipped * 80
    right_shift(tmp, 8, tmp)
    add(flipped[:,1:], tmp[:,:-1]>>1, flipped[:,1:])
    add(flipped[:,2:], tmp[:,:-2], flipped[:,2:])

    #make sure no values got too hot
    minimum(notbottom, MAX, notbottom)
    #notbottom = where(notbottom > MAX, MAX, notbottom)


def blitdouble(screen, flame, doubleflame):
    "double the size of the data, and blit to screen"
    doubleflame[::2,:-2:2] = flame[:,:-4]
    doubleflame[1::2,:-2:2] = flame[:,:-4]
    doubleflame[:,1:-2:2] = doubleflame[:,:-2:2]
    blit_array(screen, doubleflame)


# ---------------------------------------------------------------
def set_plasma_buffer(rgb, cmap, plasmaBuffer):
    ySize, xSize = plasmaBuffer.shape
    for x in range(0, xSize):
        for y in range(0, ySize):
            #print x, y,  plasmaBuffer[x][y]
            rgb.setPixel(Vector(x,y), cmap[plasmaBuffer[y][x]])


if __name__ == '__main__': main()

    