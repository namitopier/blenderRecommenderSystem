bl_info = {
    "name": "Blender Logger",
    "author": "Pier Luigi Nakai Ricchetti",
    "version": (1, 0),
    "blender": (3, 2, 2),
    "location": "View3D > Sidebar > Blender Logger",
    "description": "Logs user actions",
    "warning": "",
    "wiki_url": "",
    "category": "Blender Logger",
}

import bpy, bmesh
from bpy.props import IntProperty, FloatProperty
import mathutils
import math
import re
import os

useLogger = False
logCache = []
numberOfOp = 0
globalLastOp = None
tutorialMode = False
tutFileName = ""

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

def saveTempValueOnCache (tempValue):
    cacheDict["tempValue"] = tempValue

def getTempValueOnCache():
    return cacheDict["tempValue"]

def getObjectsOnCache():
    return cacheDict["allObjects"]

def getModifiersOnCache():
    return cacheDict["allModifiers"]

# ======================================================================================================================= #
# ========================================= Operator Functions ========================================================== #
# ======================================================================================================================= #

def runScriptOp(operator):
    return ["Run Script"]

def editModeOp(operator):

    activeObj = bpy.context.active_object
    mode = activeObj.mode

    if (mode == 'EDIT'):
        saveObjectVerticesOnCache(getAllVerticesOfObject())

    return [operator.name, mode, activeObj.name] 

def renameOp(operator):

    currentObjsDict = getAllObjects()

    # Get the name of the objects in the scene
    currentObjects = list(currentObjsDict.keys())
    oldObjects = list(getObjectsOnCache().keys())
    
    # Get the object/s that have been renamed
    set1 = set(currentObjects)
    set2 = set(oldObjects)
    difference = set1.symmetric_difference(set2)

    saveObjectsOnCache(currentObjsDict)

    return [operator.name, list(difference)]

def addModifierOp(operator):
   
    return [operator.name, operator.properties.type, bpy.context.active_object.name]

def removeModifierOp(operator):

    return [operator.name, operator.properties.modifier, bpy.context.active_object.name]

def addConstraintOp(operator):


    return [operator.name, operator.properties.type, bpy.context.active_object.name]

def deleteConstraintOp(operator):

    return [operator.name, {    "constraint": operator.properties.constraint,
                                "owner": operator.properties.owner
                            }, bpy.context.active_object.name]

def transformOp(operator):
    # Returns the final objects position / rotation / scale

    activeObj = bpy.context.view_layer.objects.active
    mode = activeObj.mode
    objsDict = getObjectsOnCache()

    if (mode == "OBJECT"):
        # Save new transform properties of objetcs
        saveObjectsOnCache(getAllObjects())


    if(mode == 'EDIT'):
        if (activeObj.type != "MESH"):
            return ["Transform operation performed on: ", activeObj.type]
        
        allVertices = getAllVerticesOfObject()
        oldVertices = objsDict[activeObj.name]["vertices"]

        # Checking which are the vertices that have been modified
        difference = []
        for key in allVertices.keys():
            if (allVertices[key] != oldVertices[key]): difference.append(key)

        saveObjectVerticesOnCache(allVertices)

        if (operator.name == "Rotate"):
            rotateValue = math.degrees(operator.properties.value)
            return  [operator.name, {
                                        "vertices": allVertices,
                                        "selectedVertices": difference,
                                        "value": [rotateValue if operator.properties.constraint_axis[0] else 0, rotateValue if operator.properties.constraint_axis[1] else 0, rotateValue if operator.properties.constraint_axis[2] else 0]
                                        },
                    activeObj.name]
        
        elif (operator.name == "Move" or operator.name == "Resize"):
            return  [operator.name, {
                                        "vertices": allVertices,
                                        "selectedVertices": difference,
                                        "value": list(operator.properties.value)
                                        },
                    activeObj.name]

    elif(operator.name == "Rotate"):
        return  [operator.name, list(activeObj.rotation_euler), activeObj.name]
    
    elif(operator.name == "Move"):
        return  [operator.name, list(activeObj.location), activeObj.name]

    elif(operator.name == "Resize"):
        return  [operator.name, list(activeObj.scale), activeObj.name]
    
    # return [operator.name, operator.properties.value]

