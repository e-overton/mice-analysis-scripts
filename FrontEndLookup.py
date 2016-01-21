#!/usr/bin/env python
"""
Simple class to facilitate 

"""
import json

try:
    from cdb import Calibration, Cabling
except:
    print "CDB interface unavailable"
    CDB_AVAIL = False
else:
    print "CDB interface available"
    CDB_AVAIL = True

# Definitions:
N_Channel = 216
N_Station = 5
N_Plane = 3
N_Tracker = 2

N_Board = 16
N_Bank = 4
N_ChBank = 128
N_ChanUIDS = N_Board*N_Bank*N_ChBank


class FrontEndLookup:
    """
    Front end lookup class, used to determine the exact board and
    channel, from which the hit originated, using the MAUS mapping.
    The MAUS calibration is then used to determine the saturation
    point.
    """

    def __init__(self, mapping_filepath=None, calibration_filepath=None,
                 badchannels_filepath=None, runid=None):
        """
        Constructor requires the path of the mapping and
        calibration to initilise the object.
        """
        # Mapping processing (file or cdb):
        if mapping_filepath is not None:
            with open(mapping_filepath, "r") as f:
                self.mapping = self.ParseMapping(f)
        elif runid is not None and CDB_AVAIL:
            # Perform CDB operations to retrive mapping..
            cdb_mapping = Cabling().get_cabling_for_run('Trackers', runid)
            self.mapping = self.ParseMapping(cdb_mapping.split('\n'))
        else:
            raise ValueError("Unable to load mapping, no methods available")

        # Mapping processing (file or cdb):
        if calibration_filepath is not None:
            with open(calibration_filepath, "r") as f:
                self.calibration = self.ParseCalibration(f.read())
        elif runid is not None and CDB_AVAIL:
            # Perform CDB operations to retrive mapping..
            cdb_calib = Calibration().get_calibration_for_run('Trackers', 
                                                              runid, 'trackers')
            print cdb_calib
            self.calibration = self.ParseCalibration(cdb_calib)
        else:
            raise ValueError("Unable to load calibration, no methods available")

        #self.mapping = self.LoadMapping(mapping_filepath)
        #self.calibration = self.LoadCalibration(calibration_filepath)

        if badchannels_filepath is not None:
            self.badfechannels = self.LoadBadChannelUIDs(badchannels_filepath)
        else:
            self.badfechannels = []

        # Lookup object, for finding things.
        self.lookup = self.GenerateLookup(self.mapping, self.calibration, self.badfechannels)

        # Missing channels from a given plane
        self.badplanelookup = self.GeneratePlaneBadLookup(self.lookup)

    def GetChannel(self, tracker, station, plane, channel):
        """
        Use the internal lookup to return all known infomation
        from a channel.
        """

        c = self.lookup[self._get1dref(tracker, station, plane, channel)]

        # validate channel:
        good = True

        try:
            if tracker != c["tracker"]:
                print "tracker mismatch"
                good = False

            if station != c["station"]:
                print "station mismatch"
                good = False

            if plane != c["plane"]:
                print "plane mismatch"
                good = False

            if channel != c["trchannel"]:
                print "channel mismatch"
                good = False
        except:
            raise LookupError("Exception in lookup")
            good = False

        if not good:
            print "Plane mismatch "
            raise LookupError("Tracker station plane do not match")

        return c

    def GetChannelSaturationPE(self, tracker, station, plane, channel):
        """
        Function to compute the saturation in PE of a channel.
        """

        # If we fail, return 0.
        try:
            channel = self.GetChannel(tracker, station, plane, channel)

            # Saturation is when the adc is 255:
            saturation = (255. - channel["adc_pedestal"])/channel["adc_gain"]

        except:
            saturation = 0

        return saturation

    def GetBadChannelsPlane(self, tracker, station, plane):
        """
        Get all the bad channels for a given plane in the detector.
        """
        planeid = self._getPlaneRef(tracker, station, plane)

        return self.badplanelookup[planeid]

    def LoadMapping(self, fname):
        """
        Not used.
        Load a channel map into a lookup which can be used to
        convert from the electronics numbering to the internal
        station numbering.
        """

        M = [{} for i in range(N_ChanUIDS)]

        # Load Map:
        with open(fname, "r") as f:
            pass

    def ParseMapping(self, mapping_str):
        """
        Function to parse the mapping into a lookup which can be
        used to convert from the electronics numbering to the 
        internal station numbering.
        """
        M = [{} for i in range(N_ChanUIDS)]
        for line in mapping_str:
            # Load and split line...
            words = line.split()
            if len(words) < 3:
                continue
            board = int(words[0])
            bank = int(words[1])
            elchannel = int(words[2])
            channelUID = board*512 + bank*128 + elchannel
            # Output Map
            M[channelUID]["channelUID"] = channelUID
            M[channelUID]["board"] = board
            M[channelUID]["bank"] = bank
            M[channelUID]["elchannel"] = elchannel
            M[channelUID]["tracker"] = int(words[3])
            M[channelUID]["station"] = int(words[4])
            M[channelUID]["plane"] = int(words[5])
            M[channelUID]["trchannel"] = int(words[6])

        return M

    def LoadCalibration(self, fname):
        """
        Load a calibration from the file to help generate the
        lookup infomation.
        """

        output = [{}] * N_ChanUIDS  # for i in range(N_ChanUIDS)]

        # Load file
        with open(fname, "r") as f:
            pass

    def ParseCalibration(self, calibration_str):
        """
        Parse a string into json, and then generate the
        calibration lookup for use..
        """
        output = [{}] * N_ChanUIDS  # for i in range(N_ChanUIDS)]
        calib = json.loads(calibration_str)
        # Expand / arrange Calibration:
        for c in calib:
            channelUID = 128*c["bank"] + c["channel"]
            c["ChannelID"] = channelUID
            output[channelUID] = c

        return output

    def LoadBadChannelUIDs(self, fname):
        """
        Process an existing "bad channels" list to determine
        the bad channels in the detector. Returns channel
        unique identifiers.
        """
        badlUIDs = []

        with open(fname, "r") as f:
            for l in f:
                bad_bank, bad_channel = l.split()
                badlUIDs.append(self._getUID(bank=int(bad_bank),
                                             channel=int(bad_channel)))

        return badlUIDs

    def GeneratePlaneBadLookup(self, lookup):
        """
        Use the lookup to generate a faster "plane lookup" where
        the bad channels for each tracker, station, and plane
        are stored.
        """
        badplanelookup = [[] for i in range(self._getPlaneRef
                                            (N_Tracker, 1, 0))]

        for c in lookup:

            try:
                if c["bad"]:
                    planeid = self._getPlaneRef(c["tracker"], c["station"],
                                                c["plane"])
                    badplanelookup[planeid].append(c["trchannel"])

            except (KeyError, TypeError):
                continue

        return badplanelookup

    def GenerateLookup(self, mapping, calibration, baduids=[]):
        """
        Functionality to create a lookup from the mapping:
        """

        lookup = [None] * self._get1dref(N_Tracker, 1, 0, 0)

        # Collect infomation from the mapping and calibration:
        for channelUID in range(N_ChanUIDS):

            # Combine data from maps:
            c = mapping[channelUID]

            # Check the channelUID has a tracker in it.
            if "tracker" in c:
                for key in ["tdc_gain", "adc_gain", "tdc_pedestal",
                            "adc_pedestal"]:
                    c[key] = calibration[channelUID][key]
                # Apply bad channnels
                if channelUID in baduids:
                    c["bad"] = True
                else:
                    c["bad"] = False


                lookup[self._get1dref(c["tracker"], c["station"], c["plane"],
                                      c["trchannel"])] = c

        return lookup

    def _get1dref(self, tracker, station, plane, channel):
        """
        Get a 1 dimenstional referference which can be used to find the
        channel in tracker space.
        """
        ref = channel + (plane + (station-1 + tracker*N_Station)*N_Plane)*N_Channel
        return ref

    def _getPlaneRef(self, tracker, station, plane):
        """
        Get a 1 dimenstional reference for each plane, which is unique
        """
        ref = plane + (station-1 + tracker*N_Station)*N_Plane
        return ref

    def _getUID(self, board=0, bank=0, channel=0):
        """
        Get the UID, for both conventions. If no board is specified
        then the convention is that the bank runs 0-63.
        """
        return board*512 + bank*128 + channel


class LookupException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
