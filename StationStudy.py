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
        self.plane_hists = [ ROOT.TH1D("StnSty_PlaneHist_%s_%i_%i"%\
                                       (self.trkname,self.station, p),\
                                       "Tracker %s, Station %i, Plane %i; Channel No.; Events"%\
                                       (self.trkname,self.station, p),\
                                       n_ch, -0.5, n_ch-0.5)\
                             for p in range(3)]
		
        # Now construct the missing plane histograms:
        self.miss_plane_hists = [ ROOT.TH1D("StnSty_MissPlaneHist_%s_%i_%i"%\
                                       (self.trkname,self.station, p),\
                                       "Tracker %s, Station %i, Plane %i; Channel No.; Events"%\
                                       (self.trkname,self.station, p),\
                                       n_ch, -0.5, n_ch-0.5)\
                             for p in range(3)]

        # The hit type histogram:
        self.track_hit_type = ROOT.TH1D("StnSty_TrkHitType_%s_%i"%(self.trkname,self.station),\
                                        "Tracker %s, Station %i; HitType; Events"%(self.tracker,self.station),\
                                        4, -0.5, 3.5)

        self.sp_hit_type = ROOT.TH1D("StnSty_SPHitType_%s_%i"%(self.trkname,self.station),\
                                     "Tracker %s, Station %i; HitType; Events"%(self.tracker,self.station),\
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
        self.miss_plane_hists[missing_plane].Fill(318.5-kuno_sum)


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

        self.legends = []

        for p in range(3):
            self.c.cd(p+1)
            self.plane_hists[p].SetFillColor(ROOT.kGray)
            self.plane_hists[p].SetLineColor(ROOT.kBlack)
            self.plane_hists[p].Draw()
            self.plane_hists[p].GetYaxis().SetTitleOffset(1.4)
            self.miss_plane_hists[p].SetLineColor(ROOT.kRed)
            self.miss_plane_hists[p].Draw("SAME")
            
            self.legends.append(ROOT.TLegend(0.1,0.75,0.35,0.9))
            self.legends[-1].AddEntry(self.plane_hists[p], "Triplet Hits")
            self.legends[-1].AddEntry(self.miss_plane_hists[p], "Duplet Missed Hit")
            self.legends[-1].Draw()
        
        self.c.cd(4)
        self.track_hit_type.SetStats(False)
        self.track_hit_type.SetFillColor(ROOT.kGray)
        self.track_hit_type.SetLineColor(ROOT.kBlack)
        self.track_hit_type.Draw()
        self.track_hit_type.GetYaxis().SetRangeUser(0,self.track_hit_type.GetEntries())
        self.track_hit_type.GetYaxis().SetTitleOffset(1.4)
        self.sp_hit_type.Draw("SAME")

        self.legends.append(ROOT.TLegend(0.1,0.75,0.35,0.9))
        self.legends[-1].AddEntry(self.track_hit_type, "Spacepoints in Tracks")
        self.legends[-1].AddEntry(self.sp_hit_type, "All Spacepoints")
        self.legends[-1].Draw()


    def MakeResultsDict(self):
        """
        Summarise the output in the format of a dictionary
        """
        o = {}

        # Tracker info:
        o["tracker"] = self.tracker
        o["station"] = self.station
        o["trkname"] = self.trkname

        # Events which passed the TOF1/2 Cut.
        o["events"] = self.n_events

        # Events which had a track in the selected tracker
        o["tracks"] = self.n_tracks

        o["sp_triplets"] = self.sp_hit_type.GetBinContent(4)
        o["sp_duplets"] = self.sp_hit_type.GetBinContent(3)
        o["sp_miss"] = self.sp_hit_type.GetBinContent(1)
        
        o["sp_dupletratio"] = self.sp_hit_type.GetBinContent(3)/\
                              self.sp_hit_type.GetBinContent(4)

        o["track_triplets"] = self.track_hit_type.GetBinContent(4)
        o["track_duplets"] = self.track_hit_type.GetBinContent(3)
        o["track_miss"] = self.track_hit_type.GetBinContent(1)

        o["track_dupletratio"] = self.track_hit_type.GetBinContent(3)/\
                                 self.track_hit_type.GetBinContent(4)

        
        # Compute "Efficiencies"
        o["track_eff"] =  (o["track_triplets"] + o["track_duplets"])/\
                          ( o["track_miss"] + o["track_duplets"] + o["track_triplets"] )

        # We assume a duplet/triplet rate from the tracks, and use the
        # number of observed spacepoint triplets to determine efficiency.
        o["sp_eff"] = (o["sp_triplets"]*(1.+o["track_dupletratio"]))/\
                      ( o["sp_miss"] +  o["sp_duplets"] + o["sp_triplets"])

        # Estimate the duplet noise rate.
        o["duplet_noise"] = o["sp_dupletratio"] - o["track_dupletratio"]
        
        
        return o