def deleteOp(operator):

    activeObj = bpy.context.view_layer.objects.active

    if (activeObj == None):
        mode = "OBJECT"
    else:
        mode = activeObj.mode

    if (mode == "EDIT"):
        if (activeObj.type != "MESH"):
            return ["Delete operation performed on: ", activeObj.type]

        allVertices = getAllVerticesOfObject()
        objsDict = getObjectsOnCache()

        currentVertices = list(allVertices.keys())
        oldVertices = list(objsDict[activeObj.name]["vertices"].keys())

        difference = list( set(currentVertices).symmetric_difference(set(oldVertices)) ) # List of the keys of the vertices that have been deleted

        saveTempValueOnCache(operator.properties.type)
        saveObjectVerticesOnCache(allVertices)

        return [operator.name, {
                                    "value": operator.properties.type, # indicates what have been deleted: Vertices, faces or edges
                                    "selectedVertices": difference
                                },
                activeObj.name]

    else:

        currentObjsDict = getAllObjects()

        currentObjects = list(currentObjsDict.keys())
        oldObjects = list(getObjectsOnCache().keys())
        
        # Get the object/s that have been deleted
        set1 = set(currentObjects)
        set2 = set(oldObjects)
        difference = set1.symmetric_difference(set2)

        saveObjectsOnCache(currentObjsDict)

        return [operator.name, list(difference)]
    
def shadeChangeOp(operator):
    activeObj = bpy.context.view_layer.objects.active
    
    currObjects = getAllObjects()
    saveObjectsOnCache(currObjects)

    return [operator.name, activeObj.name]
    
def clearOp(operator):
    activeObj = bpy.context.view_layer.objects.active
    allObjs = getAllObjects()
        
    saveObjectsOnCache(allObjs)

    return [operator.name, operator.properties.clear_delta, activeObj.name]
    
def duplicateObjOp(operator):
    activeObj = bpy.context.view_layer.objects.active
    allObjs = getAllObjects()

    saveObjectsOnCache(allObjs)

    return [operator.name, activeObj.name]
    
def recalcNormalsOp(operator):
    activeObj = bpy.context.view_layer.objects.active
    
    return [operator.name, {"inside" : operator.properties.inside},activeObj.name]
    
def mirrorOp(operator):

    activeObj = bpy.context.view_layer.objects.active
    mode = activeObj.mode

    # Need to update the new positions of all vertices if in EDIT mode
    if (mode == "EDIT"):
        allVertices = getAllVerticesOfObject()
        saveObjectVerticesOnCache(allVertices)

    return [operator.name, {    "orientType": operator.properties.orient_type,
                                "constraintAxis": list(operator.properties.constraint_axis) }, activeObj.name]

def snapOp(operator):

    activeObj = bpy.context.view_layer.objects.active
    if (activeObj == None):
        objName = "None"
        mode = "OBJECT"
    else:
        objName = activeObj.name
        mode = activeObj.mode

    # Need to update the new positions of all vertices if in EDIT mode
    if (mode == "EDIT"):
        allVertices = getAllVerticesOfObject()
        saveObjectVerticesOnCache(allVertices)
    
    # useOffset is only available as an option if "Snap Selection to Cursor" is selected. Otherwise, will return None
    return [operator.name, { "useOffset": operator.properties.use_offset if operator.name == "Snap Selection to Cursor" else None }, objName]

def subDivisionSetOp(operator):

    activeObj = bpy.context.view_layer.objects.active
    objName = activeObj.name if activeObj != None else None # User can try to apply this operation to no object
    
    return [operator.name, { "level": operator.properties.level,
                             "relative": operator.properties.relative }, objName]

def newCollectionOp(operator):

    return [operator.name, "Scene"]

def moveToCollectionOp(operator):

    return [operator.name, {    "isNew": operator.properties.is_new,
                                "newCollectionName": operator.properties.new_collection_name,
                                "collectionIndex": operator.properties.collection_index }, "Scene"]

# ===================== FOR EDIT MODE ==============================

def insetOp(operator):

    activeObj = bpy.context.view_layer.objects.active
    allVertices = getAllVerticesOfObject()  
    objsDict = getObjectsOnCache()
    
    oldVertices = objsDict[activeObj.name]["vertices"]

    # Checking which are the vertices that have been modified
    difference = []

    for key in allVertices.keys():
        if (key not in oldVertices): difference.append(key)
  
    saveObjectVerticesOnCache(allVertices)
    return [operator.name, {    "vertices": allVertices,
                                "newVertices": difference,
                                "value": operator.properties.thickness}, activeObj.name]

