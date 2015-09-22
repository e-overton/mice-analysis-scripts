#!/usr/bin/env python
"""
Simple class to facilitate 

"""
import json

# Definitions:
N_Channel = 230
N_Station = 5
N_Plane = 3
N_Tracker=2

N_Board=16
N_Bank=4
N_ChBank=128
N_ChanUIDS = N_Board*N_Bank*N_ChBank

class FrontEndLookup:
    """
    Front end lookup class, used to determine the exact board and
    channel, from which the hit originated, using the MAUS mapping.
    The MAUS calibration is then used to determine the saturation
    point.
    """

    def __init__(self, mapping_filepath, calibration_filepath):
        """
        Constructor requires the path of the mapping and 
        calibration to initilise the object.
        """
        self.mapping = self.LoadMapping(mapping_filepath)
        self.calibration = self.LoadCalibration(calibration_filepath)

        # Lookup object, for finding things.
        self.lookup = self.GenerateLookup(self.mapping, self.calibration)

    def GetChannel(self, tracker, station, plane, channel):
        
        c = self.lookup[tracker][station-1][plane][channel]
        
        # validate channel:
        good = True

        if tracker != c["tracker"]:
            print "tracker mismatch"
            good = False

        if station != c["station"]:
            print "station mismatch"
            good = False

        if plane != c["plane"]:
            print "plane mismatch"
            good = False

        if channel != c["trchan"]:
            print "channel mismatch"
            good = False


        #except:
        #    channel = None

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

    def LoadMapping (self,fname):
        """
        Load a channel map into a lookup which can be used to
        convert from the electronics numbering to the internal
        station numbering.
        """
    
        M = [{} for i in range(N_ChanUIDS)]
        
        # Load Map:
        with open(fname, "r") as f:
            for line in f:
                # Load and split line...
                words = line.split()
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
                M[channelUID]["trchan"] = int(words[6])

        return M

    def LoadCalibration (self,fname):
        """
        Load a calibration from the file to help generate the
        lookup infomation.
        """

        output = [{} for i in range(N_ChanUIDS)]

        # Load file
        with open(fname, "r") as f:
            calib = json.load(f)

            # Expand / arrange Calibration:
            for c in calib:
                channelUID = 128*c["bank"] + c["channel"]
                c["ChannelID"] = channelUID
                output[channelUID] = c

        return output


    def GenerateLookup(self, mapping, calibration):
        """
        Functionality to create a lookup from the mapping:
        """
        
        # Lookup in the format [tracker][station][plane][channel]
        lookup = []
        for tracker in range(N_Tracker):
            stations = []
            for station in range(N_Station):
                planes = []
                for plane in range(N_Plane):
                    channels = [None for channel in range(N_Channel)]
                    planes.append(channels)
                stations.append(planes)
            lookup.append(stations)

        # Collect infomation from the mapping and calibration:
        for channelUID in range (N_ChanUIDS):
        
            # Combine data from maps:
            c = mapping[channelUID]

            # Check the channelUID has a tracker in it.
            if "tracker" in c:
                for key in ["tdc_gain","adc_gain","tdc_pedestal","adc_pedestal"]:
                    c[key] = calibration[channelUID][key]

                # Now stick in the right place:
                lookup [c["tracker"]] [c["station"]-1] [c["plane"]] [c["trchan"]] = c

        return lookup
        
        
