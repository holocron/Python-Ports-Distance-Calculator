import gdal, osr 
from skimage.graph import route_through_array
import numpy as np 
from geopy.distance import vincenty
#import matplotlib.pyplot as plt
import pandas as pd
import gmplot

#Transforming a raster map to array datatype.
raster = gdal.Open('map.tif')
band = raster.GetRasterBand(1)
mapArray = band.ReadAsArray()

#Get geotransform information and declare some variables for later use
geotransform = raster.GetGeoTransform()
originX = geotransform[0]
originY = geotransform[3]
pixelWidth = geotransform[1] 
pixelHeight = geotransform[5]

ports = pd.read_csv('port.csv')

#transform the coordinates to the exact position in the array.
def coord2pixelOffset(x,y):
    
    xOffset = int((x - originX)/pixelWidth)
    yOffset = int((y - originY)/pixelHeight)
    return xOffset,yOffset

#create a path which travels through the cost map.
def createPath(costSurfaceArray,startCoord,stopCoord):   

    # coordinates to array index
    startCoordX = startCoord[0]
    startCoordY = startCoord[1]
    startIndexX,startIndexY = coord2pixelOffset(startCoordX,startCoordY)

    stopCoordX = stopCoord[0]
    stopCoordY = stopCoord[1]
    stopIndexX,stopIndexY = coord2pixelOffset(stopCoordX,stopCoordY)

    # create path
    indices, weight = route_through_array(costSurfaceArray, (startIndexY,startIndexX), (stopIndexY,stopIndexX),geometric=True,fully_connected=True)
    indices = np.array(indices).T
    indices = indices.astype(float)
    indices[1] = indices[1]*pixelWidth + originX
    indices[0] = indices[0]*pixelHeight + originY
    return indices

#Calculate the vincenty distance starts from the first pair of points to the last.
def calculateDistance(pathIndices):
    distance = 0

    for i in range(0,(len(pathIndices[0])-1)):
        distance += vincenty((pathIndices[1,i], pathIndices[0,i]), (pathIndices[1,i+1], pathIndices[0,i+1])).miles*0.868976
    return distance

#Test, in this case it's from CATANIA to MANTA
fromPort = ports.iloc[2205]
toPort = ports.iloc[1000]

print(fromPort.Port + "->" + toPort.Port)
startCoord = (fromPort.longitude, fromPort.latitude)
stopCoord = (toPort.longitude, toPort.latitude)

pathIndices = createPath(mapArray,startCoord,stopCoord)
distance = calculateDistance(pathIndices)

print("distance is " + distance)

gmap3 = gmplot.GoogleMapPlotter(0, 0, 1)
gmap3.scatter( pathIndices[0,:], pathIndices[1,:], '# FF0000', 
                              size = 40, marker = False )  
gmap3.plot(pathIndices[0,:], pathIndices[1,:],  
           'cornflowerblue', edge_width = 2.5) 
gmap3.draw( "map13.html" ) 