def subdivideOp(operator):

    activeObj = bpy.context.view_layer.objects.active
    allVertices = getAllVerticesOfObject()  
  
    saveObjectVerticesOnCache(allVertices)
    return [operator.name, operator.properties.number_cuts, activeObj.name]

def extrudeOp(operator):

    activeObj = bpy.context.view_layer.objects.active
    allVertices = getAllVerticesOfObject()  
    objsDict = getObjectsOnCache()

    operations = getPerformedOperations()

    if (len(operations) == 0):
        saveObjectVerticesOnCache(allVertices)

        return [operator.name, {    "vertices": allVertices,
                                    "newVertices": 0,
                                    "value": [0, 0, 0]}, activeObj.name]
    
    else:
        oldVertices = objsDict[activeObj.name]["vertices"]

        # Checking which are the vertices that have been modified
        difference = []

        for key in allVertices.keys():
            if (key not in oldVertices): difference.append(key)

        extrudeValue = [float(value) for value in operations[-1].split('TRANSFORM_OT_translate={"value":')[1].split("),")[0][1:].split(",")]
        saveObjectVerticesOnCache(allVertices)

        return [operator.name, {    "vertices": allVertices,
                                    "newVertices": difference,
                                    "value": extrudeValue}, activeObj.name]

def mergeByDistanceOp(operator):

    activeObj = bpy.context.view_layer.objects.active
    allVertices = getAllVerticesOfObject()
    objsDict = getObjectsOnCache()

    currentVertices = list(allVertices.keys())
    oldVertices = list(objsDict[activeObj.name]["vertices"].keys())

    difference = list( set(currentVertices).symmetric_difference(set(oldVertices)) ) # List of the keys of the vertices that have been merged

    saveObjectVerticesOnCache(allVertices)

    return [operator.name, {
                                "threshold": operator.properties.threshold,
                                "use_unselected": operator.properties.use_unselected,
                                "use_sharp_edge_from_normals": operator.properties.use_sharp_edge_from_normals,
                                "selectedVertices": difference
                            },
            activeObj.name]


def selectAllOp(operator):

    return [operator.name, operator.properties.action]


def defaultCase(operator):

    global numberOfOp

    if (type(operator) != str and operator.name[:3] == "Add"):

        activeObj = bpy.context.view_layer.objects.active
        mode = activeObj.mode

        if (mode == "EDIT"):

            allVertices = getAllVerticesOfObject()

            saveObjectVerticesOnCache(allVertices)
            return [operator.name[:3], operator.name[4:], bpy.context.active_object.name]
        
        else:

            currentObjsDict = getAllObjects()
            saveObjectsOnCache(currentObjsDict)

            return [operator.name[:3], operator.name[4:], bpy.context.active_object.name]
    

    else:
        global globalLastOp

        print("Not recognized operation: ", operator.name)

        # Regular expression pattern to match arguments and values
        arguments_pattern = re.compile(r"(\w+)\s*=\s*([^,)]+)")

        # Extract arguments and values
        arguments_matches = arguments_pattern.findall(globalLastOp)

        # Create a list of alternating names and values
        result_list = [item for sublist in arguments_matches for item in sublist]

        print("Trying to translate: [%d, %d]" %(operator.name, result_list))

        return ["Not recognized operation: {}".format(operator.name)]

operatorsDict = {
    "Run Script": runScriptOp,
    "Toggle Edit Mode": editModeOp,
    "Rename": renameOp,
    "(De)select All": selectAllOp,
    "Subdivision Set": subDivisionSetOp,

    # Collections:
    "New Collection": newCollectionOp,
    "Move to Collection": moveToCollectionOp,

    # Modifiers and Constraints
    "Add Modifier": addModifierOp,
    "Remove Modifier": removeModifierOp,
    "Add Constraint": addConstraintOp,
    "Delete Constraint": deleteConstraintOp,

    # Transform ops
    "Resize": transformOp,
    "Move": transformOp,
    "Rotate": transformOp,

    # Modifications in Object mode
    "Delete": deleteOp,
    "Duplicate Objects": duplicateObjOp,
    "Mirror": mirrorOp,

    # Normals and shading
    "Shade Smooth": shadeChangeOp,
    "Shade Flat": shadeChangeOp,
    "Recalculate Normals": recalcNormalsOp,

    "Clear Scale": clearOp,
    "Clear Location": clearOp,
    "Clear Rotation": clearOp,

    "Snap Selection to Cursor" : snapOp,
    "Snap Selection to Active" : snapOp,
    "Snap Selection to Grid" : snapOp,
    "Snap Cursor to Active" : snapOp,
    "Snap Cursor to Selected" : snapOp,
    "Snap Cursor to World Origin" : snapOp,
    "Snap Cursor to Grid" : snapOp,

    # For edit mode:
    "Subdivide": subdivideOp,
    "Extrude Region and Move": extrudeOp,
    "Inset Faces": insetOp,
    "Merge by Distance": mergeByDistanceOp,
}

