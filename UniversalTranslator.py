import re
import json

'''
bpy.ops.transform.translate(value=(0, 0.44853, 0), orient_axis_ortho='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False, release_confirm=True)

'''
#globalLastOp = 'bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 0, 0.716544), "orient_type":"NORMAL", "orient_matrix":((0, 1, 0), (-1, 0, 0), (0, 0, 1)), "orient_matrix_type":"NORMAL", "constraint_axis":(False, False, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":"SMOOTH", "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{"INCREMENT"}, "use_snap_project":False, "snap_target":"CLOSEST", "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "use_duplicated_keyframes":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "alt_navigation":True, "use_automerge_and_split":False})'
globalLastOp = "bpy.context.object.modifiers['sdfsdf'].segments = 2"
#globalLastOp = "bpy.ops.transform.translate(value=(0, 0.44853, 0), orient_axis_ortho='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False, release_confirm=True)"

isModifier = False

if ("object.modifiers" in globalLastOp):
    # Means the format will be different
    arguments_pattern = re.compile(r"\.modifiers\['([^']+)'\]\.(\w+)\s*=\s*((?:\([^()]*\)|[^(),]+))")
    isModifier = True

else:
    # Regular expression pattern to match arguments and values
    arguments_pattern = re.compile(r"(\w+)\s*=\s*((?:\([^()]*\)|[^(),]+))(?:,|\))")

# Extract arguments and values
arguments_matches = arguments_pattern.findall(globalLastOp)

# Create a list of alternating names and values
result_list = [item for sublist in arguments_matches for item in sublist]

if isModifier:
    # Convert to universal language: Name of op, value(s), target
    result_list = ["Modifier "+result_list[1], result_list[2], result_list[0]]

else:
    valuesDict = {result_list[i]: result_list[i + 1] for i in range(0, len(result_list), 2)}
    print(valuesDict)
    #result_list = [operator.name, valuesDict, bpy.context.active_object.name]

# print(result_list)

testedict = '''
{
    "MESH_OT_extrude_region": {
        "use_normal_flip":False,
        "use_dissolve_ortho_edges":False,
        "mirror":False
        },
    "TRANSFORM_OT_translate": {
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
'''

teste2 = '''
{
    "MESH_OT_extrude_region": {
        "use_normal_flip":false,
        "use_dissolve_ortho_edges":false,
        "mirror":false
        }
}
    '''

#####################################################################################################################################
######################################################## To bpy.ops #################################################################

teste3 = 'bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(3.72529e-09, 0, -0.288052), "orient_axis_ortho":"X", "orient_type":"NORMAL", "orient_matrix":((0.689899, 0.0450067, -0.722506), (0.715202, -0.196685, 0.670672), (-0.111921, -0.979433, -0.167882)), "orient_matrix_type":"NORMAL", "constraint_axis":(False, False, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":"SMOOTH", "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{"INCREMENT"}, "use_snap_project":False, "snap_target":"CLOSEST", "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})'

result = ""

# Removing all the characters before the first parenthesis
teste3 = teste3[teste3.index("(") + 1:-1]

# Some operations do not have properties (for example TODO: Edit mode)
if len(teste3) == 0:
    result = {}

else:
    # Picking all the parts divided by commas
    parts = teste3.split(",")

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

# print(result["TRANSFORM_OT_translate"]["value"])
    
#####################################################################################################################################
##################################################### To bpy.others #################################################################

'''
FORMATS:
[operator.name, valuesDict, bpy.context.active_object.name]


bpy.context.space_data.context = 'VIEW_LAYER'
bpy.context.scene.eevee.taa_render_samples = 64
bpy.context.scene.view_layers["ViewLayer"].use = False --> Name?
bpy.context.object.modifiers["Array"].count = 3
bpy.context.scene.world.mist_settings.start = 5


[bpy context space_data, {Group: , Subgroup: , propIndex: , others..., default_value (what comes before the = sign): }, bpy.context.active_object.name]

-----------------------------------------------------
bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (0.131279, 0.131279, 0.131279, 1) --> Group, Subgroup, propertyIndex, value?
bpy.data.materials["Material"].node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.513695, 0.513695, 0.513695, 1)
bpy.data.shape_keys["Key"].key_blocks["Key 1"].value = 0.104918
bpy.data.particles["ParticleSettings"].use_advanced_hair = True

[bpy data worlds node_tree nodes inputs, {Group: , Subgroup: , propIndex: , others..., default_value (what comes before the = sign): }, bpy.context.active_object.name]
'''


teste4 = 'bpy.data.shape_keys["Key"].key_blocks["Key 1"].value = 0.104918'
teste4 = 'bpy.data.materials["Material.001"].node_tree.nodes["Principled BSDF"].inputs[1].default_value = 0'


translated = [""]
# Get the first (because it might have more equal signs on the other side) occurrence of " = " to divide the 2 parts
teste4 = teste4.split(" = ", maxsplit=1)
# Get the value of the property
value = eval(teste4[1])
# List of names, groups etc and operation "address"
groupsList = [["group", ""], ["subgroup", ""], ["propIndex", ""]]
addresses = [""]
# Get all the operator "address"
teste4 = teste4[0].split(".")

groupIndex = 0

for i, addr in enumerate(teste4[:-1]): # Ignore the last one since it is the property name changed
    if "[" in addr:
        print("AAAAAAAA ", teste4)
        # Get what is inside: ['groupname']
        groupName = addr[addr.index("[")+1:addr.index("]")]
        groupName = eval(groupName)
        
        if groupIndex <= 2:
            groupsList[groupIndex][1] = groupName
        
        else:
            groupsList.append(["other"+str(groupIndex-2), groupName])

        groupIndex += 1

        # Get the address without the group name (also getting everything after it because there might be some operations that contains it)
        translated[0] = translated[0] + " " + addr[ 0 : addr.index("[") ] + addr[ addr.index("]")+1 : ]

    else:
        translated[0] = translated[0] + " " + addr

groupsList.append([teste4[-1], value])
translated.append(dict(groupsList))

print(translated)
