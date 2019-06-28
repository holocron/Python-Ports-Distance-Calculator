import gdal, osr 
from skimage import graph
import numpy as np 
from geopy import distance
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

def my_route(array, start, end, fully_connected=True, geometric=True):
    start, end = tuple(start), tuple(end)
#    if geometric:
#        mcp_class = graph.MCP_Geometric
#    else:
#        mcp_class = graph.MCP
#    m = mcp_class(array, fully_connected=fully_connected)
    m = graph.MCP_Connect(array, fully_connected=fully_connected)
    costs, traceback_array = m.find_costs([start], [end])
    return m.traceback(end), costs[end]

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
#    indices, weight = graph.route_through_array(costSurfaceArray, 
    indices, weight = my_route(costSurfaceArray, 
        (startIndexY,startIndexX), 
        (stopIndexY,stopIndexX),
        geometric=True,
        fully_connected=True)
    indices = np.array(indices).T
    indices = indices.astype(float)
    indices[1] = indices[1]*pixelWidth + originX
    indices[0] = indices[0]*pixelHeight + originY
    return indices

#Calculate the vincenty distance starts from the first pair of points to the last.
def calculateDistance(pathIndices):
    dist = 0

    for i in range(0,(len(pathIndices[0])-1)):
        dist += distance.distance((pathIndices[1,i], pathIndices[0,i]), (pathIndices[1,i+1], pathIndices[0,i+1])).km/1.852
#        dist += distance.vincenty((pathIndices[1,i], pathIndices[0,i]), (pathIndices[1,i+1], pathIndices[0,i+1])).km/1.852
    return dist

def routePorts(fromPort, toPort):
    print(fromPort.Port + "->" + toPort.Port)
    startCoord = (fromPort.longitude, fromPort.latitude)
    stopCoord = (toPort.longitude, toPort.latitude)

    pathIndices = createPath(mapArray,startCoord,stopCoord)
    dist = calculateDistance(pathIndices)

    print("distance is " + str(dist) + " NM")

    gmap3 = gmplot.GoogleMapPlotter((fromPort.longitude+toPort.longitude)/2, (fromPort.latitude+toPort.latitude)/2, 3)
    gmap3.plot(pathIndices[0,:], pathIndices[1,:], 'cornflowerblue', edge_width = 2.5) 
    gmap3.draw( "map-"+fromPort.Port+"-"+toPort.Port+".html") 

routePorts(ports.iloc[2377],ports.iloc[2139])
routePorts(ports.iloc[2205],ports.iloc[1000])