def changeShading(description):
    # Changing the shade mode of the 3D view

    newMode = description.split("= '")[1].strip("'")
    return ["Change shading mode", newMode, "Scene"]

def notOperatorDefaultCase(description):
    return ["Not recognized user action: {}".format(description)]

notOperatorsDict = {
    ("bpy", "context", "space_data", "shading"): changeShading,
}

# ======================================================================================================================= #
# ============================================ Util Functions =========================================================== #
# ======================================================================================================================= #

# def formatOperation(operator, isSame = False):
#     # Receives an operator (= bpy.context.active_operator) and returns it on the correct format to be used on the tutorial. It can also receive a string in the "isSame" field, indicating it is not an operator

#     if (type(isSame) == bool):
#         # Means it is an operator
#         opName = operator.name
#         result = operatorsDict.get(opName, defaultCase)(operator)

#     else:
#         # Means it is not an operator
#         formattedAction = tuple([part.split('["')[0].split(" =")[0] for part in isSame.split('.')][:-1])
#         result = notOperatorsDict.get(formattedAction, notOperatorDefaultCase)(isSame)

#     return result

def formatOperation2(operator, isSame):
    # Receives an operator (= bpy.context.active_operator) and returns it on the correct format to be used on the tutorial. It can also receive a string in the "isSame" field, indicating it is not an operator

# =======================================================================================================
                
    if isSame[:7] == "bpy.ops":
        # The structure of bpy.ops is different than the others -> means it is actually an operation

        result = ""
        activeObj = bpy.context.view_layer.objects.active
        mode = None if activeObj == None else activeObj.mode 

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
            print("AAAAAAAAAAAAAAAAAAAAAA ", objsDict[activeObj.name])
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
                    result["selectedVertices"] = vertDiff

            # Saving all vertices in the result
            result["vertices"] = allVertices
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

        translated = [operator.name, result, None if activeObj == None else activeObj.name]

    else:
        # # In this case, it is considering everything else that is not an operation (bpy.ops) but still is an user action

        # translated = [""]

        # # Get the first (because it might have more equal signs on the other side) occurrence of " = " to divide the 2 parts
        # processed = isSame.split(" = ", maxsplit=1)

        # # Get the value of the property
        # value = eval(processed[1])

        # # List of names, groups etc and operation "address"
        # groupsList = [["group", ""], ["subgroup", ""], ["propIndex", ""]]

        # # Get all the operator "address"
        # processed = processed[0].split(".")

        # groupIndex = 0

        # for i, addr in enumerate(processed[:-1]): # Ignore the last one since it is the property name changed
        #     if "[" in addr:
        #         # Get what is inside: ['groupname']
        #         groupName = addr[addr.index("[")+1:addr.index("]")]
        #         groupName = eval(groupName)
                
        #         if groupIndex <= 2:
        #             groupsList[groupIndex][1] = groupName
                
        #         else:
        #             groupsList.append(["other"+str(groupIndex-2), groupName])

        #         groupIndex += 1

        #         # Get the address without the group name (also getting everything after it because there might be some operations that contains it)
        #         translated[0] = translated[0] + " " + addr[ 0 : addr.index("[") ] + addr[ addr.index("]")+1 : ]

        #     else:
        #         translated[0] = translated[0] + " " + addr

        # groupsList.append([processed[-1], value])
        # translated.append(dict(groupsList))

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
        value = eval(processed[1])
        
        # Get the address of the operation
        processed = processed[0].split(".")

        for addr in processed[:-1]:
            translated[0] += " " + addr

        groupsList = groupsList[0:groupIndex]
        groupsList.append([processed[-1], value])
        translated.append(dict(groupsList))
        translated.append(None if not activeObj else activeObj.name)

    return translated

