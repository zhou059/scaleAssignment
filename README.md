<h1 align="center">Traffic Sign Image Audit Script</h1>
<p align="center">This python script detects possible lower quality bounding box annotations of traffic signs in a Scale project </p>

---

Accessing all tasks in a specified project, this python script will parse annotations and the image for all tasks to perform the following quality checks: 
* Bounding boxes are too small (under 5 pixels in length or width)
* Bounding boxes are too big (over 20% of the entire image)
* Bounding boxes are too thin (length or width over 15 times the other)
* Annotations should likely be truncated (0% truncated annotations near image border)
* Annotations that are entirely occluded (100% occluded annotations shouldn't be visible)
* Annotations that are entirely truncated (100% truncated annotations shouldn't be visible)
* Major color of pixels in bounding box do not match the annotated color (Most common color of pixels isn't the same as the annotated)

Additional future considerations for further development can be found [here](https://docs.google.com/document/d/1BKpX0U7eqsFPwtqEx7-WqSt86RT5XMuZP2wPSH7qTkA/edit?usp=sharing)

## Usage

  `python auditScaleProject.py -k <string> -p <string> -o <string>`

## Options
  
  -k, --apikey=apikey                                                               Key for authenticating with Scale SDK

  -p, --projectname=projectname                                                     Project name that contains all the
                                                                                    traffic sign annotation tasks to audit

  -o, --outputfile=outputfile                                                       Output file to write the JSON report
                                                                                    containing all errors and warning
                                                                                    detected in the project tasks

## Example
  python auditScaleProject.py -k live_####################### -p "Traffic Sign Detection" -o ./output/results.json
  // For all tasks in the 'Traffic Sign Detection' project, detect errors and warnings and write results to the 
  // output/results.json file

## Maintainers
[Jonathan Zhou/zhou059](https://github.com/zhou059)
