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

useLogger = False
logCache = []
numberOfOp = 0

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

def saveObjectVerticesOnCache (vertDict):
    # Saves all the vertices of an object in the cache

    if (bpy.context.active_object):
        cacheDict["allObjects"][bpy.context.active_object.name]["vertices"] = vertDict

    else:
        print("No active object to save the vertices on the cache")

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
        
        print("Not recognized operation: ", operator.name)
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

def formatOperation(operator, isSame = False):
    # Receives an operator (= bpy.context.active_operator) and returns it on the correct format to be used on the tutorial. It can also receive a string in the "isSame" field, indicating it is not an operator

    if (type(isSame) == bool):
        # Means it is an operator
        opName = operator.name
        result = operatorsDict.get(opName, defaultCase)(operator)

    else:
        # Means it is not an operator
        formattedAction = tuple([part.split('["')[0].split(" =")[0] for part in isSame.split('.')][:-1])
        result = notOperatorsDict.get(formattedAction, notOperatorDefaultCase)(isSame)

    return result

def isSameOperation(formattedOldOp, newOp, mouse_x, mouse_y, tut = None):
    # Receives 2 operations - old (formatted = [operator name, properties]) and new (= bpy.context.active_operator) - and compare them to return if they are the same operation (true or false)


    operations = getPerformedOperations(mouse_x, mouse_y)
    
    if (len(operations) != 0):
        # It happens sometimes that the operations list comes empty
    
        lastOp = operations[-1]
        global numberOfOp

        if (len(operations) - numberOfOp > 1):
            for operation in operations[-(len(operations) - numberOfOp):]:
                if (operation[:3] == "bpy" and operation[:34] != 'bpy.data.window_managers["WinMan"]'):
                    # Pick the last bpy occurence, ignore if window change so it keeps the operation itself
                    lastOp = operation


        if (len(operations) > numberOfOp and lastOp[:7] == "bpy.ops"):
            # Means that an operation has been performed
            numberOfOp = len(operations)
            
            if (newOp == None):
                # Operations like undo (ctrl z) or other specific operations are recognized as none
                return True

            else:
                
                return False

        
        elif (len(operations) > numberOfOp and lastOp[:3] == "bpy" and lastOp[:34] != 'bpy.data.window_managers["WinMan"]'):
            # Detected something that is not an operation, so treat them according to the type of action

            numberOfOp = len(operations)
            return operations[-1]

        else:
            return True
        
    else:
        return True
    
def getAllObjects():
    # Gets all the objects in the scene.

    objsDict = {}

    objs = bpy.context.scene.objects
    for obj in objs:
        objsDict[obj.name] = {  "scale": list(obj.scale),
                                "location": list(obj.location),
                                "rotation": list(obj.rotation_euler),
                                "vertices": {},
                                "isSmooth": True if (obj.type == "MESH" and any(face.use_smooth for face in obj.data.polygons)) else False}

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


# ======================================================================================================================= #
# ================================================ Classes ============================================================== #
# ======================================================================================================================= #

class Tutorial:
    def __init__(self, tutorialSteps = None):
        if tutorialSteps is not None:
            self.loadTutorialSteps(tutorialSteps)

        else:
            self.tutorialSteps = []
        
        self.state = 0 # Var to track the state on the tutorial. 0 - N where N is the total number of steps -1. If state == N, tutorial ended.

    def addTutorialStep(self, step):
        # Receives a list containing [operator.name, properties]

        self.tutorialSteps.append(step)
        print(self.tutorialSteps)

        global logCache
        logCache = self.tutorialSteps

    def loadTutorialSteps(self, tutorialSteps):
        # Receives a list with all the tutorial steps: [[operator.name 1, properties 1], [operator.name 2, properties 2] ...]

        self.tutorialSteps = tutorialSteps
        print(self.tutorialSteps)

    def getNextStep(self):
        return self.tutorialSteps[self.state]

    def validateStep(self, step):
        # Validates the step passed [operator.name, properties] with the current state of the tutorial

        if step == self.tutorialSteps[self.state]:
            if(self.state == len(self.tutorialSteps) - 1):
                return ['end']
            
            else:
                self.state += 1
                return ['correct']
        else:
            return ['wrong', step, self.tutorialSteps[self.state]] # List with wrong and correct operation
        
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
    
    tutState = 0
    prevOperation = None
    currOperation = None
    tut = None

    def modal(self, context, event):

        if ((bpy.context.active_object == None and len(getAllObjects().keys()) == 0) or not useLogger):
            # Means that initialized the addon with no object in the scene or logger not started
            return {'PASS_THROUGH'}

        elif event.type in {'LEFTMOUSE','TAB', 'RET', 'INBETWEEN_MOUSEMOVE', 'DEL'}:

            isSame = isSameOperation(self.prevOperation, context.active_operator, event.mouse_x, event.mouse_y, self.tut,)

            if (isSame != True):

                # Has to save in the formatted form because otherwise it will save the struct in the memory
                self.currOperation = formatOperation(context.active_operator, isSame)
                
                if (len(self.currOperation) == 0): 
                    return {'PASS_THROUGH'}

                self.tut.addTutorialStep(self.currOperation)

                # result = self.tut.validateStep(self.currOperation)
                # if (result == ['correct']):
                #     print("============================ Correct operation!")
                #     print("============================ Your progress: ", self.tut.getProgress() * 100, " %")
                #     print("\n============================ NEXT STEP: Perform the following operation: ", self.tut.getNextStep())
                # elif(result == ['end']):
                #     print("============================ Tutorial Finished!")
                # else:
                #     print("============================ WRONG OPERATION!")
                #     print("============================ Expected operation: ", result[2])

                self.prevOperation = self.currOperation

                # self.tut.validateStep(formattedOp)
                # print("\n Progress: ", self.tut.getProgress())


        elif event.type == 'NUMPAD_ASTERIX':

            print("=============== CANCELLING LOGGER MODAL ===============")
            return {'CANCELLED'}

        # else: 
        #     print(event.type)

        # return {'RUNNING_MODAL'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.object or context.object == None:

            self.tut = Tutorial()
            # self.tut.loadCubePyramidTutorial()

            context.window_manager.modal_handler_add(self)

            # if context.object == None:
            #     return {'RUNNING_MODAL'}

            # Fill the cache with the current objects and modifiers on the scene
            objsDict = getAllObjects()
            modifiersList = getAllModifiers()

            saveModifiersOnCache(modifiersList)
            saveObjectsOnCache(objsDict)

            # If on edit mode, save all its vertices already in the cache
            if(bpy.context.active_object and bpy.context.active_object.mode == 'EDIT'):
                print("SALVANDO NO CACHE")
                saveObjectVerticesOnCache(getAllVerticesOfObject())

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
        return context.active_object is not None

    def execute(self, context):
        startLogger(context)
        return {'FINISHED'}
    
class StopLogger(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.stop_logger"
    bl_label = "Stop logging the actions"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        stopLogger(context)
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

def startLogger(context):
    global useLogger
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
    bpy.utils.register_class(LayoutDemoPanel)
    bpy.utils.register_class(ModalOperator)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.utils.unregister_class(StartLogger)
    bpy.utils.unregister_class(StopLogger)
    bpy.utils.unregister_class(LayoutDemoPanel)
    bpy.utils.unregister_class(ModalOperator)
    bpy.types.VIEW3D_MT_object.remove(menu_func)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.object.modal_operator('INVOKE_DEFAULT')