def isSameOperation(formattedOldOp, newOp, mouse_x, mouse_y, tut = None):
    # Receives 2 operations - old (formatted = [operator name, properties]) and new (= bpy.context.active_operator) - and compare them to return if they are the same operation (true or false)

    operations = getPerformedOperations(mouse_x, mouse_y)
    
    if (len(operations) != 0):
        # It happens sometimes that the operations list comes empty
    
        lastOp = operations[-1]
        global numberOfOp
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
        # if (len(operations) > numberOfOp and lastOp[:7] == "bpy.ops"):
        #     # Means that an operation has been performed
        #     numberOfOp = len(operations)
            
        #     if (newOp == None):
        #         # Operations like undo (ctrl z) or other specific operations are recognized as none
        #         return True

        #     else:
                
        #         return False

        
        # elif (len(operations) > numberOfOp and lastOp[:3] == "bpy" and lastOp[:34] != 'bpy.data.window_managers["WinMan"]'):
        #     # Detected something that is not an operation, so treat them according to the type of action

        #     numberOfOp = len(operations)
        #     return operations[-1]

        # else:
        #     return True
        
    else:
        return True
    
def getAllObjects(firstCall = False):
    # Gets all the objects in the scene.

    objsDict = {}
    changedMode = False

    if firstCall:
        activeObj = bpy.context.view_layer.objects.active

        if activeObj and activeObj.mode == "OBJECT":
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
    
def getPerformedOperations(mouse_x = 0, mouse_y = 0):
    # Gets the list of performed operations

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

def getFilteredOp (translatedOp, additionalInfo = {}):
    # Filters automatically the important values to track + additional values decided by the user

    # By default, it will consider all the first 2 props of all nested dicts of the properties.

    fixedValues = [ "newVertices",
                    "newFaces",
                    "deletedVertices",
                    "deletedFaces",
                    "selectedVertices",
                    "vertices",
                    "editMode",
                    "newscale",
                    "newlocation",
                    "newrotation",
                    "selectedObjs",
                    "editMode",
                    "group",
                    "subgroup",
                    "propIndex"]
    
    additionalProps = [] if "additionalProps" not in additionalInfo else additionalInfo["additionalProps"]
    ignoreProps = [] if "ignoreProps" not in additionalInfo else additionalInfo["ignoreProps"]
    tolerance = 0 if "tolerance" not in additionalInfo else additionalInfo["tolerance"]

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

def highlightVertices(object_name, vertex_indices, highlight_color):
    # Switch to object mode
    bpy.context.view_layer.objects.active = bpy.data.objects[object_name]
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Get the mesh data
    mesh = bpy.data.objects[object_name].data
    
    # Ensure vertex colors are enabled
    if not mesh.vertex_colors:
        mesh.vertex_colors.new()
    
    # Assign highlight color to vertices
    vertex_colors = mesh.vertex_colors.active.data
    for loop_index, loop in enumerate(mesh.loops):
        if loop.vertex_index in vertex_indices:
            for i in range(3):
                vertex_colors[loop_index].color[i] = highlight_color[i]

