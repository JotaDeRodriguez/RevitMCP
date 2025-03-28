# -*- coding: utf-8 -*-
# pylint: skip-file
# This icon is from the PyRevit icon library

from pyrevit import EXEC_PARAMS

__all__ = ['geticon']

def geticon():
    return EXEC_PARAMS.imagedir + '\\settings.png' 