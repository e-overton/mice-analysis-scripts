"""
Attempt to use the EMR to determine muon/electron-ness...
"""

import math


def EMRMuon(EMREvent):
    """
    Function which copies the Online Reconstructions
    method for dermining muons.
    """

    chi2 = EMREvent.GetChi2()
    density = EMREvent.GetPlaneDensity()

    try:
        return math.log1p(chi2) < 1.0 and density > 0.9
    except ValueError:
        print "EMR-VERR",
        return False