# Noise-Editor
The noise editor is a Maya tool for animators developed in python.  
The backbone of the tool is based on the noise controller from 3dsMax that has been ported over to Maya as the `Shake` plug-in.  
  
<p align="center">
  <img align="center" height="400" src="https://github.com/user-attachments/assets/327ddf73-30e1-4588-b982-19681054a9a1">
  <img align="center" height="400" src="https://github.com/user-attachments/assets/1fc7bae5-8117-44e2-ac98-f396d7268596">
</p>

## Requirements:
This tool requires the following python packages: [dcc](https://github.com/bhsingleton/dcc) and [mpy](https://github.com/bhsingleton/mpy).  
When downloading these packages from Github make sure to unzip the contents into the Maya scripts folder located inside your user documents folder.  
It is important to remove any prefixes from the unzipped folder name: `dcc-main` > `dcc`, otherwise the tools will fail to run!  
  
The following plug-ins are also required: [Shake](https://github.com/bhsingleton/Shake/releases/tag/1.0) and [ComposeTransform](https://github.com/bhsingleton/ComposeTransform/releases/tag/1.0).  
Unzip the release files and copy the `.mll` file that matches the version of Maya you are using.  
Next, go to the Maya user documents location and locate the subfolder that matches the version of Maya you are using.  
Finally, paste the `.mll` into a `plug-ins` folder. If no `plug-ins` folder exists then go ahead and create one!
  
## How to open:
Run the following python code from the script editor or from a shelf button:  
  
```
from noiseeditor.ui import qnoiseeditor

window = qnoiseeditor.QNoiseEditor()
window.show()
```
