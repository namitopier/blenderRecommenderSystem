bl_info = {
    "name": "Blender Recommender System",
    "author": "Pier Luigi Nakai Ricchetti",
    "version": (1, 0),
    "blender": (3, 2, 2),
    "location": "View3D > Sidebar > Blender Recommender",
    "description": "Logs user actions",
    "warning": "",
    "wiki_url": "",
    "category": "Blender Recommender",
}

import bpy, bmesh
from bpy.props import IntProperty, FloatProperty
import mathutils
import math
import re
import os
import numpy as np
import json
import copy

useLogger = False
logCache = []
userProfileCache = []
numberOfOp = 0
globalLastOp = None
tutorialMode = False
tutFileName = ""
ignoreLastOp = False
userFeedback = ""

# ======================================================================================================================= #
# ============================================= Cache Related =========================================================== #
# ======================================================================================================================= #

cacheDict = {
    "allObjects": {},
    "allModifiers": [],
    "tempValue": None
}

def saveObjectsOnCache(objsDict):
    # Saves a list of all the objects names in the scene in the cache

    cacheDict["allObjects"] = objsDict

def saveModifiersOnCache(modifiersList):
    # Saves a list of all the modifiers names of the selected object in the cache
    
    cacheDict["allModifiers"] = modifiersList

def saveObjectTransformOnCache(objName, scale = None, location = None, rotation = None, objProps = None):
    # Saves transform properties of an object

    if objName not in cacheDict["allObjects"]:
        cacheDict["allObjects"][objName] = objProps

    else:   
        cacheDict["allObjects"][objName]["scale"] = scale
        cacheDict["allObjects"][objName]["location"] = location
        cacheDict["allObjects"][objName]["rotation"] = rotation

def saveObjectVerticesOnCache (vertDict):
    # Saves all the vertices of an object in the cache

    if (bpy.context.active_object):
        cacheDict["allObjects"][bpy.context.active_object.name]["vertices"] = vertDict

    else:
        print("No active object to save the vertices on the cache")

def saveObjectFacesOnCache (facesDict):
    # Saves all the faces of an object in the cache

    if (bpy.context.active_object):
        cacheDict["allObjects"][bpy.context.active_object.name]["faces"] = facesDict

    else:
        print("No active object to save the faces on the cache")

def getObjectsOnCache():
    return cacheDict["allObjects"]

def getModifiersOnCache():
    return cacheDict["allModifiers"]

# ======================================================================================================================= #
# ============================================ Util Functions =========================================================== #
# ======================================================================================================================= #
    
def getAllObjects(firstCall = False):
    # Gets all the objects in the scene.
    # If it is a new object, firstcall == True and thus all its vertices must be considered

    objsDict = {}
    changedMode = False

    if firstCall:
        activeObj = bpy.context.view_layer.objects.active

        if activeObj and activeObj.mode == "OBJECT" and activeObj.type == 'MESH':
            bpy.ops.object.editmode_toggle()
            changedMode = True

    objs = bpy.context.scene.objects
    for obj in objs:
        objsDict[obj.name] = {  "scale": list(obj.scale),
                                "location": list(obj.location),
                                "rotation": list(obj.rotation_euler),
                                "vertices": {} if not firstCall or not activeObj else getAllVerticesOfObject(),
                                "faces": {} if not firstCall or not activeObj else getAllFacesOfObject(),
                                "isSmooth": True if (obj.type == "MESH" and any(face.use_smooth for face in obj.data.polygons)) else False}

    if changedMode:
        bpy.ops.object.editmode_toggle()

    return objsDict

def getAllModifiers():
    # Gets all the modifiers of all the objects in the scene. Uses the getAllObjects() function

    objsList = list(getAllObjects().keys())
    modifiersList = []
    editMode = False

    if bpy.context.object != None:
        prevSelectedObj = bpy.context.object.name 

        if(bpy.context.object.mode == 'EDIT'):
            editMode = True
            bpy.ops.object.mode_set(mode = "OBJECT")
    
    else:
        prevSelectedObj = None

    for objectName in objsList:

        if objectName in bpy.data.objects:
            # Deselect all currently selected objects
            bpy.ops.object.select_all(action='DESELECT')

            # Select the object
            bpy.data.objects[objectName].select_set(True)

            bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]

        else:
            print(f"Object '{objectName}' not found")

        selected_object = bpy.context.view_layer.objects.active

        if selected_object is not None:
            # Get all modifiers of the selected object
            objModifiers = [modifier.name for modifier in selected_object.modifiers]
            
            modifiersList += objModifiers
    
    if prevSelectedObj is not None:

        # Deselect all currently selected objects
        bpy.ops.object.select_all(action='DESELECT')

        # Select the object and sets it to be the active one
        bpy.data.objects[prevSelectedObj].select_set(True)
        bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]

        # If it was in edit mode before, set again it
        if(editMode):
            bpy.ops.object.mode_set(mode = "EDIT")

    return modifiersList

def getAllVerticesOfObject():
    # Gets all Vertices of the active object. Returns dictionary in the format:
    # {vertex index: xyz coordinates, .....}

    activeObj = bpy.context.active_object

    if activeObj.type == 'MESH':
        
        vertices_dict = {}

        bm = bmesh.from_edit_mesh(activeObj.data)

        for vert in bm.verts:
            vertices_dict[vert.index] = list(vert.co)
        return vertices_dict

    else:
        print("Object is not a mesh.")
        return None
    
def getAllFacesOfObject():
    # Gets all faces of the active object. Returns dictionary in the format:
    # {face index: center median, .....}

    activeObj = bpy.context.active_object

    if activeObj.type == 'MESH':
        
        faces_dict = {}

        bm = bmesh.from_edit_mesh(activeObj.data)

        for face in bm.faces:
            faces_dict[face.index] = list(face.calc_center_median())
        return faces_dict

    else:
        print("Object is not a mesh.")
        return None

