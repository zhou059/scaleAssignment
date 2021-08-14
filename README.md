<h1 align="center">Traffic Sign Image Audit Script</h1>
<p align="center">This python script detects the </p>



Additional future considerations can be found [here](https://docs.google.com/document/d/1BKpX0U7eqsFPwtqEx7-WqSt86RT5XMuZP2wPSH7qTkA/edit?usp=sharing)

USAGE
  $ python auditScaleProject.py -k <string> -p <string> -o <string> 

OPTIONS
  -k, --apikey=apikey                                                               Key for authenticating with Scale SDK

  -p, --projectname=projectname                                                     Project name that contains all the
                                                                                    traffic sign annotation tasks to audit

  -o, --outputfile=outputfile                                                       Output file to write the JSON report
                                                                                    containing all errors and warning
                                                                                    detected in the project tasks

EXAMPLE
  python auditScaleProject.py -k live_####################### -p "Traffic Sign Detection" -o ./output/results.json
  // For all tasks in the 'Traffic Sign Detection' project, detect errors and warnings and write results to the 
  // output/results.json file

## Maintainers
[Jonathan Zhou/zhou059](https://github.com/zhou059)
