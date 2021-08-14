import scaleapi
from PIL import Image
import requests
import json
import operator
import sys, getopt

def main(argv):
    # Input parameters
    apiKey = "live_c3cec48826bc4476a0e5034712f4335c"
    projectName = "Traffic Sign Detection"
    outputFile="./results.json"

    # Collection of issues to be included in the final output
    issues = []
    # Initial dict to be converted to JSON for output, issues to be appended
    report = {"project_name" : projectName, "description" : "Audit report of all bounding box annotations for tasks in identified project"}

    # Parse parameters to get API key, project name and output file name
    try:
        opts, args = getopt.getopt(argv,"hk:p:o:",["apikey=","project name=","output file="])
    except getopt.GetoptError:
        print('auditScaleProject.py -k <api key> -p <project name> -o <output file>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('auditScaleProject.py -k <api key> -p <project name> -o <output file>')
            sys.exit()
        elif opt in ("-k", "--apikiey"):
            apiKey = arg
        elif opt in ("-p", "--project"):
            projectName = arg
        elif opt in ("-o", "--outputfile"):
            outputFile = arg

    client = scaleapi.ScaleClient(apiKey)               # Connect with ScaleAI SDK
    tasks = client.get_tasks(project_name=projectName)  # Grab all tasks in the project

    # For each task in the project, run an audit to identify warnings and errors
    for task in tasks:
        issues += auditTask(task)
    
    # Add all errors and warning to output dict and write to output file as JSON
    report["issues"] = issues
    f = open(outputFile, "w")
    f.write(json.dumps(report, indent = 4)  )
    f.close()

# For a given task, extract image and annotations to run a set of audit tests against and return results
def auditTask (task):
    issues = []                                         # List of issues detected for annotations
    taskId = task.task_id                              # Grabs the task ID to be included with any logged issues
    annotations = task.response["annotations"]          # Get list of annotations from task

    # Download the image and get its size
    url = task.params["attachment"]
    im = Image.open(requests.get(url, stream=True).raw)
    width, height = im.size

    # Run through list of annotations and quality checks for each
    for anttn in annotations: 
        # Grab pixels of the bounding box
        boxPixels = im.crop((anttn["left"], anttn["top"], anttn["left"]+anttn["width"], anttn["top"]+anttn["height"])).load()

        # Run through all audit jobs and include error/warning in issues list if detected
        issues += filter(None, [checkIfTooSmall(taskId, anttn)])
        issues += filter(None, [checkIfTooBig(taskId, anttn, width, height)])
        issues += filter(None, [checkIfTooThin(taskId, anttn)])
        issues += filter(None, [checkIfPossibleToBeTruncated(taskId, anttn, width, height)])
        issues += filter(None, [checkIfTotallyTruncated(taskId, anttn)])
        issues += filter(None, [checkIfTotallyOccluded(taskId, anttn)])
        if(anttn["attributes"]["background_color"] not in ["other", "not_applicable"]): 
            issues += filter(None, [checkIfMinorityColor(taskId, anttn, boxPixels, anttn["width"], anttn["height"])])
        
    return issues

# Checks if the bounding box was too small to be actually discernable
def checkIfTooSmall(taskId, annotation): 
    # If the bounding box is too small (width or height), its too difficult to discern the sign anyways and would be a low quality sign image
    if annotation["width"] <= 5 or annotation["height"] <= 5:
        return {"task_id": taskId, "annotation_id": annotation["uuid"], "type" : "Error", "code" : "1001", 
                "description": "The bounding box is too small"}

# Checks if the bounding box was too small to be actually discernable
def checkIfTooBig(taskId, annotation, width, height): 
    # If the bounding box is at least 20% of the entire image, return warning
    if 5 * annotation["width"] * annotation["height"] > width * height:
        return {"task_id": taskId, "annotation_id": annotation["uuid"], "type" : "Warning", "code" : "2001", 
                "description": "The bounding box is over 20% of the image, recommend to check if accurate"}

# Checks if the bounding box was too thing to be actually discernable
def checkIfTooThin(taskId, annotation): 
    # If the width or height is over 15 times the other, return warning
    if 15 * annotation["width"] < annotation["height"] or 15 * annotation["height"] < annotation["width"]:
        return {"task_id": taskId, "annotation_id": annotation["uuid"], "type" : "Warning", "code" : "2002", 
                "description": "The bounding box is too thin"}

# Used by the color job to calculate the closed color by using the manhattan distance between a pixel and the colors
def classify(rgb_tuple):
    # RGB definitions for our colors options
    colors = {"red": (255, 0, 0),
              "green" : (0,255,0),
              "white" : (255,255,255),
              "orange" : (255,165,0),
              "yellow" : (255,255,0),
              "green" : (0,128,0),
              "blue" : (0,0,255),
             }

    # Calculate the manhattan distance and return the color with the minimal distance
    manhattan = lambda x,y : abs(x[0] - y[0]) + abs(x[1] - y[1]) + abs(x[2] - y[2]) 
    distances = {k: manhattan(v, rgb_tuple) for k, v in colors.items()}
    color = min(distances, key=distances.get)

    return color

# Checks if the main color of the pixels in the bounding box match the annotated color
def checkIfMinorityColor(taskId, annotation, pixels, width, height): 
    # Initialize pixel color counter
    counter = {"red" : 0, "green" : 0, "white" : 0, "orange": 0, "yellow" : 0, "green" : 0, "blue" : 0}
    # Grab the color identified in the task
    color = annotation["attributes"]["background_color"]

    # Run through all pixels in the bounding box and guess the closest color of the pixel
    for x in range(width): 
        for y in range(height): 
            counter[classify(pixels[x,y])] += 1

    # Identifiy the color with the most pixels in the bounding box
    mainColor = max(counter.items(), key=operator.itemgetter(1))[0]
    # print(json.dumps(counter, indent = 4))
    # print(mainColor + " | " + color)

    # If the color with the most pixels does not match the annotated color, return warning
    if (mainColor != color):
        return {"task_id": taskId, "annotation_id": annotation["uuid"], "type" : "Warning", "code" : "2003", 
                "description": "The main color detected was not " + color + ", but " + mainColor + " instead"}

# If bounding box is very close to the border of the image, but wasn't identified as being truncated, raise a warning
def checkIfPossibleToBeTruncated(taskId, annotation, maxWidth, maxHeight): 
    # If full sign is in image (not truncated), but bounding box is within 3 pixels of a border, return warning
    if (annotation["attributes"]["truncation"] == "0%" and (annotation["left"] <= 3 or
                                                            annotation["top"] <= 3 or
                                                            annotation["left"] + annotation["width"] + 3 >= maxWidth or
                                                            annotation["top"] + annotation["height"] + 3 >= maxHeight) ): 
        return {"task_id": taskId, "annotation_id": annotation["uuid"], "type" : "Warning", "code" : "2004", 
            "description": "It is likely that this sign should be annotated as partially truncated"}

# A totally truncated sign is theoretically not visible at all and not relevant
def checkIfTotallyTruncated(taskId, annotation): 
    # Any annotation that is 100% truncated is not visible, so return error
    if (annotation["attributes"]["truncation"] == "100%"):
        return {"task_id": taskId, "annotation_id": annotation["uuid"], "type" : "Error", "code" : "1002", 
            "description": "A sign cannot be 100% truncated since that means it wouldn't be within the image"}

# A totally occluded sign is theoretically not visible at all and not relevant
def checkIfTotallyOccluded(taskId, annotation): 
    # Any annotation that is 100% occluded is not visible, so return error
    if (annotation["attributes"]["occlusion"] == "100%"):
        return {"task_id": taskId, "annotation_id": annotation["uuid"], "type" : "Error", "code" : "1003", 
            "description": "A sign cannot be 100% occluded, since that means it wouldn't be visible"}

if __name__ == "__main__":
   main(sys.argv[1:])