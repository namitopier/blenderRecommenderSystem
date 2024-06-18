# This script is meant to calculate the tf-idf of all tutorials of the recommender system
import os
import numpy as np
import json

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
    print("TUTORIAL = ", tutorial)
    for term in globalOps:
        print("TERM = ", term)
        print("OPERATIONS IN THIS TUTORIAL: ", list(tutorial["operations"].keys()))

        if term in list(tutorial["operations"].keys()):

             # Frequency of term in the current document
            f = tutorial["operations"][term]
            print("     TERM FREQUENCY ", f)

            # Max frequency among all terms in the document
            maxf = np.max(list(tutorial["operations"].values()))
            print("     MAX FREQUENCY ", maxf)

            # Number of tutorials where term occurs at least once
            nk = 0
            for tut in tutorials:
                if term in list(tut["operations"].keys()):
                    nk += 1
            print("     TUTORIALS WITH TERM ", nk)
            print("     N ", N)
            
            # Calculating TF:
            tf = f/maxf
            print("     TF ", tf)

            # Calculating IDF (I add 1 to N because since the dataset is small and also
            # it is expected that all tutorials have some terms in common, it wont
            # result in 0, resulting in over penalization):
            idf = np.log10(( (N+1 if N == nk else N)/nk ))
            print("     IDF ", idf)

            # Calculating TF-IDF:
            tf_idf = tf*idf
            print("     TF-IDF ", tf_idf)

        else:
            tf_idf = 0

        tutorial["weights"].append(tf_idf)
        
        print("CALCULATED WEIGHT: ", tf_idf)
        # print("FINAL WEIGHTS = ", tutorial["weights"])

    # Normalizing the weights - LNCS 4321:
    tutorial["weights"] = np.divide(tutorial["weights"], np.sqrt(np.sum(np.square(tutorial["weights"]))))


# Helper function to format the final result dict
def formatFinalDict(tutList, allTerms):
    # tutList is the list of all the tutorials with their term weights
    # allTerms is the list containing all the terms found in the correct order

    finalDict = {"allTerms" : allTerms,
                 "allTutorials" : {}}

    for tutInfo in tutList:
        name = tutInfo["name"]
        weights = tutInfo["weights"].tolist()

        finalDict["allTutorials"][name] = weights

    return finalDict

completeDict = formatFinalDict(tutorials, globalOps)

# Creating the file with all the tf-idf calculated
file_name = 'termWeights.txt'
file_path = os.path.join(tutorials_path, file_name)

# Write the dictionary to the text file
with open(file_path, 'w') as file:
    json.dump(completeDict, file)










# termsDict = {}

# # Read the dictionary containing all the calculated weights
# with open(file_path, 'r') as file:
#     termsDict = json.load(file)

# print(termsDict["allTerms"])