def highlightVertices(objectName, firstPos, secondPos, tolerance = 0.1):
    # objectName = Name of the target object
    # firstPos = dictionary containing all the selected vertices position before the operation
    # secondPos = dictionary containing all the selected vertices position after the operation
    # This function creates spheres to indicate the indices user should be moving
    
    highlightType = "normal"
    firstLen = len(list(firstPos.values()))
    secondLen = len(list(secondPos.values()))
    keys = list(firstPos.keys())

    if firstLen < secondLen:
        # Means addition of new vertices
        keys = list(secondPos.keys())
        highlightType = "add"
    
    elif firstLen > secondLen:
        # Means deletion of vertices
        highlightType = "delete"

    # Setting the objectName as active
    obj = bpy.data.objects[objectName]
    bpy.context.view_layer.objects.active = obj
    objLocation = list(obj.location)
    activeObj = bpy.context.view_layer.objects.active

    # Getting the mode (OBJECT or EDIT)
    mode = activeObj.mode

    if mode == "EDIT":
        bpy.ops.object.mode_set(mode='OBJECT')

    if highlightType == "normal":
        for i, key in enumerate(keys):
                initialName = str(key) + ": Initial Pos"
                finalName = str(key) + ": Final Pos"
                initialLoc = [x + y for x, y in zip(firstPos[key], objLocation)]
                finalLoc = [x + y for x, y in zip(secondPos[key], objLocation)]

                bpy.ops.object.empty_add(type='SPHERE', radius=0.03, align='WORLD', location=initialLoc, scale=(1, 1, 1))
                bpy.context.object.show_name = True
                bpy.context.object.show_in_front = True
                # bpy.context.object.hide_select = True
                bpy.context.object.name = initialName
                
                bpy.ops.object.empty_add(type='SPHERE', radius=0.03, align='WORLD', location=finalLoc, scale=(1, 1, 1))
                bpy.context.object.show_name = True
                bpy.context.object.show_in_front = True
                # bpy.context.object.hide_select = True
                bpy.context.object.name = finalName
        
    elif highlightType in ["add", "delete"]:
        # The vertices keys change, so have to compare them by value rather than by key

        differences = findVertsDiff(list(firstPos.values()), list(secondPos.values()), tolerance)
        suffix = ": Add new vert" if highlightType == "add" else ": Remove this vert"

        for i, difference in enumerate(differences):

            name = str(i) + suffix
            location = [x + y for x, y in zip(difference, objLocation)]

            bpy.ops.object.empty_add(type='SPHERE', radius=0.03, align='WORLD', location=location, scale=(1, 1, 1))
            bpy.context.object.show_name = True
            bpy.context.object.show_in_front = True
            bpy.context.object.name = name

    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[objectName].select_set(True)

    bpy.context.view_layer.objects.active = bpy.data.objects[objectName]
    if mode == "EDIT":
        bpy.ops.object.mode_set(mode='EDIT')

    global ignoreLastOp
    ignoreLastOp = True
    return

def clearHighlights():

    suffix = ["Initial Pos", "Final Pos", "Add new vert", "Remove this vert"]

    for obj in bpy.data.objects:
    # Check if the object's name ends with the specified suffix
        if obj.name.endswith(suffix[0]) or obj.name.endswith(suffix[1]) or obj.name.endswith(suffix[2]) or obj.name.endswith(suffix[3]):
            # Delete the object
            bpy.data.objects.remove(obj, do_unlink=True)

    return

def withinMargin(val1, val2, margin):
    # Checks if value 1 is in between margin defined by value 2

    return -np.abs(val2)*margin <= np.abs(val1 -val2) <= np.abs(val2)*margin

def update_user_feedback(new_feedback):
    "Updates what s shown for the user in the UI"

    bpy.context.scene.user_feedback = new_feedback

    # Redraw the UI to update with new info
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def split_text(text, width=40):
    """Splits the text into chunks of size width"""
    words = text.split(' ')
    lines = []
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 <= width:
            if current_line:
                current_line += " "
            current_line += word
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines

# ======================================================================================================================= #
# ============================================= Mesh Processor ========================================================== #
# ======================================================================================================================= #

def findVertsDiff(beforeList, afterList, margin):
    # Given list1 and list2 and a margin (% / 100), returns the differences.
    # E.g., if list1 contains vertices that are not included in list2: function returns these vertices.
    # If len(list1) == len(list2), list1 is used as the base of comparison, which means that the return
    # list contains vertices from list1 that are different than list2
    
    differences = []
    compareFrom = beforeList
    compareTo = afterList
    margin = 0.1

    if len(afterList) > len(beforeList):
        compareFrom = afterList
        compareTo = beforeList

    print("$$$$$$$$$$$$$$$$$$$$$$$$  From To: ", compareFrom, compareTo)

    for elem1 in compareFrom:
        found = False
        for elem2 in compareTo:
            if all(withinMargin(val1, val2, margin) for val1, val2 in zip(elem1, elem2)):
                found = True
                break
        if not found:
            differences.append(elem1)

    print("$$$$$$$$$$$$$$$$$$$$$$$$  DIFERENCAS: ", differences)
    return differences

def checkMeshSimilarity (meshDict1, meshDict2, margin):
    # Given 2 dictionaries containing information about vertices and faces of the 2 meshes,
    # (and considering that the number of vertices and faces are already equal for both),
    # compare their location considering the given margin.

    vert1 = np.array( list(meshDict1["vertices"].values()) )
    vert2 = list(meshDict2["vertices"].values())
    faces1 = np.array( list(meshDict1["faces"].values()) )
    faces2 = list(meshDict2["faces"].values())

    if len(vert1) != len(vert2) or len(faces1) != len(faces2):
        return False

    def checkCorrespondence (dict1, dict2, i):
        # Internal function that receives 2 dictionaries containing vertices/faces
        # and tries to find a correspondence between all entries of dict1 with all of dict2
        # considering the margin selected.
        # Once found, this entry is removed from dict2 since it is a 1-1 correspondence, 
        # increasing performance.
        # RETURNS: -1 if no correspondence found (so the mesh is wrong) or modified dict2 if found
        # correspondence (it deletes the found correspondent) .

        foundI = -1
        possibleIndices = []
        possibleValues = []
        precision = 4 # Number of decimals after point

        for j in range (len(dict2)):
            if all(np.abs(np.round(dict1[i][k], precision) - np.round(dict2[j][k], precision)) <= margin * abs(dict1[i][k]) for k in range(3)):
                    # foundI = j
                    # break  # Stop searching for this vertex in dict2 once a match is found

                    possibleIndices.append(j)
                    possibleValues.append( np.linalg.norm( np.array(dict1[i]) - np.array(dict2[j])) ) # Distance between the 2 points

        # if foundI >= 0:
        if len(possibleIndices) > 0:
            foundI = possibleIndices[np.argmin(possibleValues)]
            del dict2[foundI]
            return dict2
            
        else:
            return -1
            
    found = True

    # First test vertices correspondence:
    for i in range (len(vert1)):
        checked = checkCorrespondence(vert1, vert2, i)
        
        if checked == -1:
            found = False
            break
        
        else:
            vert2 = checked

    # If fully correspondent, check faces
    if found:
        for i in range (len(faces1)):
            checked = checkCorrespondence(faces1, faces2, i)
            if checked == -1:
                found = False
                break
            
            else:
                faces2 = checked

        
    print("***************************************")
    print("Meshes are EQUAL" if found else "Meshes are DIFFERENT")
    print("***************************************")

    return found

# ======================================================================================================================= #
# ========================================= Operations Processor ======================================================== #
# ======================================================================================================================= #

