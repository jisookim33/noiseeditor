# Noise-Editor
The noise editor is a Maya tool for animators developed in python.  
  
<p align="center">
  <img align="center" height="500" src="https://github.com/user-attachments/assets/327ddf73-30e1-4588-b982-19681054a9a1">
</p>
  
## How it Works:
The backbone of the tool is based on the noise controller from 3dsMax that has been ported over to Maya as the `Shake` plug-in.  
  
<p align="center">
  <img align="center" height="400" src="https://github.com/user-attachments/assets/1fc7bae5-8117-44e2-ac98-f396d7268596">
</p>
  
## Requirements:
This tool requires the following python packages: [dcc](https://github.com/bhsingleton/dcc) and [mpy](https://github.com/bhsingleton/mpy).  
When downloading these packages from Github make sure to unzip the contents into the Maya scripts folder located inside your user documents folder.  
It is important to remove any prefixes from the unzipped folder name: `dcc-main` > `dcc`, otherwise the tools will fail to run!  
  
The following plug-ins are also required: [Shake](https://github.com/bhsingleton/Shake/releases) and [ComposeTransform](https://github.com/bhsingleton/ComposeTransform/releases).  
The tool will attempt to auto download the plug-ins for you but if want to manually install the plug-ins then read the following:
On the releases page locate the version of Maya you are using and download the the `.mll` file.  
Next, go to the Maya user documents location and locate the subfolder that matches the version of Maya you are using.  
Finally, move the downloaded `.mll` into a `plug-ins` folder. If no `plug-ins` folder exists then go ahead and create one!  
  
## How to Open:  
Run the following python code from either the script editor or from a shelf button:  
  
```
from noiseeditor.ui import qnoiseeditor

window = qnoiseeditor.QNoiseEditor()
window.show()
```
  
## Setup:
1. Select the controls you want to add noise to.  
2. Use the position, rotation and scale check boxes to specify which transform components will receive noise.
3. Click `Create` to add noise nodes to your selected controls.
  
Use the `Select` button to select all controls in the scene file with noise.  
Use the `Delete` button to remove noise from your selected controls.  
  
## Properties:
Use the position, rotation and scale radio buttons to specify which noise components to edit on the active selection.  
  
- `Seed`:  The seed ID used to generate the noise calculations. Changing the seed ID creates a new noise curve.  
- `Frequency`: Controls the peaks and valleys of the noise curve. The useful range is from 0.01 to 1.0. High values create jagged, heavily oscillating noise curves. Low values create soft, gentle noise curves.  
- `Fractal Noise`:  Generates noise using a `Fractal Brownian Motion`. The main value of using `Fractal Noise` is that it activates the `Roughness` field.  
- `Envelope`:  Acts as an alpha mask to blend the overall effect of the noise.  
- `Roughness`: Changes the roughness of the Noise curve (when `Fractal Noise` is turned on). Where `Frequency` sets the smoothness of the overall noise effect, `Roughness` changes the smoothness of the noise curve itself.  
- `Ramp Out`:  Sets the amount of time noise takes to build to full strength. A value of 0 causes noise to start immediately at full strength at the beginning of the timeline.
- `Ramp Out`:  Sets the amount of time noise takes to fall to zero strength. A value of 0 causes noise to stop immediately at the end of the timeline.
- `XYZ Strength`:  Sets the value range for noise output. These values can be animated.  
- `XYZ Positive`:  Forces noise values to stay positive. Each `Strength` field has its own >0 constraint. 
  
## Baking:
Select the controls you want to bake.  
  
1. Enter the start and end frame to bake. Right clicking the up and down arrows will reset the spin box to your current time range!  
2. Next, enter a frame step to control the bake rate. Using a value of 1 will result in key per frame bakes!  
3. Finally, click `Bake` to bake the noise onto the active animation layer. Once the bake is complete the noise nodes will be removed from your controls.  
