# -*- coding: utf-8 -*-
from pyrevit import EXEC_PARAMS

# PyRevit will use the icon data encoded here
if EXEC_PARAMS.exec_mode:
    try:
        from pyrevit.versionmgr import PYREVIT_VERSION
        if PYREVIT_VERSION.major >= 4 and PYREVIT_VERSION.minor >= 7:
            # If PyRevit version >= 4.7, can define arbitrary sized icons
            __iconsize__ = 16
            
            # Define a chat bubble icon (simple stylized design for 16x16)
            __min_icon__ = """
        iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQI
        CAgIfAhkiAAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdh
        cmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAGRSURBVDiNlZMxSxxBFMd/
        b2ZWbxVt7IQUVhZp7CzS6BkQU1gIQgqb9H4Cv4O1jXiFToJ2NoJpEl2i
        CYcgCJ7em533UuwpG2/vvD88Zt68//vPf2aE+9RGegxrAkQZx9/XcvYx
        Z+kNEMu4Jri+fHuiqfN29G1pGjAYsyBa9oVogBDpBQsNIoFuNJoJYDjm
        hF0OeiL+pOfHm1s7AGbmO3KWm7p67oYmQHHOjkjvTZ0/tYKBxTmnMIr1
        wJyFpPk2gTmHK4pQVWA9dI5U5UylEmrrwWV4URSpVKJWD1VCRAil9aRZ
        QVKPq/EYHwhQtZHMrSexJLsflxM4w/MQmyEXm/UbUlX0i8xsjycN0HI9
        u5tjN1wQvLCWcgzK9XjydWTAxeY4IGE7wOOJUoLbXhAbzWdXTi8m9yLp
        PQxKMVkKXGFWiExLqyXdm6eNtIvAA7G+yNSJNeLyoLG3/B/g6MWwdHnw
        +M7aqBPrb5jx7urwmcbuj4m1YTC+KKMlsE1gEzjU1BnklPTszyu6OwOW
        FGUMKORPfvHx7HYi/wAIh62dsCrM4AAAAABJRU5ErkJggg==
        """
    except:
        # Legacy icon size of 16x16
        __iconsize__ = 16
        
        # Define a simple chat bubble icon
        __min_icon__ = """
        iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQI
        CAgIfAhkiAAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdh
        cmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAGRSURBVDiNlZMxSxxBFMd/
        b2ZWbxVt7IQUVhZp7CzS6BkQU1gIQgqb9H4Cv4O1jXiFToJ2NoJpEl2i
        CYcgCJ7em533UuwpG2/vvD88Zt68//vPf2aE+9RGegxrAkQZx9/XcvYx
        Z+kNEMu4Jri+fHuiqfN29G1pGjAYsyBa9oVogBDpBQsNIoFuNJoJYDjm
        hF0OeiL+pOfHm1s7AGbmO3KWm7p67oYmQHHOjkjvTZ0/tYKBxTmnMIr1
        wJyFpPk2gTmHK4pQVWA9dI5U5UylEmrrwWV4URSpVKJWD1VCRAil9aRZ
        QVKPq/EYHwhQtZHMrSexJLsflxM4w/MQmyEXm/UbUlX0i8xsjycN0HI9
        u5tjN1wQvLCWcgzK9XjydWTAxeY4IGE7wOOJUoLbXhAbzWdXTi8m9yLp
        PQxKMVkKXGFWiExLqyXdm6eNtIvAA7G+yNSJNeLyoLG3/B/g6MWwdHnw
        +M7aqBPrb5jx7urwmcbuj4m1YTC+KKMlsE1gEzjU1BnklPTszyu6OwOW
        FGUMKORPfvHx7HYi/wAIh62dsCrM4AAAAABJRU5ErkJggg==
        """ 