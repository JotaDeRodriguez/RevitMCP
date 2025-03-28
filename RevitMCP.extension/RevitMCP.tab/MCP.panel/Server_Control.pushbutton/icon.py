# -*- coding: utf-8 -*-
from pyrevit import EXEC_PARAMS

# PyRevit will use the icon data encoded here
if EXEC_PARAMS.exec_mode:
    try:
        from pyrevit.versionmgr import PYREVIT_VERSION
        if PYREVIT_VERSION.major >= 4 and PYREVIT_VERSION.minor >= 7:
            # If PyRevit version >= 4.7, can define arbitrary sized icons
            __iconsize__ = 16
            
            # Define a server/computer icon (simple stylized design for 16x16)
            __min_icon__ = """
        iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQI
        CAgIfAhkiAAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdh
        cmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAFJSURBVDiNpZMxSgNBFIa/
        mSyb3YAHsBMEC7G18ADiCSzSewYP4BksLEVs7AU7C89gJVjYCFoqGg3J
        zrxncRPMLju68Mowj/n/7/1vHvxXLKpYUyvRrO+Aec+F1Q23o2r5I0DH
        dLw5iwBT/zKE8g1k/AaLZl3XsXpJPkm1vXXTEoYfQL4EqvqWquq9quqN
        qr7GUbRMkjMGLe8tAFW9QtkD+lhcCRTWTIBrDw/fzPokl1KZjVxMlkqE
        LCmFmA+RMGV+V6QwA/wkvZjAM44H40dqd28LwE7cswPg0HU6G2sYuATG
        Dk5cO3rKlMc8WCnNdSKrxlFUw803MADIRGQgIu7Ksty0ceZB4d5BkPgW
        yJN+pMnNNg4OKvMA5OmDxNsVxXLWo1VvPMvzE6AOrAOpzfPT4vR0t3QL
        QUJfT2Jdl3IXZf8XDIAx4IEpcDt4f/t9/S+yH5zAB/dcdQqLAAAAAElF
        TkSuQmCC
        """
    except:
        # Legacy icon size of 16x16
        __iconsize__ = 16
        
        # Define a simple server/computer icon
        __min_icon__ = """
        iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQI
        CAgIfAhkiAAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdh
        cmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAFJSURBVDiNpZMxSgNBFIa/
        mSyb3YAHsBMEC7G18ADiCSzSewYP4BksLEVs7AU7C89gJVjYCFoqGg3J
        zrxncRPMLju68Mowj/n/7/1vHvxXLKpYUyvRrO+Aec+F1Q23o2r5I0DH
        dLw5iwBT/zKE8g1k/AaLZl3XsXpJPkm1vXXTEoYfQL4EqvqWquq9quqN
        qr7GUbRMkjMGLe8tAFW9QtkD+lhcCRTWTIBrDw/fzPokl1KZjVxMlkqE
        LCmFmA+RMGV+V6QwA/wkvZjAM44H40dqd28LwE7cswPg0HU6G2sYuATG
        Dk5cO3rKlMc8WCnNdSKrxlFUw803MADIRGQgIu7Ksty0ceZB4d5BkPgW
        yJN+pMnNNg4OKvMA5OmDxNsVxXLWo1VvPMvzE6AOrAOpzfPT4vR0t3QL
        QUJfT2Jdl3IXZf8XDIAx4IEpcDt4f/t9/S+yH5zAB/dcdQqLAAAAAElF
        TkSuQmCC
        """ 