def formatOperation2(operator, isSame):
    '''
    Receives an operator (= bpy.context.active_operator) and returns it on the correct format (translated) to be used on the tutorial.
    It also receives a string in the "isSame" field related to an operation/action performed. Depending on its structure, different
    logic is used to process it.

    - Returns: translated operation always in the format: [name of operation, dictionary with its properties, name of target object].

    - Note: if it is not an operation but a user action, the dictionary will always follow the structure:  {group: property,
                                                                                                            subgroup: property,
                                                                                                            propIndex: property,
                                                                                                            other1: property,
                                                                                                            ...,
                                                                                                            otherN: property}
    
    '''

    activeObj = bpy.context.view_layer.objects.active             
    mode = None if activeObj == None else activeObj.mode 
    
    if isSame[:7] == "bpy.ops":
        # The structure of bpy.ops is different than the others -> means it is actually an operation

        result = ""

        # Removing all the characters before the first parenthesis
        processed = isSame[isSame.index("(") + 1:-1]

        # Some operations do not have properties
        if len(processed) == 0:
            result = {}

        else:
            # Picking all the parts divided by commas
            parts = processed.split(",")

            for part in parts:
                # Must replace all "=" to ":" and also include quotes so it is in the format of dictionary
                splitted = part.split("=")

                if (len(splitted) > 1):
                    splitted[0] = '"' + splitted[0].strip(" ") + '"'
                    splitted = splitted[0] + ":" + splitted[1] + ","
                else:
                    splitted = splitted[0]  + ","

                result = result + splitted

            # Transforming into a dictionary
            result = eval("{" + result + "}")

        if (mode and mode == "EDIT" and activeObj.type == "MESH"):

            allVertices = getAllVerticesOfObject()
            allFaces = getAllFacesOfObject()
            objsDict = getObjectsOnCache()
            oldVertices = objsDict[activeObj.name]["vertices"]
            oldFaces = objsDict[activeObj.name]["faces"]
            vertDiff = []
            facesDiff = []

            oldVertNumber = len(oldVertices.keys())
            oldFacesNumber = len(oldFaces.keys())
            newVertNumber = len(allVertices.keys())
            newFacesNumber = len(allFaces.keys())

            if ( oldVertNumber != newVertNumber or oldFacesNumber != newFacesNumber ):
                # Means it is an operation that added/removed vertices/faces. In this case, save which vertices/faces have been created/deleted

                if (oldVertNumber < newVertNumber or oldFacesNumber < newFacesNumber):
                    # Means created more vertices/faces

                    for key in allVertices.keys():
                        if (key not in oldVertices): vertDiff.append(key)
                    
                    result["newVertices"] = vertDiff

                    for key in allFaces.keys():
                        if (key not in oldFaces): facesDiff.append(key)
                    
                    result["newFaces"] = facesDiff

                else:
                    # Means deleted vertices

                    for key in oldVertices.keys():
                        if (key not in allVertices): vertDiff.append(key)
                    
                    result["deletedVertices"] = vertDiff

                    for key in oldFaces.keys():
                        if (key not in allFaces): facesDiff.append(key)
                    
                    result["deletedFaces"] = facesDiff
                
                saveObjectVerticesOnCache(allVertices)
                saveObjectFacesOnCache(allFaces)

            else:
                # Means it is an operation that just modified vertices

                for key in allVertices.keys():
                    if (allVertices[key] != oldVertices[key]): vertDiff.append(key)

                if (len(vertDiff) != 0):
                    # Means modification occurred

                    saveObjectVerticesOnCache(allVertices)
                    saveObjectFacesOnCache(allFaces)
                    result["selectedVertices"] = vertDiff

            # Saving all vertices in the result
            result["vertices"] = allVertices
            result["faces"] = allFaces
            result["editMode"] = True


        elif (mode and mode == "OBJECT"):
            # Save new transform properties of objetcs if modified
            cacheObjs = getObjectsOnCache()

            if (activeObj.name in cacheObjs):
                # Means it is an update

                selectedObjs = bpy.context.selected_objects

                for i, obj in enumerate(selectedObjs):
                    # There can be multiple objects being selected

                    if obj.name in cacheObjs:
                        # There are some operations that create new objects from edit mode (like separate)

                        oldObj = cacheObjs[obj.name]
                        objProps = {"scale" : list(obj.scale),
                                    "location" : list(obj.location),
                                    "rotation" : list(obj.rotation_euler)}
                        
                        if(obj.name == activeObj.name):
                            # If active, include new properties in the translated operation

                            for key in objProps.keys():
                                if (oldObj[key] != objProps[key]):
                                    # Add into dictionary result the modified property
                                    result["new" + key] = objProps[key]
                        
                        # Update cache with new values
                        saveObjectTransformOnCache(obj.name, objProps["scale"], objProps["location"], objProps["rotation"])
                    
                    else:
                        bpy.context.view_layer.objects.active = obj
                        # bpy.ops.object.select_all(action='DESELECT')
                        bpy.ops.object.editmode_toggle()

                        objProps = {"scale" : list(obj.scale),
                                    "location" : list(obj.location),
                                    "rotation" : list(obj.rotation_euler),
                                    "vertices": getAllVerticesOfObject(),
                                    "faces": getAllFacesOfObject(),
                                    "isSmooth": True if (obj.type == "MESH" and any(face.use_smooth for face in obj.data.polygons)) else False}
                        
                        bpy.ops.object.editmode_toggle()

                        saveObjectTransformOnCache(obj.name, objProps=objProps)

                if (len(selectedObjs) > 1):
                    result["selectedObjs"] = [obj.name for obj in selectedObjs]


            else:
                # Means it is adding a new one
                cacheObjs[activeObj.name] = getAllObjects(firstCall=True)[activeObj.name]
                saveObjectsOnCache(cacheObjs)
            
            result["editMode"] = False

        if activeObj == None:
            # Means its probably a deletion, so have to include manually "editMode"
            result["editMode"] = False

        translated = [operator.name, result, None if activeObj == None else activeObj.name]

    else:
        # In this case, it is considering everything else that is not an operation (bpy.ops) but still is an user action

        activeObj = bpy.context.view_layer.objects.active

        possindices = [index for index, char in enumerate(isSame) if char == '"']
        endIndices = []
        processed = isSame
        groupIndex = 0
        baseIndex = 0
        translated = [""]
        
        # List of names, groups etc and operation "address"
        groupsList = [["group", ""], ["subgroup", ""], ["propIndex", ""]]

        for index in possindices:
            #if isSame[index-1] != "[" or ord(isSame[index-1]) != 92:
            if ord(isSame[index-1]) == 92:
                foundAnother = False
                count = 0
                i = 1
                
                while not foundAnother:
                    if (ord(isSame[index-i]) == 92):
                        count+=1
                        i+=1
                        
                    else:
                        foundAnother = True
                        
                if (count%2 == 0):
                    # If even, it is the end of string

                    endIndices.append(index)
            
            elif index != ( len(isSame)-1 ) and isSame[index+1] == "]":
                endIndices.append(index)

        if len(endIndices) != 0:
            # Means that it requires special treatment for the "["something"]"
            for i, char in enumerate(isSame):
                if (char == "[" and i > baseIndex):
                    # At every first occurrence of [, means the start of a string

                    # The first occ. of "[" may be related to a number, which means that the endIndices won't be considering:
                    if (isSame[i + 1] != '"'):
                        # Means it is a number
                        
                        closeIndex = isSame[i+1:].index("]")
                        groupName = isSame[i+1:][:closeIndex]
                        evalGroupName = eval(groupName)

                    else:
                        # Means it is a String

                        closeIndex = endIndices[0]+1
                        groupName = isSame[i+1 : closeIndex]
                        evalGroupName = eval(groupName)
                        baseIndex = closeIndex
                        del endIndices[0]

                    if groupIndex <= 2:
                            groupsList[groupIndex][1] = evalGroupName

                    else:
                        groupsList.append(["other"+str(groupIndex-2), evalGroupName])

                    processed = processed.replace("[" + groupName + "]", "")

                    groupIndex += 1
        
        processed = processed.split(" = ")

        # Get the value of the property
        if type(eval(processed[1]) not in [int, float, str]):
            value = str(processed[1])
        else:
            value = eval(processed[1])
        
        # Get the address of the operation
        processed = processed[0].split(".")

        for addr in processed[:-1]:
            translated[0] += " " + addr

        groupsList = groupsList[0:groupIndex]
        groupsList.append([processed[-1], value])
        translated.append(dict(groupsList))
        translated.append(None if not activeObj else activeObj.name)
        translated[1]["editMode"] = True if mode == 'EDIT' else False

    return translated

