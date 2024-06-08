# This script is meant to calculate the tf-idf of all tutorials of the recommender system
import os
import numpy as np

# Tutorials list
tutorials = []

# Global list containing all the operations in the tutorials
globalOps = []

# Get the path to the folder containing the tutorials
tutorials_path = os.path.join(os.path.dirname(__file__), 'blenderProject') 

# List all files in the folder
file_names = os.listdir(tutorials_path)

# Filtering tutorials by initial letters: "TUT"
tut_files = [file_name for file_name in file_names if file_name.startswith("TUT")]

# Read content line by line for each file
for i, file_name in enumerate(tut_files):
    file_path = os.path.join(tutorials_path, file_name)
    
    # Dictionary containing all the information of current tutorial
    tutDict = {"name" : file_name,
               "operations": {},
               "weights": []}

    with open(file_path, 'r') as file:
        for line in file:
            operationName = eval(line.strip())[0]

            if operationName not in tutDict["operations"]:
                tutDict["operations"][operationName] = 1
            else:
                tutDict["operations"][operationName] += 1

            if operationName not in globalOps:
                globalOps.append(operationName)
    
    tutorials.append(tutDict)



# Number of tutorials considered
N = len(tutorials)

for tutorial in tutorials:
    for term in globalOps:
        if term in list(tutorial["operations"].keys()):
             # Frequency of term in the current document
            f = tutorial["operations"][term]

            # Max frequency among all terms in the document
            maxf = np.max(list(tutorial["operations"].values()))

            # Number of tutorials where term occurs at least once
            nk = 0
            for tut in tutorials:
                if term in list(tut["operations"].keys()):
                    nk += 1
            
            # Calculating TF:
            tf = f/maxf

            # Calculating IDF:
            idf = np.log10((N/nk))

            # Calculating TF-IDF:
            tf_idf = tf*idf

        else:
            tf_idf = 0

        tutorial["weights"].append(tf_idf)

    # Normalizing the weights:
    tutorial["weights"] = np.divide(tutorial["weights"], np.sqrt(np.sum(np.square(tutorial["weights"]))))

    # for term in list(tutorial["operations"].keys()):

    #     # Frequency of term in the current document
    #     f = tutorial["operations"][term]

    #     # Max frequency among all terms in the document
    #     maxf = np.max(list(tutorial["operations"].values()))

    #     # Number of tutorials where term occurs at least once
    #     nk = 0
    #     for tut in tutorials:
    #         if term in list(tut["operations"].keys()):
    #             nk += 1
        
    #     # Calculating TF:
    #     tf = f/maxf

    #     # Calculating IDF:
    #     idf = np.log10((N/nk))

    #     # Calculating TF-IDF:
    #     tf_idf = tf*idf

print(tutorials)

'''

desired = ['Extrude to Cursor or Add', {'rotate_source': True, 'newVertices': [8, 9, 10, 11], 'newFaces': [6, 7, 8, 9], 'vertices': {0: [0.8783648610115051, 1.0, 0.9925748705863953], 1: [1.1216351985931396, 1.0, -0.9925748705863953], 2: [0.8783648610115051, -1.0, 0.9925748705863953], 3: [1.1216351985931396, -1.0, -0.9925748705863953], 4: [-1.0, 1.0, 1.0], 5: [-1.0, 1.0, -1.0], 6: [-1.0, -1.0, 1.0], 7: [-1.0, -1.0, -1.0], 8: [3.5378735065460205, 0.9999998807907104, 1.6619833707809448], 9: [4.020801544189453, 0.9999998807907104, -0.2788362503051758], 10: [3.5378735065460205, -1.0000001192092896, 1.6619833707809448], 11: [4.020801544189453, -1.0000001192092896, -0.2788362503051758]}, 'editMode': True}, 'Cube', {}]
performed = ['Extrude to Cursor or Add', {'rotate_source': True, 'newVertices': [8, 9, 10, 11], 'newFaces': [6, 7, 8, 9], 'vertices': {0: [0.8783648610115051, 1.0, 0.9925748705863953], 1: [1.1216351985931396, 1.0, -0.9925748705863953], 2: [0.8783648610115051, -1.0, 0.9925748705863953], 3: [1.1216351985931396, -1.0, -0.9925748705863953], 4: [-1.0, 1.0, 1.0], 5: [-1.0, 1.0, -1.0], 6: [-1.0, -1.0, 1.0], 7: [-1.0, -1.0, -1.0], 8: [3.5378735065460205, 0.9999998807907104, 1.6619833707809448], 9: [4.020801544189453, 0.9999998807907104, -0.2788362503051758], 10: [3.5378735065460205, -1.0000001192092896, 1.6619833707809448], 11: [4.020801544189453, -1.0000001192092896, -0.2788362503051758]}, 'editMode': True}, 'Cube', {}]
tolerance = 10

def validateValues(structure, structureCompare, structureType, tolerance):
    hadBreak = False
    if structureType == dict:
        for key in list(structure.keys()):
            value = structure[key]
            if type(value) != float and type(value) != int:
                if validateValues(value, structureCompare[key], type(value), tolerance) == False:
                    return False
            elif type(value) == float:
                valueCompare = structureCompare[key]
                if not (value == valueCompare or (value >= valueCompare*(1-tolerance) and value <= valueCompare*(1+tolerance))):
                    return False
                
    elif structureType == list or structureType == tuple:
        for i, value in enumerate(structure):
            if type(value) != float and type(value) != int:
                if validateValues(value, structureCompare[i], type(value), tolerance) == False:
                    return False
            elif type(value) == float:
                valueCompare = structureCompare[i]
                if not (value == valueCompare or (value >= valueCompare*(1-tolerance) and value <= valueCompare*(1+tolerance))):
                    return False
                
    if hadBreak:
        return False
    else:
        return True
        
#print(validateValues({0: [2.8, 1.0, 0.9], 1: [4.8, 2.0, 1.9]}, {0: [2.8, 1.0, 0.9], 1: [3.8, 2.0, 1.9]}, dict, tolerance/100))
print(validateValues(desired, performed, list, tolerance/100))
        
print(validateValues({0: [2.8, 1.0, 0.9], 1: [4.8, 2.0, 1.9]}, {0: [2.8, 1.0, 0.9], 1: [3.8, 2.0, 1.9]}, dict, tolerance/100))
'''