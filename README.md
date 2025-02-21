# Noise-Editor
A Maya python based noise tool for animators.  

## Requirements:
This tool requires the following python packages: [dcc](https://github.com/bhsingleton/dcc) and [mpy](https://github.com/bhsingleton/mpy).   
The following plug-ins are also required: [Shake](https://github.com/bhsingleton/Shake) and [ComposeTransform](https://github.com/bhsingleton/ComposeTransform).
  
## How to open:
Run the following python code from the script editor or from a shelf button:  
  
```
from noiseeditor.ui import qnoiseeditor

window = qnoiseeditor.QNoiseEditor()
window.show()
```
