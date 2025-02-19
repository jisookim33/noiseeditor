from Qt import QtCore, QtWidgets, QtGui
from maya import cmds as mc
from mpy import mpyscene

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QNoiseGraph(QtWidgets.QWidget):
    """
    Overload of `QWidget` that displays a noise graph.
    """

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key parent: QtWidgets.QWidget
        :key f: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        parent = kwargs.pop('parent', None)
        f = kwargs.pop('f', QtCore.Qt.WindowFlags())

        super(QNoiseGraph, self).__init__(parent=parent, f=f)

        # Declare private variables
        #
        self._scene = mpyscene.MPyScene.getInstance(asWeakReference=True)
        self._seed = kwargs.get('seed', 0)
        self._frequency = kwargs.get('frequency', 0.5)
        self._roughness = kwargs.get('roughness', 0.0)
        self._fractal = kwargs.get('fractal', True)
        self._rampIn = kwargs.get('rampIn', 0.0)
        self._rampOut = kwargs.get('rampOut', 0.0)
        self._step = kwargs.get('step', 4)
        self._timeScale = kwargs.get('timeScale', 20)
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
    def seed(self):
        """
        Getter method that returns the seed value.

        :rtype: int
        """

        return self._seed

    @seed.setter
    def seed(self, seed):
        """
        Setter method that updates the seed value.

        :type seed: int
        :rtype: None
        """

        self._seed = seed
        self.repaint()

    @property
    def frequency(self):
        """
        Getter method that returns the frequency value.

        :rtype: float
        """

        return self._frequency

    @frequency.setter
    def frequency(self, frequency):
        """
        Setter method that updates the frequency value.

        :type frequency: float
        :rtype: None
        """

        self._frequency = frequency
        self.repaint()

    @property
    def roughness(self):
        """
        Getter method that returns the roughness value.

        :rtype: float
        """

        return self._roughness

    @roughness.setter
    def roughness(self, roughness):
        """
        Setter method that updates the roughness value.

        :type roughness: float
        :rtype: None
        """

        self._roughness = roughness
        self.repaint()

    @property
    def fractal(self):
        """
        Getter method that returns the fractal flag.

        :rtype: bool
        """

        return self._fractal

    @fractal.setter
    def fractal(self, fractal):
        """
        Setter method that updates the fractal flag.

        :type fractal: bool
        :rtype: None
        """

        self._fractal = fractal
        self.repaint()

    @property
    def rampIn(self):
        """
        Getter method that returns the ramp-in time.

        :rtype: float
        """

        return self._rampIn

    @rampIn.setter
    def rampIn(self, rampIn):
        """
        Setter method that updates the ramp-in time.

        :type rampIn: float
        :rtype: None
        """

        self._rampIn = rampIn
        self.repaint()

    @property
    def rampOut(self):
        """
        Getter method that returns the ramp-out time.

        :rtype: float
        """

        return self._rampOut

    @rampOut.setter
    def rampOut(self, rampOut):
        """
        Setter method that updates the ramp-out time.

        :type rampOut: float
        :rtype: None
        """

        self._rampOut = rampOut
        self.repaint()

    @property
    def step(self):
        """
        Getter method that returns the draw step in pixels.

        :rtype: int
        """

        return self._step

    @step.setter
    def step(self, step):
        """
        Setter method that updates the draw step in pixels.

        :type step: int
        :rtype: None
        """

        self._step = step
        self.repaint()

    @property
    def timeScale(self):
        """
        Getter method that returns the time scale.

        :rtype: int
        """

        return self._timeScale

    @timeScale.setter
    def timeScale(self, timeScale):
        """
        Setter method that updates the time scale.

        :type timeScale: int
        :rtype: None
        """

        self._timeScale = timeScale
        self.repaint()
    # endregion

    # region Events
    def paintEvent(self, event):
        """
        The event for any paint requests made to this widget.

        :type event: QtGui.QPaintEvent
        :rtype: None
        """

        # Initialize painter
        #
        painter = QtGui.QPainter(self)
        self.initPainter(painter)

        # Paint background
        #
        rect = self.rect()
        size = rect.width()
        palette = self.palette()

        pen = QtGui.QPen(palette.alternateBase(), 1)
        brush = palette.base()

        painter.setPen(pen)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.fillRect(rect, brush)
        painter.drawRect(rect)

        # Paint axis line
        #
        left, right = rect.left(), rect.right()
        top, bottom = rect.top(), rect.bottom()
        mid = rect.center().y()

        pen = QtGui.QPen(palette.text(), 1)
        pen.setStyle(QtCore.Qt.DashLine)

        painter.setPen(pen)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawLine(QtCore.QPointF(left, mid), QtCore.QPointF(right, mid))

        # Paint ramp lines
        #
        startTime, endTime = self.scene.animationRange
        rampScale = size / (endTime - startTime)
        rampIn, rampOut = (left + (self.rampIn * rampScale)), (right - (self.rampOut * rampScale))

        painter.drawLine(QtCore.QPointF(rampIn, top), QtCore.QPointF(rampIn, bottom))
        painter.drawLine(QtCore.QPointF(rampOut, top), QtCore.QPointF(rampOut, bottom))

        # Paint noise line
        #
        if self.isEnabled():

            values = mc.shake(
                seed=self.seed,
                frequency=self.frequency,
                roughness=self.roughness,
                fractal=self.fractal,
                rampIn=self.rampIn,
                rampOut=self.rampOut,
                size=size,
                step=self.step,
                timeScale=self.timeScale
            )

            path = QtGui.QPainterPath(QtCore.QPointF(0, mid))

            for (i, x) in enumerate(range(rect.left(), rect.right(), self.step)):

                y = mid + int(rect.height() * values[i])
                path.lineTo(QtCore.QPointF(x, y))

            pen = QtGui.QPen(palette.highlightedText(), 1)
            pen.setStyle(QtCore.Qt.SolidLine)

            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawPath(path)
    # endregion