def isSameOperation(newOp, mouse_x, mouse_y):
    '''
    Receives current operation (= bpy.context.active_operator) - and compare it to the last performed to return if they are the same operation.
    Returns a bool if repeated operation and the operation itself if a new one
    '''

    operations = getPerformedOperations(mouse_x, mouse_y)
    global ignoreLastOp
    global numberOfOp

    if ignoreLastOp:
        numberOfOp = len(operations)
        ignoreLastOp = False
        return True
    
    if (len(operations) != 0):
        # It happens sometimes that the operations list comes empty
    
        lastOp = operations[-1]
        global globalLastOp

        if (len(operations) - numberOfOp > 1):
            for operation in operations[-(len(operations) - numberOfOp):]:
                if (operation[:3] == "bpy" and operation[:34] != 'bpy.data.window_managers["WinMan"]'):
                    # Pick the last bpy occurence, ignore if window change so it keeps the operation itself
                    lastOp = operation
                    globalLastOp = lastOp
        
        if len(operations) > numberOfOp and lastOp[:3] == "bpy":
            # Must consider only strings that start with "bpy" otherwise it is not a valid user action
        
            numberOfOp = len(operations)

            if (newOp == None):
                # Operations like undo (ctrl z) or other specific operations are recognized as none
                return True
            
            # If valid operation, return the string of the last operation performed
            return lastOp

        else:
            return True
        
    else:
        return True
    
def getPerformedOperations(mouse_x = 0, mouse_y = 0):
    '''
    Gets all the performed operations in the current session from the INFO window in Blender.
    If just one window or the INFO window not present in the UI, use context override to 
    replace or create the INFO window, copy all info listed there and then change back to
    the original config.

    - Returns a list of operations
    
    '''

    hoveredArea = None

    for currentArea in bpy.context.window_manager.windows[0].screen.areas:
        if ( mouse_x > currentArea.x and mouse_x < (currentArea.x + currentArea.width) and mouse_y > currentArea.y and mouse_y < (currentArea.y + currentArea.height) ):
            # Means that mouse is inside this area
            hoveredArea = currentArea.type
    
    index = 1 if bpy.context.window_manager.windows[0].screen.areas[0].type == hoveredArea else 0


    if (len(bpy.context.window_manager.windows[0].screen.areas) == 1):
        # Need to create a new one in case only one are in the window:

        window = bpy.context.window_manager.windows[0]
        area = window.screen.areas[0]

        override = {'window': window, 'screen': window.screen, 'area': window.screen.areas[0]}

        with bpy.context.temp_override(**override):
            bpy.ops.screen.area_split(direction='HORIZONTAL', factor=0.001)


    window = bpy.context.window_manager.windows[0]
    area = window.screen.areas[index]
    area_type = area.type
    area.type = "INFO"

    override = {'window': window, 'screen': window.screen, 'area': window.screen.areas[index]}

    with bpy.context.temp_override(**override):
        bpy.ops.info.select_all(action='SELECT')
        bpy.ops.info.report_copy()

    area.type = area_type

    clipboard = bpy.context.window_manager.clipboard

    return clipboard.split("\n")[:-1] # Has to exclude the last one since it will be "" 

def getFilteredOp (translatedOp, additionalInfo = {"tolerance": 10}):
    '''
    Filters automatically the important values to track + additional values decided by the user
    By default, it will consider all the first 2 props of all nested dicts of the properties.

    - Returns: Filtered translated operation with fixed properties to track + first 2 props of any operation + additional dictionary: 
    [name of op, filtered dictionary + first 2 props, target object, additional Info dict]
    
    '''


    fixedValues = [ "newVertices",
                    "newFaces",
                    "deletedVertices",
                    "deletedFaces",
                    "selectedVertices",
                    "vertices",
                    "faces",
                    "editMode",
                    "newscale",
                    "newlocation",
                    "newrotation",
                    "selectedObjs",
                    "group",
                    "subgroup",
                    "propIndex"]
    
    additionalProps = [] if "additionalProps" not in additionalInfo else additionalInfo["additionalProps"]
    ignoreProps = [] if "ignoreProps" not in additionalInfo else additionalInfo["ignoreProps"]

    fixedValues += additionalProps
    fixedValues = [prop for prop in fixedValues if prop not in ignoreProps]
    props = translatedOp[1]
    filtered = {}
    included = 0

    for prop in list(props.keys()):
        
        if included != 2:
            if type(props[prop]) == dict and prop not in fixedValues:
                # Means nested dict
                for nestedProp in list(props[prop].keys())[:2]:
                    filtered[nestedProp] = props[prop][nestedProp]
                
                included += 1

            elif prop not in fixedValues:
                filtered[prop] = props[prop]
                included += 1

        if prop in fixedValues:
            filtered[prop] = props[prop]

    return [translatedOp[0], filtered, translatedOp[2], additionalInfo]

# ======================================================================================================================= #
# ================================================ Classes ============================================================== #
# ======================================================================================================================= #

