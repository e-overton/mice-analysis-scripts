#!/usr/bin/env python

"""
Store infomation from a single station which may be useful
at some later point..
"""

import ROOT
from TOFTools import TOF12Coincidence


class StationStudy:

    def __init__(self, tracker, station):
        """
        Constructor for class object.
        """
		
        # The tracker to examine
        self.tracker = tracker
        self.trkname = "US" if tracker == 0 else "DS"
        
        # The staion to examine
        self.station = station

        n_ch = 220
		
        # Plane histograms for the selected plane:
        self.plane_hists = [ ROOT.TH1D("StnSty_PlaneHist_%i_%i_%i"%\
                                       (self.tracker,self.station, p),\
                                       "Tracker %i, Station %i, Plane %i; Channel No.; Events"%\
                                       (self.tracker,self.station, p),\
                                       n_ch, -0.5, n_ch-0.5)\
                             for p in range(3)]
		
        # Now construct the missing plane histograms:
        self.miss_plane_hists = [ ROOT.TH1D("StnSty_MissPlaneHist_%i_%i_%i"%\
                                       (self.tracker,self.station, p),\
                                       "Tracker %i, Station %i, Plane %i; Channel No.; Events"%\
                                       (self.tracker,self.station, p),\
                                       n_ch, -0.5, n_ch-0.5)\
                             for p in range(3)]

        # The hit type histogram:
        self.track_hit_type = ROOT.TH1D("StnSty_TrkHitType_%i_%i"%(self.tracker,self.station),\
                                        "Tracker %i, Station %i; HitType; Events"%(self.tracker,self.station),\
                                        4, -0.5, 3.5)

        self.sp_hit_type = ROOT.TH1D("StnSty_SPHitType_%i_%i"%(self.tracker,self.station),\
                                     "Tracker %i, Station %i; HitType; Events"%(self.tracker,self.station),\
                                     4, -0.5, 3.5)
        
        # Number of analysed events:
        self.n_events = 0
        self.n_tracks = 0

    def FillRecon (self, ReconEvent):
        """
        Fill these histograms from the ReconEvent.
        """

        # Check the TOF Coincidence, return if its not there:
        if not TOF12Coincidence(ReconEvent.GetTOFEvent()):
            return

        self.n_events += 1

        # Spacepoint type [0 = none, 1 = duplet, 2 = triplet]
        sp_track_type = 0
        sp_sp_type = 0
        track_in_tracker = False

        # Check the tracking:
        for track in ReconEvent.GetSciFiEvent().straightprtracks():
            for sp in track.get_spacepoints():

                # Check the tracker
                if ( self.tracker == sp.get_tracker() ):
                    track_in_tracker = True

                    #Check the station
                    if ( self.station == sp.get_station() ):
                        sp_track_type = len ( sp.get_channels() )
                        if len ( sp.get_channels() ) == 3:
                            self.FillTriplet(sp)
                        elif len ( sp.get_channels() ) == 2:
                            self.FillDuplet(sp)

        # Update track infomation from previous hunt.
        self.track_hit_type.Fill(sp_track_type)
        if track_in_tracker:
            self.n_tracks += 1

        # Collect infomation from the RAW spacepoints.
        for sp in ReconEvent.GetSciFiEvent().spacepoints():
            if ( self.tracker == sp.get_tracker() and\
                 self.station == sp.get_station() and\
                 sp_sp_type < len ( sp.get_channels() )):

                sp_sp_type = len ( sp.get_channels() )
        
        self.sp_hit_type.Fill(sp_sp_type)
        

    def FillTriplet(self,sp):
        """
        Functionality to fill a triplet spacepoint
        """
        for cluster in sp.get_channels():
            self.plane_hists[cluster.get_plane()].Fill(cluster.get_channel()) 


    def FillDuplet(self,sp):
        """
        Functionality to fill a duplet spacepoint
        """
        missing_plane = 3
        kuno_sum = 0
        for cluster in sp.get_channels():
            missing_plane -= cluster.get_plane()
            kuno_sum += cluster.get_channel()
        self.miss_plane_hists[missing_plane].Fill(318-kuno_sum)

    def MakeDrawCanvas(self):
        """
        Make and draw a canvas with a summary of the hits in.
        """
        self.c = ROOT.TCanvas("StationStudy_Tracker%i_Station%i"%\
                              (self.tracker,self.station),\
                              "StationStudy Tracker:%i Station:%i"%\
                              (self.tracker,self.station),\
                              800,600)
        
        self.c.Divide(2,2)

        for p in range(3):
            self.c.cd(p+1)
            self.plane_hists[p].SetFillColor(ROOT.kGray)
            self.plane_hists[p].SetLineColor(ROOT.kBlack)
            self.plane_hists[p].Draw()
            self.plane_hists[p].GetYaxis().SetTitleOffset(1.4)
            self.miss_plane_hists[p].SetLineColor(ROOT.kRed)
            self.miss_plane_hists[p].Draw("SAME")
        
        self.c.cd(4)
        self.track_hit_type.SetStats(False)
        self.track_hit_type.SetFillColor(ROOT.kGray)
        self.track_hit_type.SetLineColor(ROOT.kBlack)
        self.track_hit_type.Draw()
        self.track_hit_type.GetYaxis().SetRangeUser(0,self.track_hit_type.GetEntries())
        self.track_hit_type.GetYaxis().SetTitleOffset(1.4)
        self.sp_hit_type.Draw("SAME")
        
    def MakeResultsDict(self):
        """
        Summarise the output in the format of a dictionary
        """
        o = {}

        # Events which passed the TOF1/2 Cut.
        o["events"] = self.n_events

        # Events which had a track in the selected tracker
        o["tracks"] = self.n_tracks

        
        # The ratio of duplets to triplets in the spacepoints
        o["sp_dupletratio"] = self.sp_hit_type.GetBinContent(3)/\
                              self.sp_hit_type.GetBinContent(4)
        
        # The ratio of duplets to triplets in the tracks
        o["track_dupletratio"] = self.track_hit_type.GetBinContent(3)/\
                                 self.track_hit_type.GetBinContent(4)
        
        print o