def clear_vertex_colors(object_name):
    # Switch to object mode
    bpy.context.view_layer.objects.active = bpy.data.objects[object_name]
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Get the mesh data
    mesh = bpy.data.objects[object_name].data
    
    # Ensure vertex colors are enabled
    if not mesh.vertex_colors:
        return
    
    # Iterate over all vertex colors and set them to white
    for vertex_color_layer in mesh.vertex_colors:
        for loop_color in vertex_color_layer.data:
            loop_color.color = (1.0, 1.0, 1.0, 1.0)  # Set to white

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

        print("AAAAAAAAAAAAAAAAAAAAAAAAAAA ", self.tutorialSteps[self.state-1])

        if (self.state != 0 and self.tutorialSteps[self.state-1][1]["editMode"] and ("selectedVertices" in self.tutorialSteps[self.state-1][1]) and len(self.tutorialSteps[self.state-1][1]["selectedVertices"]) > 0):
            object_name = self.tutorialSteps[self.state-1][-2]  # Replace with the name of your object
            clear_vertex_colors(object_name)
        
        if (nextStep[1]["editMode"] and ("selectedVertices" in nextStep[1]) and len(nextStep[1]["selectedVertices"]) > 0):
            object_name = nextStep[-2] 
            vertex_indices = nextStep[1]["selectedVertices"]
            highlight_color = (0.0, 1.0, 0.0)  # RGB
            highlightVertices(object_name, vertex_indices, highlight_color)
        
        return nextStep

    def validateStep(self, step):
        # Validates the step passed [operator.name, properties] with the current state of the tutorial

        # Get the current step
        currentStep = self.tutorialSteps[self.state]

        # Get the filtered operation considering the additional props tracked (last element of saved step)
        filteredOp = getFilteredOp(step, currentStep[-1])

        if filteredOp == self.tutorialSteps[self.state]:
            if(self.state == len(self.tutorialSteps) - 1):
                return ['end']
            
            else:
                self.state += 1
                return ['correct']
        else:
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

    def modal(self, context, event):

        if ((bpy.context.active_object == None and len(getAllObjects().keys()) == 0) or not useLogger):
            # Means that initialized the addon with no object in the scene or logger not started
            if (not useLogger):
                return {'CANCELLED'}
            
            return {'PASS_THROUGH'}

        elif event.type in {'LEFTMOUSE', 'RIGHTMOUSE','TAB', 'RET', 'INBETWEEN_MOUSEMOVE', 'DEL'}:

            isSame = isSameOperation(self.prevOperation, context.active_operator, event.mouse_x, event.mouse_y, self.tut)

            if (type(isSame) != bool):

                # Has to save in the formatted form because otherwise it will save the struct in the memory
                self.currOperation = formatOperation2(context.active_operator, isSame)
                
                if (len(self.currOperation) == 0): 
                    return {'PASS_THROUGH'}

                if self.tutorialMode:
                    result = self.tut.validateStep(self.currOperation)
                    if (result == ['correct']):
                        print("============================ Correct operation!")
                        print("============================ Your progress: ", self.tut.getProgress() * 100, " %")
                        print("\n============================ NEXT STEP: Perform the following operation: ", self.tut.getNextStep())
                    elif(result == ['end']):
                        print("============================ Tutorial Finished!")
                    else:
                        print("============================ WRONG OPERATION!")
                        print("============================ Expected operation: ", result[2])
                        print("============================ Got: ", result[1])
                
                else:
                    self.tut.addTutorialStep(self.currOperation)


                self.prevOperation = self.currOperation

                # self.tut.validateStep(formattedOp)
                # print("\n Progress: ", self.tut.getProgress())
                
            return {'PASS_THROUGH'}


        elif event.type == 'NUMPAD_ASTERIX':

            print("=============== CANCELLING LOGGER MODAL ===============")
            return {'CANCELLED'}

        # else: 
        #     print(event.type)

        # return {'RUNNING_MODAL'}

        else:
            return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.object or context.object == None:

            global tutFileName
            global tutorialMode

            self.tut = Tutorial()
            # self.tut.loadCubePyramidTutorial()

            if tutorialMode:
                # If in tutorial mode, has to load the tutorial specified by name
                self.tut.loadTutorialSteps(tutFileName)
                self.tutorialMode = True

            context.window_manager.modal_handler_add(self)

            # if context.object == None:
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

            # print("\n============================ NEXT STEP: Perform the following operation: ", self.tut.getNextStep())
            print("================================= Initializing in the CREATE TUTORIAL MODE")

            return {'RUNNING_MODAL'}

        else:
            self.report({'WARNING'}, "No active object, could not finish")
            return {'CANCELLED'}
        