class Tutorial:

    count = 0

    def __init__(self, tutorialName = None):
        if tutorialName is not None:
            self.loadTutorialSteps(tutorialName)

        else:
            self.tutorialSteps = []
        
        self.state = 0 # Var to track the state on the tutorial. 0 - N where N is the total number of steps -1. If state == N, tutorial ended.

    def addTutorialStep(self, step):
        # Receives a list containing [operator.name, properties]

        filteredOp = getFilteredOp(step)
        self.tutorialSteps.append(filteredOp)
        self.count = 0
        print("\n============================= LIST OF OPS")
        for op in self.tutorialSteps:
            print("")
            print(self.count, " - ", op)
            self.count += 1

        global logCache
        logCache = self.tutorialSteps

    def loadTutorialSteps(self, tutorialName):
        # Receives a list with all the tutorial steps: [[operator.name 1, properties 1], [operator.name 2, properties 2] ...]
        file_path = bpy.path.abspath('//'+tutorialName)

        # Open the file in read mode
        with open(file_path, 'r') as file:
            # Read each line using a loop
            for line in file:
                self.tutorialSteps.append( eval(line.strip()) )

    def getNextStep(self):
        nextStep = self.tutorialSteps[self.state]
        return nextStep

    def recursiveValidate(self, structure, structureCompare, structureType, tolerance):
        # Given a structure (list, dictionary, int, str ...) and the corresponding structure to compare, recursively compare its float values 
        # considering the tolerance (0,1 = 10%) and returns False if there is a difference and True otherwise. 
        if structureType == dict:
            for key in list(structure.keys()):
                value = structure[key]
                if type(value) != float and type(value) != int:
                    if self.recursiveValidate(value, structureCompare[key], type(value), tolerance) == False:
                        return False
                elif type(value) == float:
                    valueCompare = abs(structureCompare[key])
                    if not (value == valueCompare or (abs(value) >= valueCompare*(1-tolerance) and abs(value) <= valueCompare*(1+tolerance))):
                        return False
                    
        elif structureType == list or structureType == tuple:
            for i, value in enumerate(structure):
                if type(value) != float and type(value) != int:
                    if self.recursiveValidate(value, structureCompare[i], type(value), tolerance) == False:
                        return False
                elif type(value) == float:
                    # print("======= GOT VALUE   : ", value)
                    valueCompare = abs(structureCompare[i])
                    # print("======= COMPARE WITH: ", structureCompare[i], value == valueCompare or (value >= valueCompare*(1-tolerance) and value <= valueCompare*(1+tolerance)))
                    if not (value == valueCompare or (abs(value) >= valueCompare*(1-tolerance) and abs(value) <= valueCompare*(1+tolerance))):
                        return False       
        return True
    
    def validateFinalValues(self, tolerance, expectedMeshes, actualMesh, lastStep, objName):
        # tolerance: Percentage/100 of tolerance for vertices location 
        # expectedMeshes: list of dictionaries of all the vertices and their expected locations of the next 3 operations
        # Returns a list of incorrect indices and [] if all correct
        global userFeedback

        expFacesLen = len(list(expectedMeshes[0]["faces"].values()))
        actFacesLen = len(list(actualMesh["faces"].values()))
        expVertsLen = len(list(expectedMeshes[0]["vertices"].values()))
        actVertsLen = len(list(actualMesh["vertices"].values()))

        # expectedLen = len(list(expectedVerts.values()))
        # actualLen = len(list(actualVerts.values()))
        lastVertsLen = 0
        lastFacesLen = 0

        if "vertices" in lastStep and type(lastStep["vertices"]) == dict:
            lastVertsLen = len(list(lastStep["vertices"].values()))
            lastFacesLen = len(list(lastStep["faces"].values()))


        # If new vertices or deleted vertices, no need to validate the values, they will be already wrong
        if expFacesLen != actFacesLen or expVertsLen != actVertsLen:
            # Checking which are the vertices/faces that have been created/deleted
            # First check if the mesh configuration is as it was meant to be to go to next operation

            # clearHighlights()
            if lastVertsLen != actVertsLen and lastVertsLen != 0:
                # Means the mesh is not in the correct configuration to follow to next step

                if (lastVertsLen > actVertsLen):
                    # Means that some vertices are missing
                    
                    missing = lastVertsLen-actVertsLen

                    if (missing == 1):
                        print("ERROR FOUND! There is 1 vertex missing in this object. Be sure to add it at the correct location so the tutorial can continue!")
                        update_user_feedback("ERROR FOUND! There is 1 vertex missing in this object. Be sure to add it at the correct location so the tutorial can continue!")
                    else:
                        print("ERROR FOUND! There are %i vertices missing in this object. Be sure to add them at the correct location so the tutorial can continue!" %(missing))
                        update_user_feedback("ERROR FOUND! There are " + str(missing) + " vertices missing in this object. Be sure to add them at the correct location so the tutorial can continue!")
                    
                else:
                    # Means that there are additional vertices

                    additional = actVertsLen - lastVertsLen

                    if (additional == 1):
                        print("ERROR FOUND! There is 1 additional vertex in this object. Be sure to delete the correct one so the tutorial can continue!")
                        update_user_feedback("ERROR FOUND! There is 1 additional vertex in this object. Be sure to delete the correct one so the tutorial can continue!")
                    else:
                        print("ERROR FOUND! There are %i additional vertices in this object. Be sure to delete the corect ones so the tutorial can continue!" %(additional))
                        update_user_feedback("ERROR FOUND! There are " + str(additional) + " additional vertices in this object. Be sure to delete the corect ones so the tutorial can continue!")

            elif lastFacesLen != actFacesLen and lastFacesLen != 0:
                # Means the mesh is not in the correct configuration to follow to next step

                if (lastFacesLen > actFacesLen):
                    # Means that some faces are missing
                    
                    missing = lastFacesLen-actFacesLen

                    if (missing == 1):
                        print("ERROR FOUND! There is 1 face missing in this object. Be sure to add it at the correct location so the tutorial can continue!")
                        update_user_feedback("ERROR FOUND! There is 1 face missing in this object. Be sure to add it at the correct location so the tutorial can continue!")
                    else:
                        print("ERROR FOUND! There are %i faces missing in this object. Be sure to add them at the correct location so the tutorial can continue!" %(missing))
                        update_user_feedback("ERROR FOUND! There are "+ str(missing) +" faces missing in this object. Be sure to add them at the correct location so the tutorial can continue!")
                    
                else:
                    # Means that there are additional faces

                    additional = actFacesLen - lastFacesLen

                    if (additional == 1):
                        print("ERROR FOUND! There is 1 additional face in this object. Be sure to delete the correct one so the tutorial can continue!")
                        update_user_feedback("ERROR FOUND! There is 1 additional face in this object. Be sure to delete the correct one so the tutorial can continue!")
                    else:
                        print("ERROR FOUND! There are %i additional faces in this object. Be sure to delete the corect ones so the tutorial can continue!" %(additional))
                        update_user_feedback("ERROR FOUND! There are "+ str(additional) +" additional faces in this object. Be sure to delete the corect ones so the tutorial can continue!")

            else:
                # Means the mesh is ready fot the next step, so now compare the actual vertices to the expected for the next op
                
                if (expVertsLen > actVertsLen):
                    # Means that some vertices are missing
                    
                    missing = expVertsLen-actVertsLen

                    if (missing == 1):
                        print("There is still 1 vertex missing in this object in order to conclude this step! Follow the tutorial to add it at the correct location!")
                        update_user_feedback("There is still 1 vertex missing in this object in order to conclude this step! Follow the tutorial to add it at the correct location!")
                    else:
                        print("There are %i vertices missing in this object in order to conclude this step! Follow the tutorial to add them at the correct location!" %(missing))
                        update_user_feedback("There are "+ str(missing) +" vertices missing in this object in order to conclude this step! Follow the tutorial to add them at the correct location!")
                    
                elif (expVertsLen < actVertsLen):
                    # Means that there are additional vertices

                    additional = actVertsLen - expVertsLen

                    if (additional == 1):
                        print("There is still 1 additional vertex in this object in order to conclude this step! Follow the tutorial to delete it at the correct location!")
                        update_user_feedback("There is still 1 additional vertex in this object in order to conclude this step! Follow the tutorial to delete it at the correct location!")
                    else:
                        print("There are %i additional vertices in this object in order to conclude this step!. Follow the tutorial to delete them at the correct location!" %(additional))
                        update_user_feedback("There are "+ str(additional) +" additional vertices in this object in order to conclude this step!. Follow the tutorial to delete them at the correct location!")

                if (expFacesLen > actFacesLen):
                    # Means that some faces are missing
                    
                    missing = expFacesLen-actFacesLen

                    if (missing == 1):
                        print("There is still 1 face missing in this object in order to conclude this step! Follow the tutorial to add it at the correct location!")
                        update_user_feedback("There is still 1 face missing in this object in order to conclude this step! Follow the tutorial to add it at the correct location!")
                    else:
                        print("There are %i faces missing in this object in order to conclude this step! Follow the tutorial to add them at the correct location!" %(missing))
                        update_user_feedback("There are "+ str(missing) +" faces missing in this object in order to conclude this step! Follow the tutorial to add them at the correct location!")
                    
                elif (expFacesLen < actFacesLen):
                    # Means that there are additional faces

                    additional = actFacesLen - expFacesLen

                    if (additional == 1):
                        print("There is still 1 additional face in this object in order to conclude this step! Follow the tutorial to delete it at the correct location!")
                        update_user_feedback("There is still 1 additional face in this object in order to conclude this step! Follow the tutorial to delete it at the correct location!")
                    else:
                        print("There are %i additional faces in this object in order to conclude this step!. Follow the tutorial to delete them at the correct location!" %(additional))
                        update_user_feedback("There are "+ str(additional) +" additional faces in this object in order to conclude this step!. Follow the tutorial to delete them at the correct location!")

            return False, -1

        # Indicates if the mesh is equal to any of the next 3 operations
        same = False
        # Indicates which mesh is the equivalent (-1 if none)
        meshIndex = -1
        for i, mesh in enumerate(expectedMeshes):
            if(checkMeshSimilarity(mesh, actualMesh, 0.2)):
                same = True
                meshIndex = i
                break

        if not same:
            print("There are some vertices/faces wrong located in this object in order to conclude this step! Follow the tutorial to move them to the correct location!")
            update_user_feedback("The current mesh topology is different than the expected for the conclusion of this step. Fix it in order to conclude this step! Follow the tutorial to shape it correctly!")

        return same, meshIndex


    def validateStep(self, step):
        # Validates the step passed [operator.name, properties] with the current state of the tutorial

        activeObj = bpy.context.view_layer.objects.active
        editMode = False

        if (activeObj and activeObj.mode == "EDIT"):
            editMode = True

        # Get the current step
        currentStep = self.tutorialSteps[self.state]

        # Get the filtered operation considering the additional props tracked (last element of saved step)
        filteredOp = getFilteredOp(step, currentStep[-1])

        print("=========== PERFORMED VS EXPECTED = ", filteredOp[0], self.tutorialSteps[self.state][0])

        # Checking first if the mode is the same:
        if ("editMode" not in currentStep[1] and editMode == "OBJECT") or ("editMode" in currentStep[1] and currentStep[1]["editMode"] == editMode):

            correct = False
            tolerance = self.tutorialSteps[self.state][-1]["tolerance"]/100
            meshIndex = -1

            if (editMode and activeObj and activeObj.name == currentStep[-2]):
                # Checking if user is in edit mode and the name of the object selected is the same as the target operation

                objName = currentStep[-2]
                actualMesh = getObjectsOnCache()[objName]
                
                if "vertices" not in currentStep[1]:
                    # If there is no vertices/faces in the next operation, means it was something like "add material"
                    # therefore We can skip mesh verification
                    
                    # Checking if the name of the operation is the same
                    if filteredOp[0] == self.tutorialSteps[self.state][0]:
                        correct = self.recursiveValidate(self.tutorialSteps[self.state], filteredOp, list, tolerance)
                    
                    else:
                        correct = False

                else: 
                    meshes = []
                    numberOfMeshes = 10
                    numberOfSteps = len(self.tutorialSteps)
                    
                    for i in range (self.state, self.state + numberOfMeshes if numberOfSteps >= self.state + numberOfMeshes else numberOfSteps):
                        # Considers the next 5 meshes states. In the case that current state + 5 overflows number of steps, considers until the end of steps

                        step = self.tutorialSteps[i][1]
                        if step["editMode"] == False and self.tutorialSteps[i][0] == 'Toggle Edit Mode':
                            # Means that edit mode was disabled, thus there is no reason to continue comparing following mesh structures
                            break

                        if "vertices" in step and "faces" in step:
                            # If there is a description of the mesh, it is possible to check its similarity
                            meshes.append(step)

                    correct, meshIndex = self.validateFinalValues(tolerance, meshes, actualMesh, self.tutorialSteps[self.state-1][1], objName)

            # Checking if the name of the operation is the same
            elif filteredOp[0] == self.tutorialSteps[self.state][0]:
                correct = self.recursiveValidate(self.tutorialSteps[self.state], filteredOp, list, tolerance)

            print("=========== OPERATION CORRECT? ", correct)

            if correct:
                if(self.state == len(self.tutorialSteps) - 1):
                    return ['end']
                
                else:
                    # If found an equivalent mesh in the next operations, can skip some steps
                    self.state += 1 if meshIndex == -1 else meshIndex + 1
                    return ['correct']

        return ['wrong', filteredOp, self.tutorialSteps[self.state]] # List with wrong and correct operation
        
    def getProgress(self):
        # Returns the percentage of completeness of the tutorial
        if (self.state == len(self.tutorialSteps) - 1 ):
            return 1
        
        else:
            return self.state/( len(self.tutorialSteps) )
    
    def loadCubePyramidTutorial(self):

        self.tutorialSteps = [['Add', 'Cube'], ['Move', mathutils.Vector((5.0, 0.0, 0.0))], ['Resize', mathutils.Vector((2.0, 2.0, 2.0))], ['Add', 'Cube'], ['Move', mathutils.Vector((0.0, 0.0, 3.0))], ['Move', mathutils.Vector((5.0, 0.0, 0.0))], ['Add', 'Cube'], ['Resize', mathutils.Vector((0.5, 0.5, 0.5))], ['Move', mathutils.Vector((0.0, 0.0, 4.5))], ['Move', mathutils.Vector((5.0, 0.0, 0.0))]]    


