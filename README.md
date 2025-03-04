# Noise-Editor
A Maya python based noise tool for animators.  

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
