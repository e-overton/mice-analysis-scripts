#!/usr/bin/env python

"""
A nice set of TOF tools for helping place cuts on the
tracker data.
"""

def TOFHit(SlabHitArray):
    """
    A function to verify that a TOF was hit
    using only slab infomation. Note that since this
    requires both a vertical and horizontal hit it
    is quite immune to noise, but does not depend
    on timing infomation
    """
    
    plane_hits = [0,0]
    for sh in SlabHitArray:
        plane_hits[sh.GetPlane()] += 1
    
    return (plane_hits[0] > 0 and plane_hits[1] > 0)


def TOF12Coincidence(TOFEvent):
    """
    Return the coincidence of TOF1 and TOF2, using
    the TOFHit function.
    """
    shs = TOFEvent.GetTOFEventSlabHit()

    return TOFHit(shs.GetTOF1SlabHitArray()) and\
        TOFHit(shs.GetTOF2SlabHitArray())