class ModalOperator(bpy.types.Operator):
    """Move an object with the mouse, example"""
    bl_idname = "object.modal_operator"
    bl_label = "Simple Modal Operator"
    
    prevOperation = None
    currOperation = None
    tut = None
    tutorialMode = False
    recommender = None

    def modal(self, context, event):

        if ((bpy.context.active_object == None and len(getAllObjects().keys()) == 0) or not useLogger):
            # Means that initialized the addon with no object in the scene or logger not started
            if (not useLogger):
                return {'CANCELLED'}
            
            return {'PASS_THROUGH'}

        elif event.type in {'LEFTMOUSE', 'RIGHTMOUSE','TAB', 'RET', 'INBETWEEN_MOUSEMOVE', 'DEL'}:

            isSame = isSameOperation(context.active_operator, event.mouse_x, event.mouse_y)

            if (type(isSame) != bool):

                # Has to save in the formatted form because otherwise it will save the struct in the memory
                self.currOperation = formatOperation2(context.active_operator, isSame)
                
                if (len(self.currOperation) == 0): 
                    return {'PASS_THROUGH'}

                if self.tutorialMode:
                    result = self.tut.validateStep(self.currOperation)
                    if (result == ['correct']):
                        self.recommender.updateUserProfile(self.currOperation[0], True)
                        print("============================ Correct operation!")
                        print("============================ Your progress: ", self.tut.getProgress() * 100, " %")
                        stepDescription = copy.deepcopy(self.tut.getNextStep())
                        if "vertices" in stepDescription[1]:
                            del stepDescription[1]["vertices"]
                        if "faces" in stepDescription[1]:
                            del stepDescription[1]["faces"]
                            
                        print("\n============================ NEXT STEP: Perform the following operation: ", stepDescription)
                        update_user_feedback("Correct operation! Your current progress: " + str(self.tut.getProgress() * 100) + "%. Next step:  Perform the following operation: " + str(stepDescription[0]) + " on object '" + str(stepDescription[-2]) + "'")

                    elif(result == ['end']):
                        recommendations = self.recommender.makeRecommendation()

                        if recommendations[0] == "" and recommendations[1] == "":
                            update_user_feedback("Tutorial Completed!. WARNING: The system could not gather enough information to make a recommendation nor identify your difficulties! Please, do more tutorials!")
                        else:
                            update_user_feedback("Tutorial Completed! Difficulties identified in the following operations: " + str(self.recommender.getUserDifficulties()) + "    Tutorials recommended: " + str(self.recommender.makeRecommendation()))
                        
                        print("============================ Tutorial Finished!")
                        print("\n RECOMMENDATIONS: ", self.recommender.makeRecommendation())
                        stopLogger(reason=1)
                    else:
                        # self.recommender.updateUserProfile(self.currOperation[0], False)
                        
                        # Updates user profile based on what shoud've been done
                        self.recommender.updateUserProfile(result[2][0], False)
                        print("============================ WRONG OPERATION!")
                        print("============================ Expected operation: ", result[2][0])
                        print("============================ Got:                ", result[1][0])

                        if bpy.context.scene.user_feedback[:7] == "Correct":
                            update_user_feedback("WRONG OPERATION! Expected operation: '" + str(result[2][0]) + "' but got: '" + str(result[1][0]) + "'")
                
                else:
                    self.tut.addTutorialStep(self.currOperation)


                self.prevOperation = self.currOperation
                
            return {'PASS_THROUGH'}


        elif event.type == 'NUMPAD_ASTERIX':

            print("=============== CANCELLING LOGGER MODAL ===============")
            return {'CANCELLED'}

        else:
            return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.object or context.object == None:

            global tutFileName
            global tutorialMode

            self.tut = Tutorial()

            if tutorialMode:
                # If in tutorial mode, has to load the tutorial specified by name
                self.tut.loadTutorialSteps(tutFileName)
                self.tutorialMode = True

                self.recommender = recommenderSys()
                firstStep = self.tut.getNextStep()
                update_user_feedback("First step:  Perform the following operation: " + str(firstStep[0]) + " on object '" + str(firstStep[-2]) + "'")

            context.window_manager.modal_handler_add(self)

            #     return {'RUNNING_MODAL'}

            # Fill the cache with the current objects and modifiers on the scene
            objsDict = getAllObjects(firstCall=True)
            modifiersList = getAllModifiers()

            saveModifiersOnCache(modifiersList)
            saveObjectsOnCache(objsDict)

            # If on edit mode, save all its vertices already in the cache
            if(bpy.context.active_object and bpy.context.active_object.mode == 'EDIT'):
                print("SAVING ON CACHE")
                saveObjectVerticesOnCache(getAllVerticesOfObject())
                saveObjectFacesOnCache(getAllFacesOfObject())

            # Update the number of operations performed so far
            global numberOfOp
            operations = getPerformedOperations()
            numberOfOp = len(operations)

            print("================================= Initializing in the CREATE TUTORIAL MODE")

            return {'RUNNING_MODAL'}

        else:
            self.report({'WARNING'}, "No active object, could not finish")
            return {'CANCELLED'}

