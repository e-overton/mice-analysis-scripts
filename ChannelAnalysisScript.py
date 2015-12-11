#!/bin/env PYTHON
"""
Script to allow processing of a Channel in the ChannelAnalysis Script
"""

# Packages :
import pickle
from ChannelAnalysis import ChannelAnalysis, ChannelAnalysisResultsProcessor
import ROOT

# Parameters:
_FILENAME = "dpro2.pickle"
_TRACKER = 1
_STATION = 5
_PLANE = 1
_CHANNEL = 100


if __name__ == "__main__":
    """
    Default function, should load default data
    """
    d = pickle.load(file(_FILENAME))

    tg = ROOT.TGraphErrors()

    for _CHANNEL in range(1,200):

        # Select Channel to Process:
        proc_channel = None
        for c in d.channels:
            assert isinstance(c, ChannelAnalysis)
            if (_TRACKER == c.tracker) and \
               (_STATION == c.station) and \
               (_PLANE == c.plane) and \
               (_CHANNEL == c.channel):
                # Found the desired Channel:
                proc_channel = c

        try:
            assert isinstance(proc_channel, ChannelAnalysis)
        except:
            print "Channel is not a channelanalysis type.."

        # Results processing:
        rpro = ChannelAnalysisResultsProcessor(proc_channel)
        ly, ly_e = rpro.findLightYield()
        point = tg.GetN()
        tg.SetPoint(point, _CHANNEL, ly)
        tg.SetPointError(point, 0.0, ly_e)
        
        #rpro.parameteriseLightYield("duplet")

    tg.Draw("AP")

    #rpro.draw()

    raw_input("press to exit")