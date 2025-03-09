import random

from maya import cmds as mc
from maya.api import OpenMaya as om
from mpy import mpyscene, mpynode
from collections import namedtuple
from dcc.generators.inclusiverange import inclusiveRange
from dcc.maya.libs import plugutils
from dcc.maya.decorators import animate, undo
from dcc.ui import qsingletonwindow, qtimespinbox
from dcc.vendor.Qt import QtCore, QtWidgets, QtGui, QtCompat
from .widgets import qnoisegraph
from ..libs import noiseutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


NoiseItem = namedtuple('NoiseItem', ('node', 'transform', 'position', 'rotation', 'scale'))


def onSelectionChanged(*args, **kwargs):
    """
    Callback method for any selection changes.

    :rtype: None
    """

    # Check if instance exists
    #
    instance = QNoiseEditor.getInstance()

    if instance is None:

        return

    # Evaluate if instance is still valid
    #
    if QtCompat.isValid(instance):

        instance.selectionChanged(*args, **kwargs)

    else:

        log.warning('Unable to process selection changed callback!')


class QNoiseEditor(qsingletonwindow.QSingletonWindow):
    """
    Overload of `QUicWindow` that interfaces with noise nodes.
    """

    # region Dunderscores
    __ids__ = (2, 3, 4)
    __patterns__ = ('*:_Ctrl_*', '*:*_CTRL')
    __plugins__ = ('Shake', 'ComposeTransform')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key parent: QtWidgets.QWidget
        :key flags: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        super(QNoiseEditor, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._scene = mpyscene.MPyScene.getInstance(asWeakReference=True)
        self._callbackIds = om.MCallbackIdArray()

    def __post_init__(self, *args, **kwargs):
        """
        Private method called after an instance has initialized.

        :rtype: None
        """

        # Call parent method
        #
        super(QNoiseEditor, self).__post_init__(*args, **kwargs)

        # Load required plugins
        #
        self.loadPlugins()

    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        # Call parent method
        #
        super(QNoiseEditor, self).__setup_ui__(self, *args, **kwargs)

        # Initialize main window
        #
        self.setWindowTitle("|| Noise Editor")
        self.setMinimumSize(QtCore.QSize(400, 575))

        # Initialize central widget
        #
        centralLayout = QtWidgets.QVBoxLayout()
        centralLayout.setObjectName('centralLayout')

        centralWidget = QtWidgets.QWidget()
        centralWidget.setObjectName('centralWidget')
        centralWidget.setLayout(centralLayout)

        self.setCentralWidget(centralWidget)

        # Initialize setup widgets
        #
        self.createLayout = QtWidgets.QHBoxLayout()
        self.createLayout.setObjectName('createLayout')

        self.createWidget = QtWidgets.QWidget()
        self.createWidget.setObjectName('createWidget')
        self.createWidget.setLayout(self.createLayout)
        self.createWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.createWidget.setFixedHeight(35)

        self.posCheckBox = QtWidgets.QCheckBox('Pos')
        self.posCheckBox.setObjectName('posCheckBox')
        self.posCheckBox.setChecked(True)
        self.posCheckBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred))
        self.posCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)

        self.rotCheckBox = QtWidgets.QCheckBox('Rot')
        self.rotCheckBox.setObjectName('rotCheckBox')
        self.rotCheckBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred))
        self.rotCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)

        self.scaleCheckBox = QtWidgets.QCheckBox('Scale')
        self.scaleCheckBox.setObjectName('scaleCheckBox')
        self.scaleCheckBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred))
        self.scaleCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)

        self.createLayout.addWidget(self.posCheckBox)
        self.createLayout.addWidget(self.rotCheckBox)
        self.createLayout.addWidget(self.scaleCheckBox)

        self.createPushButton = QtWidgets.QPushButton('Create')
        self.createPushButton.setObjectName('createPushButton')
        self.createPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.createPushButton.setFixedHeight(35)
        self.createPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.createPushButton.clicked.connect(self.on_createPushButton_clicked)

        self.setupDivider = QtWidgets.QFrame()
        self.setupDivider.setObjectName('setupDivider')
        self.setupDivider.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding))
        self.setupDivider.setFrameShape(QtWidgets.QFrame.VLine)
        self.setupDivider.setFrameShadow(QtWidgets.QFrame.Sunken)

        self.selectPushButton = QtWidgets.QPushButton('Select')
        self.selectPushButton.setObjectName('selectPushButton')
        self.selectPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.selectPushButton.setFixedHeight(35)
        self.selectPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.selectPushButton.clicked.connect(self.on_selectPushButton_clicked)

        self.deletePushButton = QtWidgets.QPushButton('Delete')
        self.deletePushButton.setObjectName('deletePushButton')
        self.deletePushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.deletePushButton.setFixedHeight(35)
        self.deletePushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.deletePushButton.clicked.connect(self.on_deletePushButton_clicked)

        # Initialize setup group-box
        #
        self.setupLayout = QtWidgets.QGridLayout()
        self.setupLayout.setObjectName('setupLayout')

        self.setupGroupBox = QtWidgets.QGroupBox('Setup:')
        self.setupGroupBox.setObjectName('setupGroupBox')
        self.setupGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.setupGroupBox.setLayout(self.setupLayout)

        self.setupLayout.addWidget(self.createWidget, 0, 0)
        self.setupLayout.addWidget(self.createPushButton, 1, 0)
        self.setupLayout.addWidget(self.setupDivider, 0, 1, 2, 1)
        self.setupLayout.addWidget(self.selectPushButton, 0, 2)
        self.setupLayout.addWidget(self.deletePushButton, 1, 2)

        centralLayout.addWidget(self.setupGroupBox)

        # Initialize component widget
        #
        self.filterLayout = QtWidgets.QHBoxLayout()
        self.filterLayout.setObjectName('filterLayout')
        self.filterLayout.setContentsMargins(0, 0, 0, 0)

        self.filterWidget = QtWidgets.QWidget()
        self.filterWidget.setObjectName('componentWidget')
        self.filterWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.filterWidget.setFixedHeight(24)
        self.filterWidget.setLayout(self.filterLayout)

        self.positionRadioButton = QtWidgets.QRadioButton('Position')
        self.positionRadioButton.setObjectName('positionRadioButton')
        self.positionRadioButton.setChecked(True)
        self.positionRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred))
        self.positionRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.rotationRadioButton = QtWidgets.QRadioButton('Rotation')
        self.rotationRadioButton.setObjectName('rotationRadioButton')
        self.rotationRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred))
        self.rotationRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.scaleRadioButton = QtWidgets.QRadioButton('Scale')
        self.scaleRadioButton.setObjectName('scaleRadioButton')
        self.scaleRadioButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred))
        self.scaleRadioButton.setFocusPolicy(QtCore.Qt.NoFocus)

        positionId, rotationId, scaleId = self.__ids__

        self.radioButtonGroup = QtWidgets.QButtonGroup(self.filterWidget)
        self.radioButtonGroup.setExclusive(True)
        self.radioButtonGroup.addButton(self.positionRadioButton, id=positionId)
        self.radioButtonGroup.addButton(self.rotationRadioButton, id=rotationId)
        self.radioButtonGroup.addButton(self.scaleRadioButton, id=scaleId)
        self.radioButtonGroup.idClicked.connect(self.on_radioButtonGroup_idClicked)

        self.filterLayout.addWidget(self.positionRadioButton, alignment=QtCore.Qt.AlignHCenter)
        self.filterLayout.addWidget(self.rotationRadioButton, alignment=QtCore.Qt.AlignHCenter)
        self.filterLayout.addWidget(self.scaleRadioButton, alignment=QtCore.Qt.AlignHCenter)

        # Initialize interop widget
        #
        self.interopLayout = QtWidgets.QGridLayout()
        self.interopLayout.setObjectName('interopLayout')
        self.interopLayout.setContentsMargins(0, 0, 0, 0)

        self.interopWidget = QtWidgets.QWidget()
        self.interopWidget.setObjectName('interopWidget')
        self.interopWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.interopWidget.setLayout(self.interopLayout)

        self.randomizeSeedPushButton = QtWidgets.QPushButton('Random Seed')
        self.randomizeSeedPushButton.setObjectName('randomizeSeedPushButton')
        self.randomizeSeedPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.randomizeSeedPushButton.setFixedHeight(24)
        self.randomizeSeedPushButton.clicked.connect(self.on_randomizeSeedPushButton_clicked)

        self.seedSpinBox = QtWidgets.QSpinBox()
        self.seedSpinBox.setObjectName('seedSpinBox')
        self.seedSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.seedSpinBox.setFixedHeight(24)
        self.seedSpinBox.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.seedSpinBox.setMinimum(0)
        self.seedSpinBox.setMaximum(100)
        self.seedSpinBox.setSingleStep(1)
        self.seedSpinBox.setValue(0)
        self.seedSpinBox.setWhatsThis('seed')
        self.seedSpinBox.valueChanged.connect(self.on_seedSpinBox_valueChanged)

        self.frequencyLabel = QtWidgets.QLabel('Frequency:')
        self.frequencyLabel.setObjectName('frequencyLabel')
        self.frequencyLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.frequencyLabel.setFixedSize(QtCore.QSize(70, 24))
        self.frequencyLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.frequencySpinBox = QtWidgets.QDoubleSpinBox()
        self.frequencySpinBox.setObjectName('frequencySpinBox')
        self.frequencySpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.frequencySpinBox.setFixedHeight(24)
        self.frequencySpinBox.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.frequencySpinBox.setDecimals(3)
        self.frequencySpinBox.setMinimum(0.001)
        self.frequencySpinBox.setMaximum(10.0)
        self.frequencySpinBox.setSingleStep(0.005)
        self.frequencySpinBox.setValue(5.0)
        self.frequencySpinBox.setWhatsThis('frequency')
        self.frequencySpinBox.valueChanged.connect(self.on_frequencySpinBox_valueChanged)

        self.fractalNoiseCheckBox = QtWidgets.QCheckBox('Fractal Noise')
        self.fractalNoiseCheckBox.setObjectName('fractalNoiseCheckBox')
        self.fractalNoiseCheckBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.fractalNoiseCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.fractalNoiseCheckBox.setChecked(True)
        self.fractalNoiseCheckBox.setWhatsThis('fractal')
        self.fractalNoiseCheckBox.stateChanged.connect(self.on_fractalNoiseCheckBox_stateChanged)

        self.envelopeLabel = QtWidgets.QLabel('Envelope:')
        self.envelopeLabel.setObjectName('envelopeLabel')
        self.envelopeLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.envelopeLabel.setFixedSize(QtCore.QSize(70, 24))
        self.envelopeLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.envelopeSpinBox = QtWidgets.QDoubleSpinBox()
        self.envelopeSpinBox.setObjectName('envelopeSpinBox')
        self.envelopeSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.envelopeSpinBox.setFixedHeight(24)
        self.envelopeSpinBox.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.envelopeSpinBox.setDecimals(1)
        self.envelopeSpinBox.setMinimum(0.0)
        self.envelopeSpinBox.setMaximum(1.0)
        self.envelopeSpinBox.setSingleStep(0.1)
        self.envelopeSpinBox.setValue(1.0)
        self.envelopeSpinBox.setWhatsThis('envelope')
        self.envelopeSpinBox.valueChanged.connect(self.on_envelopeSpinBox_valueChanged)

        self.roughnessLabel = QtWidgets.QLabel('Roughness:')
        self.roughnessLabel.setObjectName('roughnessLabel')
        self.roughnessLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.roughnessLabel.setFixedSize(QtCore.QSize(70, 24))
        self.roughnessLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.roughnessSpinBox = QtWidgets.QDoubleSpinBox()
        self.roughnessSpinBox.setObjectName('roughnessSpinBox')
        self.roughnessSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.roughnessSpinBox.setFixedHeight(24)
        self.roughnessSpinBox.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.roughnessSpinBox.setDecimals(2)
        self.roughnessSpinBox.setMinimum(0.0)
        self.roughnessSpinBox.setMaximum(1.0)
        self.roughnessSpinBox.setSingleStep(0.1)
        self.roughnessSpinBox.setValue(0.5)
        self.roughnessSpinBox.setWhatsThis('roughness')
        self.roughnessSpinBox.valueChanged.connect(self.on_roughnessSpinBox_valueChanged)

        self.rampInLabel = QtWidgets.QLabel('Ramp-In:')
        self.rampInLabel.setObjectName('rampInLabel')
        self.rampInLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.rampInLabel.setFixedSize(QtCore.QSize(70, 24))
        self.rampInLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.rampInSpinBox = QtWidgets.QDoubleSpinBox()
        self.rampInSpinBox.setObjectName('rampInSpinBox')
        self.rampInSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.rampInSpinBox.setFixedHeight(24)
        self.rampInSpinBox.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.rampInSpinBox.setDecimals(2)
        self.rampInSpinBox.setMinimum(0.0)
        self.rampInSpinBox.setMaximum(10000.0)
        self.rampInSpinBox.setSingleStep(0.01)
        self.rampInSpinBox.setValue(0.0)
        self.rampInSpinBox.setWhatsThis('rampIn')
        self.rampInSpinBox.valueChanged.connect(self.on_rampInSpinBox_valueChanged)

        self.rampOutLabel = QtWidgets.QLabel('Ramp-Out:')
        self.rampOutLabel.setObjectName('rampOutLabel')
        self.rampOutLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.rampOutLabel.setFixedSize(QtCore.QSize(70, 24))
        self.rampOutLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.rampOutSpinBox = QtWidgets.QDoubleSpinBox()
        self.rampOutSpinBox.setObjectName('rampOutSpinBox')
        self.rampOutSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.rampOutSpinBox.setFixedHeight(24)
        self.rampOutSpinBox.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.rampOutSpinBox.setDecimals(2)
        self.rampOutSpinBox.setMinimum(0.0)
        self.rampOutSpinBox.setMaximum(10000.0)
        self.rampOutSpinBox.setSingleStep(0.01)
        self.rampOutSpinBox.setValue(0.0)
        self.rampOutSpinBox.setWhatsThis('rampOut')
        self.rampOutSpinBox.valueChanged.connect(self.on_rampOutSpinBox_valueChanged)

        self.xStrengthLabel = QtWidgets.QLabel('X-Strength:')
        self.xStrengthLabel.setObjectName('xStrengthLabel')
        self.xStrengthLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.xStrengthLabel.setFixedSize(QtCore.QSize(70, 24))
        self.xStrengthLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.xStrengthLayout = QtWidgets.QHBoxLayout()
        self.xStrengthLayout.setObjectName('xStrengthLayout')
        self.xStrengthLayout.setContentsMargins(0, 0, 0, 0)

        self.xStrengthWidget = QtWidgets.QWidget()
        self.xStrengthWidget.setObjectName('xStrengthWidget')
        self.xStrengthWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.xStrengthWidget.setFixedHeight(24)
        self.xStrengthWidget.setLayout(self.xStrengthLayout)

        self.xStrengthSpinBox = QtWidgets.QDoubleSpinBox()
        self.xStrengthSpinBox.setObjectName('xStrengthSpinBox')
        self.xStrengthSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred))
        self.xStrengthSpinBox.setFixedHeight(24)
        self.xStrengthSpinBox.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.xStrengthSpinBox.setDecimals(2)
        self.xStrengthSpinBox.setMinimum(0.0)
        self.xStrengthSpinBox.setMaximum(10000.0)
        self.xStrengthSpinBox.setSingleStep(0.01)
        self.xStrengthSpinBox.setValue(5.0)
        self.xStrengthSpinBox.setWhatsThis('strengthX')
        self.xStrengthSpinBox.valueChanged.connect(self.on_xStrengthSpinBox_valueChanged)

        self.posXCheckBox = QtWidgets.QCheckBox('>0')
        self.posXCheckBox.setObjectName('posXCheckBox')
        self.posXCheckBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred))
        self.posXCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.posXCheckBox.setWhatsThis('positiveX')
        self.posXCheckBox.stateChanged.connect(self.on_posXCheckBox_stateChanged)

        self.xStrengthLayout.addWidget(self.xStrengthSpinBox)
        self.xStrengthLayout.addWidget(self.posXCheckBox)

        self.yStrengthLabel = QtWidgets.QLabel('Y-Strength:')
        self.yStrengthLabel.setObjectName('yStrengthLabel')
        self.yStrengthLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.yStrengthLabel.setFixedSize(QtCore.QSize(70, 24))
        self.yStrengthLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.yStrengthLayout = QtWidgets.QHBoxLayout()
        self.yStrengthLayout.setObjectName('yStrengthLayout')
        self.yStrengthLayout.setContentsMargins(0, 0, 0, 0)

        self.yStrengthWidget = QtWidgets.QWidget()
        self.yStrengthWidget.setObjectName('yStrengthWidget')
        self.yStrengthWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.yStrengthWidget.setFixedHeight(24)
        self.yStrengthWidget.setLayout(self.yStrengthLayout)

        self.yStrengthSpinBox = QtWidgets.QDoubleSpinBox()
        self.yStrengthSpinBox.setObjectName('yStrengthSpinBox')
        self.yStrengthSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred))
        self.yStrengthSpinBox.setFixedHeight(24)
        self.yStrengthSpinBox.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.yStrengthSpinBox.setDecimals(2)
        self.yStrengthSpinBox.setMinimum(0.0)
        self.yStrengthSpinBox.setMaximum(10000.0)
        self.yStrengthSpinBox.setSingleStep(0.01)
        self.yStrengthSpinBox.setValue(5.0)
        self.yStrengthSpinBox.setWhatsThis('strengthY')
        self.yStrengthSpinBox.valueChanged.connect(self.on_yStrengthSpinBox_valueChanged)

        self.posYCheckBox = QtWidgets.QCheckBox('>0')
        self.posYCheckBox.setObjectName('posYCheckBox')
        self.posYCheckBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred))
        self.posYCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.posYCheckBox.setWhatsThis('positiveY')
        self.posYCheckBox.stateChanged.connect(self.on_posYCheckBox_stateChanged)

        self.yStrengthLayout.addWidget(self.yStrengthSpinBox)
        self.yStrengthLayout.addWidget(self.posYCheckBox)

        self.zStrengthLabel = QtWidgets.QLabel('Z-Strength:')
        self.zStrengthLabel.setObjectName('zStrengthLabel')
        self.zStrengthLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.zStrengthLabel.setFixedSize(QtCore.QSize(70, 24))
        self.zStrengthLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.zStrengthLayout = QtWidgets.QHBoxLayout()
        self.zStrengthLayout.setObjectName('zStrengthLayout')
        self.zStrengthLayout.setContentsMargins(0, 0, 0, 0)

        self.zStrengthWidget = QtWidgets.QWidget()
        self.zStrengthWidget.setObjectName('zStrengthWidget')
        self.zStrengthWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.zStrengthWidget.setFixedHeight(24)
        self.zStrengthWidget.setLayout(self.zStrengthLayout)

        self.zStrengthSpinBox = QtWidgets.QDoubleSpinBox()
        self.zStrengthSpinBox.setObjectName('zStrengthSpinBox')
        self.zStrengthSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred))
        self.zStrengthSpinBox.setFixedHeight(24)
        self.zStrengthSpinBox.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.zStrengthSpinBox.setDecimals(2)
        self.zStrengthSpinBox.setMinimum(0.0)
        self.zStrengthSpinBox.setMaximum(10000.0)
        self.zStrengthSpinBox.setSingleStep(0.01)
        self.zStrengthSpinBox.setValue(5.0)
        self.zStrengthSpinBox.setWhatsThis('strengthZ')
        self.zStrengthSpinBox.valueChanged.connect(self.on_zStrengthSpinBox_valueChanged)

        self.posZCheckBox = QtWidgets.QCheckBox('>0')
        self.posZCheckBox.setObjectName('posZCheckBox')
        self.posZCheckBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred))
        self.posZCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.posZCheckBox.setWhatsThis('positiveZ')
        self.posZCheckBox.stateChanged.connect(self.on_posZCheckBox_stateChanged)

        self.zStrengthLayout.addWidget(self.zStrengthSpinBox)
        self.zStrengthLayout.addWidget(self.posZCheckBox)

        self.interopLayout.addWidget(self.randomizeSeedPushButton, 0, 0)
        self.interopLayout.addWidget(self.seedSpinBox, 0, 1)
        self.interopLayout.addWidget(self.frequencyLabel, 1, 0)
        self.interopLayout.addWidget(self.frequencySpinBox, 1, 1)
        self.interopLayout.addWidget(self.fractalNoiseCheckBox, 2, 1)
        self.interopLayout.addWidget(self.envelopeLabel, 3, 0)
        self.interopLayout.addWidget(self.envelopeSpinBox, 3, 1)
        self.interopLayout.addWidget(self.roughnessLabel, 4, 0)
        self.interopLayout.addWidget(self.roughnessSpinBox, 4, 1)
        self.interopLayout.addWidget(self.rampInLabel, 0, 2)
        self.interopLayout.addWidget(self.rampInSpinBox, 0, 3)
        self.interopLayout.addWidget(self.rampOutLabel, 1, 2)
        self.interopLayout.addWidget(self.rampOutSpinBox, 1, 3)
        self.interopLayout.addWidget(self.xStrengthLabel, 2, 2)
        self.interopLayout.addWidget(self.xStrengthWidget, 2, 3, 0, 1)
        self.interopLayout.addWidget(self.yStrengthLabel, 3, 2)
        self.interopLayout.addWidget(self.yStrengthWidget, 3, 3, 0, 1)
        self.interopLayout.addWidget(self.zStrengthLabel, 4, 2)
        self.interopLayout.addWidget(self.zStrengthWidget, 4, 3, 0, 1)

        self.noisePropertyWidgets = [
            self.seedSpinBox,
            self.frequencySpinBox,
            self.envelopeSpinBox,
            self.roughnessSpinBox,
            self.rampInSpinBox,
            self.rampOutSpinBox,
            self.xStrengthSpinBox,
            self.yStrengthSpinBox,
            self.zStrengthSpinBox
        ]

        self.noiseCheckBoxes = [
            self.fractalNoiseCheckBox,
            self.posXCheckBox,
            self.posYCheckBox,
            self.posZCheckBox
        ]

        # Initialize properties group-box
        #
        self.propertiesLayout = QtWidgets.QVBoxLayout()
        self.propertiesLayout.setObjectName('propertiesLayout')

        self.propertiesGroupBox = QtWidgets.QGroupBox('Properties:')
        self.propertiesGroupBox.setObjectName('propertiesGroupBox')
        self.propertiesGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.propertiesGroupBox.setLayout(self.propertiesLayout)

        self.propertiesLayout.addWidget(self.filterWidget)
        self.propertiesLayout.addWidget(self.interopWidget)

        centralLayout.addWidget(self.propertiesGroupBox)

        # Initialize animation-range widget
        #
        self.animationRangeLayout = QtWidgets.QHBoxLayout()
        self.animationRangeLayout.setObjectName('animationRangeLayout')
        self.animationRangeLayout.setContentsMargins(0, 0, 0, 0)
        
        self.animationRangeWidget = QtWidgets.QWidget()
        self.animationRangeWidget.setObjectName('animationRangeWidget')
        self.animationRangeWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.animationRangeWidget.setFixedHeight(24)
        self.animationRangeWidget.setLayout(self.animationRangeLayout)

        self.startLabel = QtWidgets.QLabel('Start:')
        self.startLabel.setObjectName('startLabel')
        self.startLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred))
        self.startLabel.setFixedWidth(32)
        self.startLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        
        self.startSpinBox = qtimespinbox.QTimeSpinBox()
        self.startSpinBox.setObjectName('startSpinBox')
        self.startSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred))
        self.startSpinBox.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.startSpinBox.setDefaultType(qtimespinbox.QTimeSpinBox.DefaultType.START_TIME)
        self.startSpinBox.setMinimum(-9999999)
        self.startSpinBox.setMaximum(9999999)
        self.startSpinBox.setValue(self.scene.startTime)

        self.endLabel = QtWidgets.QLabel('End:')
        self.endLabel.setObjectName('endLabel')
        self.endLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred))
        self.endLabel.setFixedWidth(32)
        self.endLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.endSpinBox = qtimespinbox.QTimeSpinBox()
        self.endSpinBox.setObjectName('endSpinBox')
        self.endSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred))
        self.endSpinBox.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.endSpinBox.setDefaultType(qtimespinbox.QTimeSpinBox.DefaultType.END_TIME)
        self.endSpinBox.setMinimum(-9999999)
        self.endSpinBox.setMaximum(9999999)
        self.endSpinBox.setValue(self.scene.endTime)

        self.stepLabel = QtWidgets.QLabel('Step:')
        self.stepLabel.setObjectName('stepLabel')
        self.stepLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred))
        self.stepLabel.setFixedWidth(32)
        self.stepLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.stepSpinBox = QtWidgets.QSpinBox()
        self.stepSpinBox.setObjectName('stepSpinBox')
        self.stepSpinBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred))
        self.stepSpinBox.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.stepSpinBox.setMinimum(1)
        self.stepSpinBox.setMaximum(100)
        self.stepSpinBox.setValue(1)
        
        self.animationRangeLayout.addWidget(self.startLabel)
        self.animationRangeLayout.addWidget(self.startSpinBox)
        self.animationRangeLayout.addWidget(self.endLabel)
        self.animationRangeLayout.addWidget(self.endSpinBox)
        self.animationRangeLayout.addWidget(self.stepLabel)
        self.animationRangeLayout.addWidget(self.stepSpinBox)

        # Initialize baking group-box
        #
        self.bakingLayout = QtWidgets.QGridLayout()
        self.bakingLayout.setObjectName('bakingLayout')

        self.bakingGroupBox = QtWidgets.QGroupBox('Baking:')
        self.bakingGroupBox.setObjectName('bakingGroupBox')
        self.bakingGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.bakingGroupBox.setLayout(self.bakingLayout)

        self.bakePushButton = QtWidgets.QPushButton('Bake')
        self.bakePushButton.setObjectName('bakePushButton')
        self.bakePushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.bakePushButton.setFixedHeight(24)
        self.bakePushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.bakePushButton.clicked.connect(self.on_bakePushButton_clicked)

        self.bakingLayout.addWidget(self.animationRangeWidget)
        self.bakingLayout.addWidget(self.bakePushButton)
        
        centralLayout.addWidget(self.bakingGroupBox)
        
        # Initialize graph group-box
        #
        self.graphLayout = QtWidgets.QGridLayout()
        self.graphLayout.setObjectName('graphLayout')

        self.graphGroupBox = QtWidgets.QGroupBox('Graph:')
        self.graphGroupBox.setObjectName('graphGroupBox')
        self.graphGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.graphGroupBox.setLayout(self.graphLayout)

        self.noiseGraph = qnoisegraph.QNoiseGraph()
        self.noiseGraph.setObjectName('noiseGraph')
        self.noiseGraph.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred))

        self.graphLayout.addWidget(self.noiseGraph)

        centralLayout.addWidget(self.graphGroupBox)
    # endregion

    # region Callbacks
    def selectionChanged(self, *args, **kwargs):
        """
        Notifies all properties of a selection change.

        :key clientData: Any
        :rtype: None
        """

        self.updateNoiseProperties()
    # endregion

    # region Properties
    @property
    def scene(self):
        """
        Getter method that returns the scene interface.

        :rtype: mpyscene.MPyScene
        """

        return self._scene()

    @property
    def startTime(self):
        """
        Getter method that returns the start time.

        :rtype: int
        """

        return self.startSpinBox.value()

    @startTime.setter
    def startTime(self, startTime):
        """
        Setter method that updates the start time.

        :type startTime: int
        :rtype: None
        """

        self.startSpinBox.setValue(startTime)

    @property
    def endTime(self):
        """
        Getter method that returns the end time.

        :rtype: int
        """

        return self.endSpinBox.value()

    @endTime.setter
    def endTime(self, endTime):
        """
        Setter method that updates the end time.

        :type endTime: int
        :rtype: None
        """

        self.endSpinBox.setValue(endTime)

    @property
    def step(self):
        """
        Getter method that returns the step interval.

        :rtype: int
        """

        return self.stepSpinBox.value()

    @step.setter
    def step(self, interval):
        """
        Setter method that updates the step interval.

        :type interval: int
        :rtype: None
        """

        self.stepSpinBox.setValue(interval)
    # endregion

    # region Methods
    def addCallbacks(self):
        """
        Adds any callbacks required by this window.

        :rtype: None
        """

        # Check if callbacks exists
        #
        hasCallbacks = len(self._callbackIds) > 0

        if not hasCallbacks:

            callbackId = om.MEventMessage.addEventCallback('SelectionChanged', onSelectionChanged)
            self._callbackIds.append(callbackId)

        # Force selection update
        #
        self.selectionChanged()

    def removeCallbacks(self):
        """
        Removes any callbacks created by this window.

        :rtype: None
        """

        # Check if callbacks exists
        #
        hasCallbacks = len(self._callbackIds) > 0

        if hasCallbacks:

            om.MEventMessage.removeCallbacks(self._callbackIds)
            self._callbackIds.clear()

    def loadPlugins(self):
        """
        Loads the required plugins.

        :rtype: None
        """

        # Iterate through required plugins
        #
        for plugin in self.__plugins__:

            isLoaded = mc.pluginInfo(plugin, query=True, loaded=True)

            if not isLoaded:

                log.info(f'Loading plugin: {plugin}')
                mc.loadPlugin(plugin)

    def isValidId(self, id):
        """
        Evaluates if the supplied ID is valid.

        :type id: int
        :rtype: bool
        """

        return id in self.__ids__

    def iterControls(self, fromSelection=False):
        """
        Returns a generator that yields animatable controls.

        :type fromSelection: bool
        :rtype: Iterator[mpynode.MPyNode]
        """

        if fromSelection:

            yield from self.scene.iterSelection(apiType=om.MFn.kTransform)

        else:

            yield from self.scene.iterNodesByPattern(*self.__patterns__, apiType=om.MFn.kTransform)

    def iterShakes(self, fromSelection=False):
        """
        Returns a generator that yields shake components from the scene.

        :type fromSelection: bool
        :rtype: Iterator[NoiseItem]
        """

        # Iterate through selected controls
        #
        for node in self.iterControls(fromSelection=fromSelection):

            # Evaluate `offsetParentMatrix` plug
            #
            plug = node['offsetParentMatrix']

            if not plug.isDestination:

                continue

            # Check if source plug is a `composeTransform` node
            # If the node is referenced then skip it to avoid breaking any custom rig functionality!
            #
            sourcePlug = plug.source()
            sourceNode = mpynode.MPyNode(sourcePlug.node())

            if sourceNode.typeName != 'composeTransform' or sourceNode.isFromReferencedFile:

                continue

            # Find associated `shake` nodes
            #
            composeTransform = sourceNode
            positionShake, rotationShake, scaleShake = noiseutils.findAssociatedShakes(composeTransform)

            yield NoiseItem(
                node=node,
                transform=composeTransform,
                position=positionShake,
                rotation=rotationShake,
                scale=scaleShake
            )

    def toggleNoiseProperties(self, state):
        """
        Updates the enabled state on the property widgets.

        :type state: bool
        :rtype: None
        """

        self.interopWidget.setEnabled(state)
        self.bakingGroupBox.setEnabled(state)
        self.noiseGraph.setEnabled(state)

    def enableNoiseProperties(self):
        """
        Enables the noise property widgets.

        :rtype: None
        """

        self.toggleNoiseProperties(True)

    def disableNoiseProperties(self):
        """
        Disables the noise property widgets.

        :rtype: None
        """

        self.toggleNoiseProperties(False)

    def updateNoiseProperties(self):
        """
        Updates the noise property widgets.

        :rtype: None
        """

        # Get selected shake nodes
        #
        checkedId = self.radioButtonGroup.checkedId()
        index = checkedId if (checkedId != -1) else None

        shakes = [noiseItem[index] for noiseItem in self.iterShakes(fromSelection=True) if noiseItem[index] is not None] if index is not None else []
        numShakes = len(shakes)

        if numShakes == 0:

            self.disableNoiseProperties()
            return

        # Iterate through property widgets
        #
        self.enableNoiseProperties()

        for (i, widget) in enumerate(self.noisePropertyWidgets):

            # Evaluate selected shake nodes
            #
            widget.blockSignals(True)

            if len(shakes) == 0:

                widget.lineEdit().setText('')

            elif len(shakes) == 1:

                widget.setValue(shakes[0].getAttr(widget.whatsThis()))

            else:

                values = list({shake.getAttr(widget.whatsThis()) for shake in shakes})
                isIdentical = len(values) == 1

                if isIdentical:

                    widget.setValue(values[0])

                else:

                    widget.lineEdit().setText('Mixed Values')

            widget.blockSignals(False)

        # Iterate through check boxes
        #
        for (i, checkBox) in enumerate(self.noiseCheckBoxes):

            # Evaluate selected shake nodes
            #
            checkBox.blockSignals(True)

            if len(shakes) == 0:

                checkBox.setChecked(False)

            elif len(shakes) == 1:

                checkBox.setChecked(shakes[0].getAttr(checkBox.whatsThis()))

            else:

                values = list({shake.getAttr(checkBox.whatsThis()) for shake in shakes})
                isIdentical = len(values) == 1

                if isIdentical:

                    checkBox.setChecked(values[0])

                else:

                    checkBox.setCheckState(QtCore.Qt.PartiallyChecked)

            checkBox.blockSignals(False)

        # Update noise graph
        #
        self.updateNoiseGraph(shakes[0])

    def updateNoiseGraph(self, shake):
        """
        Updates the noise graph widget.

        :type shake: mpynode.MPyNode
        :rtype: None
        """

        self.noiseGraph.seed = shake.getAttr('seed')
        self.noiseGraph.frequency = shake.getAttr('frequency')
        self.noiseGraph.roughness = shake.getAttr('roughness')
        self.noiseGraph.fractal = shake.getAttr('fractal')
        self.noiseGraph.rampIn = shake.getAttr('rampIn')
        self.noiseGraph.rampOut = shake.getAttr('rampOut')

    def setDefaultNoiseProperties(self, shake):
        """
        Updates the default value of the noise properties.

        :type shake: mpynode.MPyNode
        :rtype: None
        """
        
        shake.setAttr('frequency', 5.0)
        shake.setAttr('roughness', 0.5)

    @undo.Undo(state=False)
    def createNoise(self):
        """
        Assigns shake nodes to the active selection.

        :rtype: None
        """

        with animate.Animate(state=False):

            # Iterate through selected controls
            #
            timeNode = mpynode.MPyNode('time1')

            for node in self.iterControls(fromSelection=True):

                # Evaluate `offsetParentMatrix` plug connections
                #
                nodeName = node.name()
                plug = node['offsetParentMatrix']

                composeTransform = None

                if plug.isDestination:

                    sourceNode = mpynode.MPyNode(plug.source().node())

                    if sourceNode.typeName == 'composeTransform':

                        composeTransform = sourceNode

                    else:

                        continue
                else:

                    composeTransformName = f'{node.name()}_composeTransform'
                    composeTransform = self.scene.createNode('composeTransform', name=composeTransformName)
                    composeTransform.setAttr('inputOffsetParentMatrix', node.getAttr('offsetParentMatrix'))
                    composeTransform.connectPlugs(node['translate'], 'inputRotatePivot')
                    composeTransform.connectPlugs(node['translate'], 'inputScalePivot')
                    composeTransform.connectPlugs(node['rotateOrder'], 'inputRotateOrder')
                    composeTransform.connectPlugs('outputMatrix', plug)
                    composeTransform.setDoNotWrite(True)

                # Check if position is checked
                #
                if self.posCheckBox.isChecked():

                    if not plugutils.hasConnection(composeTransform['inputTranslate']):

                        shakeName = f'{nodeName}_positionShake'
                        shake = self.scene.createNode('shake', name=shakeName)
                        shake.setDoNotWrite(True)

                        self.setDefaultNoiseProperties(shake)

                        shake.connectPlugs('outputTranslate', composeTransform['inputTranslate'])
                        shake.connectPlugs(timeNode['outTime'], 'time')

                    else:

                        log.warning(f'"{nodeName}" control already has position noise!')

                # Check if rotation is checked
                #
                if self.rotCheckBox.isChecked():

                    if not plugutils.hasConnection(composeTransform['inputRotate']):

                        shakeName = f'{nodeName}_rotationShake'
                        shake = self.scene.createNode('shake', name=shakeName)
                        shake.setDoNotWrite(True)

                        self.setDefaultNoiseProperties(shake)

                        shake.connectPlugs('outputRotate', composeTransform['inputRotate'])
                        shake.connectPlugs(timeNode['outTime'], 'time')

                    else:

                        log.warning(f'"{nodeName}" control already has rotation noise!')

                # Check if scale is checked
                #
                if self.scaleCheckBox.isChecked():

                    if not plugutils.hasConnection(composeTransform['inputScale']):

                        shakeName = f'{nodeName}_scaleShake'
                        shake = self.scene.createNode('shake', name=shakeName)
                        shake.setDoNotWrite(True)

                        self.setDefaultNoiseProperties(shake)

                        shake.connectPlugs('outputScale', composeTransform['inputScale'])
                        shake.connectPlugs(timeNode['outTime'], 'time')

                    else:

                        log.warning(f'"{nodeName}" control already has scale noise!')

            # Invalidate noise properties
            #
            self.updateNoiseProperties()

    @undo.Undo(state=False)
    def selectNoise(self):
        """
        Selects any controls with shake nodes from the scene file.

        :rtype: None
        """

        # Check if position is enabled
        #
        nodes = []

        if self.posCheckBox.isChecked():

            found = [noiseItem.node for noiseItem in self.iterShakes(fromSelection=False) if noiseItem.position is not None]
            nodes.extend(found)

        # Check if rotation is enabled
        #
        if self.rotCheckBox.isChecked():

            found = [noiseItem.node for noiseItem in self.iterShakes(fromSelection=False) if noiseItem.rotation is not None]
            nodes.extend(found)

        # Check if scale is enabled
        #
        if self.scaleCheckBox.isChecked():

            found = [noiseItem.node for noiseItem in self.iterShakes(fromSelection=False) if noiseItem.scale is not None]
            nodes.extend(found)

        # Update active selection
        #
        self.scene.setSelection(nodes)

    @undo.Undo(state=False)
    def deleteNoise(self, fromSelection=True):
        """
        Deletes any shake nodes from the active selection.

        :type fromSelection: bool
        :rtype: None
        """

        with animate.Animate(state=False):

            # Iterate through selected nodes
            #
            for noiseItem in self.iterShakes(fromSelection=fromSelection):

                # Check if position requires deleting
                #
                if self.posCheckBox.isChecked() and noiseItem.position is not None:

                    noiseItem.position.delete()
                    noiseItem.transform.resetAttr('inputTranslate')

                # Check if rotation requires deleting
                #
                if self.rotCheckBox.isChecked() and noiseItem.rotation is not None:

                    noiseItem.rotation.delete()
                    noiseItem.transform.resetAttr('inputRotate')

                # Check if scale requires deleting
                #
                if self.scaleCheckBox.isChecked() and noiseItem.scale is not None:

                    noiseItem.scale.delete()
                    noiseItem.transform.resetAttr('inputScale')

                # Check if compose transform requires deleting
                #
                hasPosition = any([plug.isDestination for plug in plugutils.iterChildren(noiseItem.transform['inputTranslate'])])
                hasRotation = any([plug.isDestination for plug in plugutils.iterChildren(noiseItem.transform['inputRotate'])])
                hasScale = any([plug.isDestination for plug in plugutils.iterChildren(noiseItem.transform['inputScale'])])

                if not any([hasPosition, hasRotation, hasScale]):

                    offsetParentMatrix = noiseItem.transform.getAttr('inputOffsetParentMatrix')
                    noiseItem.transform.delete()

                    if noiseItem.node.isFromReferencedFile:

                        referenceNode = noiseItem.node.getAssociatedReferenceNode()
                        referenceNode.removeEdits(noiseItem.node['offsetParentMatrix'])

                    else:

                        noiseItem.node.setAttr('offsetParentMatrix', offsetParentMatrix)

            # Invalidate noise properties
            #
            self.updateNoiseProperties()

    @undo.Undo(state=False)
    def pushNoise(self, widget, id=-1):
        """
        Pushes the supplied widget's value to the active selection.

        :type widget: Union[QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox, QtWidgets.QCheckBox]
        :type id: int
        :rtype: None
        """

        # Evaluate supplied ID
        #
        if not self.isValidId(id):

            return

        # Iterate through shake nodes
        #
        for noiseItem in self.iterShakes(fromSelection=True):

            # Check if noise item is valid
            #
            if noiseItem[id] is None:

                continue

            # Update associated node attribute
            #
            attribute = widget.whatsThis()

            if isinstance(widget, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):

                noiseItem[id].setAttr(attribute, widget.value())

            elif isinstance(widget, QtWidgets.QCheckBox):

                noiseItem[id].setAttr(attribute, widget.isChecked())

            else:

                continue

    @undo.Undo(state=False)
    def randomizeSeed(self, id=-1):
        """
        Randomizes the seed value on the selected controls.

        :type id: int
        :rtype: None
        """

        # Evaluate supplied ID
        #
        if not self.isValidId(id):

            return

        # Iterate through shake nodes
        #
        for noiseItem in self.iterShakes(fromSelection=True):

            noiseItem[id].setAttr('seed', random.randint(0, 99))

        # Invalidate noise properties
        #
        self.updateNoiseProperties()

    @undo.Undo(state=False)
    def bakeNoise(self):
        """
        Bakes any controllers with shake node(s) from the active selection.

        :rtype: None
        """

        # Iterate through selected nodes
        #
        for noiseItem in self.iterShakes(fromSelection=True):

            # Check if any shake nodes exist
            #
            shakes = list(filter(None, (noiseItem.position, noiseItem.rotation, noiseItem.scale)))
            numShakes = len(shakes)

            if numShakes == 0:

                noiseItem.transform.delete()
                noiseItem.node.setAttr('offsetParentMatrix', om.MMatrix.kIdentity)

                continue

            # Enable auto-key and iterate through time-range
            #
            positionEnabled = noiseItem.position is not None
            rotationEnabled = noiseItem.rotation is not None
            scaleEnabled = noiseItem.scale is not None

            with animate.Animate(state=True):

                # Iterate through time-range
                #
                position = om.MVector(noiseItem.node.getAttr('translate'))
                rotation = om.MVector(noiseItem.node.getAttr('rotate'))
                scale = om.MVector(noiseItem.node.getAttr('scale'))

                for time in inclusiveRange(self.startTime, self.endTime, self.step):

                    # Go to next frame
                    #
                    self.scene.time = time

                    if positionEnabled:

                        newTranslation = position + om.MVector(noiseItem.transform.getAttr('inputTranslate'))
                        noiseItem.node.setAttr('translate', newTranslation)

                    if rotationEnabled:

                        newRotation = rotation + om.MVector(noiseItem.transform.getAttr('inputRotate'))  # Should be safe to add rotations???
                        noiseItem.node.setAttr('rotate', newRotation)

                    if scaleEnabled:

                        newScale = scale + om.MVector(noiseItem.transform.getAttr('inputScale'))
                        noiseItem.node.setAttr('scale', newScale)

                # Cleanup shake nodes
                #
                if positionEnabled:

                    noiseItem.position.delete()  # Deleting position shake after baking

                if rotationEnabled:

                    noiseItem.rotation.delete()  # Deleting rotation shake after baking

                if scaleEnabled:

                    noiseItem.scale.delete()  # Deleting scale shake after baking

                # Cleanup compose transform node and reset `offsetParentMatrix` plug
                #
                noiseItem.transform.delete()
                noiseItem.node.setAttr('offsetParentMatrix', om.MMatrix.kIdentity)

        # Invalidate noise properties
        #
        self.updateNoiseProperties()
    # endregion

    # region Slots
    @QtCore.Slot(int)
    def on_radioButtonGroup_idClicked(self, id):
        """
        Slot method for the `radioButtonGroup` widget's `idClicked` signal.

        :type id: int
        :rtype: None
        """

        self.updateNoiseProperties()

    @QtCore.Slot(bool)
    def on_createPushButton_clicked(self, checked=False):
        """
        Slot method for the `noiseCreatePushButton` widget's `clicked` signal.

        :type checked: bool
        :rtype: None
        """

        self.createNoise()

    @QtCore.Slot(bool)
    def on_selectPushButton_clicked(self, checked=False):
        """
        Slot method for the `noiseSelectPushButton` widget's `clicked` signal.

        :type checked: bool
        :rtype: None
        """

        self.selectNoise()

    @QtCore.Slot(bool)
    def on_deletePushButton_clicked(self, checked=False):
        """
        Slot method for the `noiseDeletePushButton` widget's `clicked` signal.

        :type checked: bool
        :rtype: None
        """

        self.deleteNoise(fromSelection=True)

    @QtCore.Slot(bool)
    def on_bakePushButton_clicked(self, checked=False):
        """
        Slot method for the `bakePushButton` widget's `clicked` signal.

        :type checked: bool
        :rtype: None
        """

        self.bakeNoise()

    @QtCore.Slot(int)
    def on_seedSpinBox_valueChanged(self, value):
        """
        Slot method for the `seedSpinBox` widget's `valueChanged` signal.

        :type value: int
        :rtype: None
        """

        self.pushNoise(self.sender(), id=self.radioButtonGroup.checkedId())
        self.noiseGraph.seed = value

    @QtCore.Slot(bool)
    def on_randomizeSeedPushButton_clicked(self, checked=False):
        """
        Slot method for the `randomizeSeedPushButton` widget's `clicked` signal.

        :type checked: bool
        :rtype: None
        """

        self.randomizeSeed(id=self.radioButtonGroup.checkedId())

    @QtCore.Slot(float)
    def on_frequencySpinBox_valueChanged(self, value):
        """
        Slot method for the `frequencySpinBox` widget's `valueChanged` signal.

        :type value: float
        :rtype: None
        """

        self.pushNoise(self.sender(), id=self.radioButtonGroup.checkedId())
        self.noiseGraph.frequency = value

    @QtCore.Slot(float)
    def on_envelopeSpinBox_valueChanged(self, value):
        """
        Slot method for the `envelopeSpinBox` widget's `valueChanged` signal.

        :type value: float
        :rtype: None
        """

        self.pushNoise(self.sender(), id=self.radioButtonGroup.checkedId())

    @QtCore.Slot(float)
    def on_roughnessSpinBox_valueChanged(self, value):
        """
        Slot method for the `roughnessSpinBox` widget's `valueChanged` signal.

        :type value: float
        :rtype: None
        """

        self.pushNoise(self.sender(), id=self.radioButtonGroup.checkedId())
        self.noiseGraph.roughness = value

    @QtCore.Slot(float)
    def on_rampInSpinBox_valueChanged(self, value):
        """
        Slot method for the `rampInSpinBox` widget's `valueChanged` signal.

        :type value: float
        :rtype: None
        """

        self.pushNoise(self.sender(), id=self.radioButtonGroup.checkedId())
        self.noiseGraph.rampIn = value

    @QtCore.Slot(float)
    def on_rampOutSpinBox_valueChanged(self, value):
        """
        Slot method for the `rampOutSpinBox` widget's `valueChanged` signal.

        :type value: float
        :rtype: None
        """

        self.pushNoise(self.sender(), id=self.radioButtonGroup.checkedId())
        self.noiseGraph.rampOut = value

    @QtCore.Slot(float)
    def on_xStrengthSpinBox_valueChanged(self, value):
        """
        Slot method for the `xStrengthSpinBox` widget's `valueChanged` signal.

        :type value: float
        :rtype: None
        """

        self.pushNoise(self.sender(), id=self.radioButtonGroup.checkedId())

    @QtCore.Slot(float)
    def on_yStrengthSpinBox_valueChanged(self, value):
        """
        Slot method for the `yStrengthSpinBox` widget's `valueChanged` signal.

        :type value: float
        :rtype: None
        """

        self.pushNoise(self.sender(), id=self.radioButtonGroup.checkedId())

    @QtCore.Slot(float)
    def on_zStrengthSpinBox_valueChanged(self, value):
        """
        Slot method for the `zStrengthSpinBox` widget's `valueChanged` signal.

        :type value: float
        :rtype: None
        """

        self.pushNoise(self.sender(), id=self.radioButtonGroup.checkedId())

    @QtCore.Slot(int)
    def on_fractalNoiseCheckBox_stateChanged(self, state):
        """
        Slot method for the `fractalNoiseCheckBox` widget's `stateChanged` signal.

        :type state: bool
        :rtype: None
        """

        sender = self.sender()
        self.pushNoise(sender, id=self.radioButtonGroup.checkedId())
        self.noiseGraph.fractal = sender.isChecked()

    @QtCore.Slot(int)
    def on_posXCheckBox_stateChanged(self, state):
        """
        Slot method for the `posXCheckBox` widget's `stateChanged` signal.

        :type state: bool
        :rtype: None
        """

        self.pushNoise(self.sender(), id=self.radioButtonGroup.checkedId())

    @QtCore.Slot(int)
    def on_posYCheckBox_stateChanged(self, state):
        """
        Slot method for the `posYCheckBox` widget's `stateChanged` signal.

        :type state: bool
        :rtype: None
        """

        self.pushNoise(self.sender(), id=self.radioButtonGroup.checkedId())

    @QtCore.Slot(int)
    def on_posZCheckBox_stateChanged(self, state):
        """
        Slot method for the `posZCheckBox` widget's `stateChanged` signal.

        :type state: bool
        :rtype: None
        """

        self.pushNoise(self.sender(), id=self.radioButtonGroup.checkedId())
    # endregion
