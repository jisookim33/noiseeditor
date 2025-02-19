from mpy import mpynode
from dcc.maya.libs import plugutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def findAssociatedShakes(composeTransform):
    """
    Returns the shake nodes from the supplied `composeTransform` node.

    :type composeTransform: mpynode.MPyNode
    :rtype: Tuple[Union[mpynode.MPyNode, None], Union[mpynode.MPyNode, None], Union[mpynode.MPyNode, None]]
    """

    # Iterate through destination plugs
    #
    shakes = [None, None, None]

    for (i, attributeName) in enumerate(['inputTranslate', 'inputRotate', 'inputScale']):

        # Check if compound plug is connected
        #
        plug = composeTransform[attributeName]

        if plug.isDestination:

            # Evaluate source type
            #
            sourceNode = mpynode.MPyNode(plug.source().node())

            if sourceNode.typeName == 'shake':

                shakes[i] = sourceNode

            else:

                continue

        else:

            # Evaluate child plugs
            #
            sourcePlugs = [childPlug.source() for childPlug in plugutils.iterChildren(plug)]
            isNull = any([sourcePlug.isNull for sourcePlug in sourcePlugs])

            if isNull:
                continue

            sourceNodes = [mpynode.MPyNode(sourcePlug.node()) for sourcePlug in sourcePlugs]
            isShake = all([sourceNode.typeName == 'shake' for sourceNode in sourceNodes])

            if isShake:

                shakes[i] = sourceNodes[0]

            else:

                continue

    return shakes