class recommenderSys:

    # Alpha = influence of old user model
    alpha = 1.0
    # Beta = influence of useful terms (in this case, incorrectly perfromed operations)
    beta = 0.5
    # Gamma = influence of non useful terms (in this case, correctly perfromed operations)
    gamma = -0.5
    # userProfile = updated (and normalized) weights for the useful terms
    userProfile = []
    
    # List containing all the terms (name of operations) found in tutorials
    allTerms = []
    # Dictionary containing all tutorials and all terms
    termsDict = {}

    def __init__(self):

        # Get the path to the folder containing all the tf-idf calculated
        # file_name = 'termWeights.txt'
        # tutorials_path = os.path.join(os.path.dirname(__file__), 'blenderProject') 
        # file_path = os.path.join(tutorials_path, file_name)

        # Get cache of user Profile. If it is set, means that has to load a pre-existent user profile
        global userProfileCache

        file_path = bpy.path.abspath('//termWeights.txt')

        # Read the dictionary containing all the calculated weights
        with open(file_path, 'r') as file:
            self.termsDict = json.load(file)

        file.close()

        if len(userProfileCache) != 0:
            print("############ DEBUG: Found user profile! Loading it: ", userProfileCache)
            self.userProfile = userProfileCache
        
        else:
            # User profile length should be equal to the number of terms found in the tutorials
            self.userProfile = [0] * len(self.termsDict["allTerms"])

        self.allTerms = self.termsDict["allTerms"]

        print("############ DEBUG: All terms: ", self.allTerms)

    def getAllTerms(self):
        # Returns a list containing all the names of operations in order for the Rocchio's algorithm
        return self.allTerms


    def updateUserProfile(self, operationName, correct):
        # Given an operation name and if the operation was correct, update user profile according
        # to alpha, beta and gamma.
        # NOTE: The operation names are actually the terms used to calculate relevance of tutorials

        print("############ DEBUG: old profile: ", self.userProfile)

        if operationName in self.allTerms:
            # List where it is equal to 1 only for the operation name
            update = [1 if name == operationName else 0 for name in self.allTerms]

            if correct:
                # Means gamma should be used
                self.userProfile = np.add(np.multiply(self.userProfile, self.alpha), np.multiply(update, self.gamma))
            
            else:
                # Means beta should be used
                self.userProfile = np.add(np.multiply(self.userProfile, self.alpha), np.multiply(update, self.beta))
            
            # Updating the cache with the new user profile
            global userProfileCache
            userProfileCache = self.userProfile

        else:
            print("ERROR! operation name not found as a pre-calculated term!!")

        print("############ DEBUG: new profile: ", self.userProfile)
        
    def makeRecommendation(self):
        # Returns a list of the top 2 recommendations (excluding the current one)
        
        # Name of the tutorial loaded (current)
        global tutFileName

        # First remove negative values (since minimum is 0 in calculated weights) and it can result to negative cosine similarity
        positiveProfile = [0 if value < 0 else value for value in self.userProfile]

        # After, normalize updated user profile
        normalizedProfile = np.divide(positiveProfile, np.sqrt(np.sum(np.square(positiveProfile))))


        bestSimilarities = [0, 0]
        recommendations = ["", ""]

        for tutName in self.termsDict['allTutorials'].keys():
            # Exclude the current tutorial (cannot recommend the same tutorial)
            if tutName != tutFileName:
                weights = self.termsDict['allTutorials'][tutName]

                print("############ DEBUG: tutName and weight: ", tutName, "\n", weights)

                # Sice both weights and normalizedProfile are already normalized, cosine similarity is just the dot product
                cosineSimilarity = np.dot(np.array(normalizedProfile), np.array(weights))
                print("############ DEBUG: CosineSimilarity: ", cosineSimilarity)

                if cosineSimilarity > bestSimilarities[0]:
                    
                    old = bestSimilarities[0]
                    bestSimilarities[0] = cosineSimilarity
                    bestSimilarities[1] = old     

                    oldRec = recommendations[0]
                    recommendations[0] = tutName
                    recommendations[1] = oldRec

                elif cosineSimilarity > bestSimilarities[1]:

                    bestSimilarities[1] = cosineSimilarity
                    recommendations[1] = tutName

        return recommendations

    def getUserDifficulties(self):
        "Return the 2 (if there are) most positive terms names"
        
        difficulties = []
        userProfileList = list(self.userProfile)
        difficultiesIndices = [userProfileList.index(x) for x in sorted(userProfileList, reverse=True)[:2]]

        for index in difficultiesIndices:
            difficulties.append(self.allTerms[index])

        return difficulties

