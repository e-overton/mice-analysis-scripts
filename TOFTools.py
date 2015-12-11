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


def TOF12Times(TOFSpacePoints, trigger_time=1):
    """
    Caclulate times between the TOF1 trigger and TOF2.

    The "trigger" spacepoint is determined by being
    within trigger_time from t=0, default is 1ns.

    returns an array of possible times for particles
    between a trigger in TOF1 and TOF2.
    """

    times = []

    for tof1_sp in TOFSpacePoints.GetTOF1SpacePointArray():
        tof1_sp_time = tof1_sp.GetTime()
        if abs(tof1_sp_time) < trigger_time:
            for tof2_sp in TOFSpacePoints.GetTOF2SpacePointArray():
                times.append(tof2_sp.GetTime() - tof1_sp_time)

    return times


def TOF12CoincidenceTime(TOFEvent, low_ns=20, high_ns=50):
    """
    Return the coincidence of TOF1 and TOF2, using
    the TOFHit function.
    """

    for time in TOF12Times(TOFEvent.GetTOFEventSpacePoint()):
        if (time < high_ns) and (time > low_ns):
            return True

    return False


def TimeInSpill(Spill, event_number):
    """
    Use the V1290 coarse time to determine the
    time within the spill, using the time tag,
    which counts in 800ns steps.

    The arbitary subtraction of 4.880 ms seems to
    bring the spill start to about the right time.

    returns time in spill (ms)
    """

    v1290aray = Spill.GetDAQData()\
        .GetTOF1DaqArray()[event_number].GetV1290Array()

    time_tag = v1290aray[0].GetTriggerTimeTag()
    time = time_tag*0.8E-3 - 4.880

    return time