class StartLogger(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.log_actions"
    bl_label = "Log User Actions"

    @classmethod
    def poll(cls, context):
        # Can only click here if logger hasn't started yet
        global useLogger
        return not useLogger
        # return context.active_object is not None

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
        stopLogger(context)
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
        
        startLogger(context, tutMode=True, fileName = fileName)
        return {'FINISHED'}
    
class LayoutDemoPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    # bl_label = "Layout Demo"
    bl_idname = "BLENDER_PT_Logger"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Blender Logger'
    bl_label = "Logger"
    # bl_space_type = 'PROPERTIES'
    # bl_region_type = 'WINDOW'
    # bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        
        #print("Chamou DRAW")

#        # Create a simple row.
#        layout.label(text=" Simple Row:")

#        row = layout.row()
#        row.prop(scene, "frame_start")
#        row.prop(scene, "frame_end")

#        # Create an row where the buttons are aligned to each other.
#        layout.label(text=" Aligned Row:")

#        row = layout.row(align=True)
#        row.prop(scene, "frame_start")
#        row.prop(scene, "frame_end")

#        # Create two columns, by using a split layout.
#        split = layout.split()

#        # First column
#        col = split.column()
#        col.label(text="Column One:")
#        col.prop(scene, "frame_end")
#        col.prop(scene, "frame_start")

#        # Second column, aligned
#        col = split.column(align=True)
#        col.label(text="Column Two:")
#        col.prop(scene, "frame_start")
#        col.prop(scene, "frame_end")

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

        # Different sizes in a row
#        layout.label(text="Different button sizes:")
#        row = layout.row(align=True)
#        row.operator("render.render")

#        sub = row.row()
#        sub.scale_x = 2.0
#        sub.operator("render.render")

#        row.operator("render.render")

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

def startLogger(context, tutMode = False, fileName = ""):
    global useLogger
    global tutorialMode
    global tutFileName

    if (tutMode):
        tutFileName = fileName
        tutorialMode = True
    
    useLogger = True
    bpy.ops.object.modal_operator('INVOKE_DEFAULT')
    print("============================================== LOGGER STARTED ==============================================")

def stopLogger(context):

    global logCache
    file_path = bpy.path.abspath('//logger_log.txt')

    with open(file_path, 'w') as file:
        # Convert the list to a string

        for action in logCache:
            # Write the string to the file
            file.write(format_list_as_string(action) + '\n')

    global useLogger
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
    bpy.utils.register_class(ModalOperator)
    bpy.types.VIEW3D_MT_object.append(menu_func)
    bpy.types.Scene.tutorial_filename = bpy.props.StringProperty(name="Tutorial Filename", default="")


def unregister():
    bpy.utils.unregister_class(StartLogger)
    bpy.utils.unregister_class(StopLogger)
    bpy.utils.unregister_class(StartTutorial)
    bpy.utils.unregister_class(LayoutDemoPanel)
    bpy.utils.unregister_class(ModalOperator)
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    del bpy.types.Scene.tutorial_filename


if __name__ == "__main__":
    register()

    # test call
    # bpy.ops.object.modal_operator('INVOKE_DEFAULT')

'''
globalLastOp = 'bpy.ops.mesh.extrude_region_move(
    {
    MESH_OT_extrude_region: {
        "use_normal_flip":False,
        "use_dissolve_ortho_edges":False,
        "mirror":False
        },
    TRANSFORM_OT_translate: {
        "value":(0, 0, 0.716544),
        "orient_type":"NORMAL",
        "orient_matrix":((0, 1, 0), (-1, 0, 0), (0, 0, 1)),
        "orient_matrix_type":"NORMAL",
        "constraint_axis":(False, False, True),
        "mirror":False,
        "use_proportional_edit":False,
        "proportional_edit_falloff":"SMOOTH",
        "proportional_size":1,
        "use_proportional_connected":False,
        "use_proportional_projected":False,
        "snap":False,
        "snap_elements":{"INCREMENT"},
        "use_snap_project":False,
        "snap_target":"CLOSEST",
        "use_snap_self":True,
        "use_snap_edit":True,
        "use_snap_nonedit":True,
        "use_snap_selectable":False,
        "snap_point":(0, 0, 0),
        "snap_align":False,
        "snap_normal":(0, 0, 0),
        "gpencil_strokes":False,
        "cursor_transform":False,
        "texture_space":False,
        "remove_on_cancel":False,
        "use_duplicated_keyframes":False,
        "view2d_edge_pan":False,
        "release_confirm":False,
        "use_accurate":False,
        "alt_navigation":True,
        "use_automerge_and_split":False
        }
    }

    MESH_OT_extrude_region: {"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate: {"value":(0, 0, 0.716544), "orient_type":"NORMAL", "orient_matrix":((0, 1, 0), (-1, 0, 0), (0, 0, 1)), "orient_matrix_type":"NORMAL", "constraint_axis":(False, False, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":"SMOOTH", "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{"INCREMENT"}, "use_snap_project":False, "snap_target":"CLOSEST", "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "use_duplicated_keyframes":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "alt_navigation":True, "use_automerge_and_split":False})'

'''