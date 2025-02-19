# noiseeditor
A Maya python based auto secondary tool for animators.  

## Requirements:
This tool requires the following PIP installs: Qt.py, six, numpy and scipy.  
On top of the following python packages: [dcc](https://github.com/bhsingleton/dcc) and [mpy](https://github.com/bhsingleton/mpy).   

## Installing the PIP Dependencies
To install the required pip dependencies open a Command Prompt window.  
In this example I will be using Maya 2024. Be sure to adjust your code to whichever version of Maya you are using.  
Change the current working directory using:  
> cd %PROGRAMFILES%\Autodesk\Maya2024\bin  

Make sure you have pip installed using:  
> mayapy.exe -m ensurepip --upgrade --user  

Now you can install the necessary dependencies using:  
> mayapy.exe -m pip install Qt.py --user  

## How to open:

```
from noiseeditor.ui import qnoiseeditor

window = qnoiseeditor.QNoiseEditor()
window.show()
```