class StartLogger(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.log_actions"
    bl_label = "Log User Actions"

    @classmethod
    def poll(cls, context):
        # Can only click here if logger hasn't started yet
        global useLogger
        return not useLogger

    def execute(self, context):
        startLogger(context)
        return {'FINISHED'}
    
class StopLogger(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.stop_logger"
    bl_label = "Stop logging the actions"

    @classmethod
    def poll(cls, context):
        # Can only click here if logger has started
        global useLogger
        return useLogger
        # return context.active_object is not None

    def execute(self, context):
        stopLogger()
        return {'FINISHED'}
    
class StartTutorial(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.start_tutorial"
    bl_label = "Load tutorial by name"

    @classmethod
    def poll(cls, context):
        # Can only click here if logger hasn't started
        
        global useLogger
        return not useLogger
        # return context.active_object is not None

    def execute(self, context):
        fileName = context.scene.tutorial_filename
        file_path = bpy.path.abspath('//'+fileName)

        if not os.path.exists(file_path):
            self.report({'ERROR'}, "File does not exist at the specified path.")
            return {'CANCELLED'}
        
        # highlightVertices("Cube", {0: [0,0,0]}, {0: [0,0,1]})
        startLogger(context, tutMode=True, fileName = fileName)
        return {'FINISHED'}
    
class LayoutDemoPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_idname = "BLENDER_PT_Logger"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Blender Logger'
    bl_label = "Logger"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        # Start Logger
        layout.label(text="Start the logger:")
        row = layout.row()
        row.scale_y = 3.0
        row.operator("object.log_actions")

        # Stop Logger
        layout.label(text="Stop the logger:")
        row = layout.row()
        row.scale_y = 3.0
        row.operator("object.stop_logger")

        # Load Tutorial
        layout.label(text="Load a tutorial:")
        row = layout.row()
        row.label(text = "File Name:")
        row = layout.row()
        row.prop(context.scene, "tutorial_filename", text="")
        row = layout.row()
        row.scale_y = 3.0
        row.operator("object.start_tutorial")

class RecommenderMessages(bpy.types.Panel):
    """Place where the messages are displayed"""
    bl_idname = "BLENDER_PT_Messages"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Blender Logger'
    bl_label = "System Messages"

    def draw(self, context):

        global userFeedback
        layout = self.layout

        scene = context.scene
        user_feedback = scene.user_feedback

        # Sys Messages
        layout.label(text="")

        lines = split_text(user_feedback, width=40)  # Adjust width as needed
        for line in lines:
            row = layout.row()
            row.label(text=line)


# ======================================================================================================================= #
# ======================================================================================================================= #
# ======================================================================================================================= #

def format_list_as_string(my_list):
    result = "["

    for item in my_list:
        if isinstance(item, list):
            result += format_list_as_string(item)
        else:
            result += repr(item)

        if item != my_list[-1]:
            result += ", "

    result += "]"
    return result

def formatUserProfile(userProf):
    result = "["
    lastIndex = len(userProf) - 1

    for i, item in enumerate(userProf):
        result += repr(item)

        if i < lastIndex:
            result += ", "

    result += "]"
    return result

def startLogger(context, tutMode = False, fileName = ""):
    global useLogger
    global tutorialMode
    global tutFileName

    if (tutMode):
        tutFileName = fileName
        tutorialMode = True

        if os.path.exists(bpy.path.abspath('//user_profile.txt')):
            
            # Than has to load user profile from txt
            global userProfileCache

            # Open the file in read mode
            with open(bpy.path.abspath('//user_profile.txt'), 'r') as file:
                # Read each line using a loop
                for line in file:
                    userProfileCache = [float(value) for value in line.strip()[1:-1].split(",")]

            file.close()

    else:
        tutorialMode = False
        update_user_feedback("")
    
    useLogger = True
    bpy.ops.object.modal_operator('INVOKE_DEFAULT')
    print("============================================== LOGGER STARTED ==============================================")

def stopLogger(reason = None):

    global tutorialMode
    global logCache
    global useLogger

    if reason == None:
        update_user_feedback("")

    log_file_path = bpy.path.abspath('//logger_log.txt')

    with open(log_file_path, 'w') as file:
        # Convert the list to a string

        for action in logCache:
            # Write the string to the file
            file.write(format_list_as_string(action) + '\n')
    
    file.close()

    if tutorialMode:
        # Then, before stopping, has to save the user profile to be loaded again if user continue to use the system
        global userProfileCache
        userProf_file_path = bpy.path.abspath('//user_profile.txt')

        with open(userProf_file_path, 'w') as file:

            # Convert the list to a string
            file.write(formatUserProfile(userProfileCache))

        file.close()
        
    useLogger = False
    print("============================================== LOGGER STOPPED ==============================================")

def menu_func(self, context):
    self.layout.operator(ModalOperator.bl_idname, text=ModalOperator.bl_label)


# Register and add to the "view" menu (required to also use F3 search "Simple Modal Operator" for quick access).
def register():
    bpy.utils.register_class(StartLogger)
    bpy.utils.register_class(StopLogger)
    bpy.utils.register_class(StartTutorial)
    bpy.utils.register_class(LayoutDemoPanel)
    bpy.utils.register_class(RecommenderMessages)
    bpy.utils.register_class(ModalOperator)
    bpy.types.VIEW3D_MT_object.append(menu_func)
    bpy.types.Scene.tutorial_filename = bpy.props.StringProperty(name="Tutorial Filename", default="")
    bpy.types.Scene.user_feedback = bpy.props.StringProperty(
        name="User Feedback",
        description="System messages displayed here",
        default="Initial message"
    )


def unregister():
    bpy.utils.unregister_class(StartLogger)
    bpy.utils.unregister_class(StopLogger)
    bpy.utils.unregister_class(StartTutorial)
    bpy.utils.unregister_class(LayoutDemoPanel)
    bpy.utils.unregister_class(RecommenderMessages)
    bpy.utils.unregister_class(ModalOperator)
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    del bpy.types.Scene.tutorial_filename
    del bpy.types.Scene.user_feedback


if __name__ == "__main__":
    register()