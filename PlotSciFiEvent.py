"""
Tool to plot the SciFi Event
"""

import ROOT
import math


class PlotSciFiEvent:
    """
    A class to facilitate plotting the SciFi Event.
    """

    def __init__(self, name="s"):
        """
        Construct & setup class memorys...

        :type name: string
        :param name: "human readable" name to add to each histogram
        """
        self.prog_xz = True
        self.prog_yz = True

        self.name = name

        # Dynamicaly generate TGraphs for projections:
        for tracker in ["us", "ds"]:
            for track in ["str", "hel", "nat"]:
                for prj in ["zx", "zy", "xy", "zr", "zphi"]:
                    for typ in ["t","d"]:
                        obj_name = "tgpr_%s_%s_%s_%s" % (tracker, track, prj, typ)
                        tg = ROOT.TGraph()
                        # tg.SetName("%s_%s"(self.name, obj_name))
                        setattr(self, obj_name, tg)



        self.colors = {"str": ROOT.kBlue, "hel": ROOT.kGreen, "nat": ROOT.kRed}

    def fill(self, scifi_recon_event):
        """
        Perform the data filling.

        :type scifi_recon_event: MAUS.SciFiRecon
        :param scifi_recon_event: The recon event which wants to be plotted.
        """

        self.find_doubletstn(1, scifi_recon_event)

        for tracker in ["us", "ds"]:
            for track in ["str", "hel", "nat"]:
                for prj in ["zx", "zy", "xy", "zr", "zphi"]:
                    for typ in ["t", "d"]:
                        getattr(self, "tgpr_%s_%s_%s_%s" %
                                (tracker, track, prj, typ)).Set(0)

        for sp in scifi_recon_event.spacepoints():

            #if len ( sp.get_channels() ) == 2:
            #    continue

            tracker = "us" if sp.get_tracker() == 0 else "ds"
            track = "nat"

            # Find track:
            # TODO:  Look for is used flag
            find_npe = sp.get_npe()

            for trk in scifi_recon_event.straightprtracks():
                if sp in trk.get_spacepoints():
                    track = "str"

            for trk in scifi_recon_event.helicalprtracks():
                if sp in trk.get_spacepoints():
                    if track == "str":
                        print "already found a straight, but its helical!"
                    track = "hel"

            if len ( sp.get_channels() ) == 2:
                typ = "d"
            else:
                typ = "t"

            pos = sp.get_position()

            tg_zx = getattr(self, "tgpr_%s_%s_%s_%s" % (tracker, track, "zx", typ))
            tg_zx.SetPoint(tg_zx.GetN(), pos.z(), pos.x())

            tg_zy = getattr(self, "tgpr_%s_%s_%s_%s" % (tracker, track, "zy", typ))
            tg_zy.SetPoint(tg_zy.GetN(), pos.z(), pos.y())

            tg_xy = getattr(self, "tgpr_%s_%s_%s_%s" % (tracker, track, "xy", typ))
            tg_xy.SetPoint(tg_xy.GetN(), pos.x(), pos.y())

            radius = math.sqrt(pos.x()*pos.x() + pos.y()*pos.y())
            tg_zr = getattr(self, "tgpr_%s_%s_%s_%s" % (tracker, track, "zr", typ))
            tg_zr.SetPoint(tg_zr.GetN(), pos.z(), radius)
            
            phi = math.atan2(pos.y(), pos.x())
            tg_zt = getattr(self, "tgpr_%s_%s_%s_%s" % (tracker, track, "zphi", typ))
            tg_zt.SetPoint(tg_zt.GetN(), pos.z(), phi)

    def draw(self):
        """
        Function to cause drawing of the plots...
        """

        self.c = ROOT.TCanvas("c", "c", 1024, 768)

        self.c.Divide(3, 2)

        # Top Left:
        for i, tracker in enumerate(["us", "ds"]):
            for j, prj in enumerate(["zr", "zphi", "xy"]):

                self.c.cd(i*3+j+1)

                # Generate a multi graph:
                mg = ROOT.TMultiGraph()
                for track in ["str", "hel", "nat"]:
                    for typ in ["t","d"]:
                        tg = getattr(self, "tgpr_%s_%s_%s_%s" % (tracker, track, prj, typ))
                        if tg.GetN() > 0:
                            mg.Add(tg, "p")
                            tg.SetMarkerColor(self.colors[track])
                            if typ == "t":
                                tg.SetMarkerStyle(20)
                            else:
                                tg.SetMarkerStyle(24)

                mg.Draw("a")
                setattr(self, "mg_%s_%s" % (tracker, prj), mg)
                try:
                    if j == 3:
                        mg.GetXaxis().SetRangeUser(-150, 150)
                    mg.GetYaxis().SetRangeUser(-150, 150)
                except:
                    pass


    def find_doubletstn(self, tracker, scifi_recon_event):

        station_triplet = [False]*5
        for sp in scifi_recon_event.spacepoints():
            if sp.get_tracker() == tracker and\
               len(sp.get_channels()) == 3:
                station_triplet[sp.get_station()-1]=True

        for i, found in enumerate (station_triplet):
            if not found:
                #print "Tracker:%i, Station:%i"%(tracker, i+1)
                #self.list_clusters(tracker, i+1, scifi_recon_event)
                self.list_doublet_breakdown(tracker, i+1, scifi_recon_event)


    def list_clusters(self, tracker, station, scifi_recon_event):        
        for c in scifi_recon_event.clusters():
            if c.get_tracker() == tracker and\
               c.get_station() == station:

                print c.get_plane(), c.get_channel(), c.is_used(), c.get_npe()


    def list_doublet_breakdown(self, tracker, station, scifi_recon_event):

        found_clusters = []

        print ""
        print ""
        print "Tracker:%i, Station:%i"%(tracker, station)
        for sp in scifi_recon_event.spacepoints():
            if sp.get_tracker() == tracker and\
               sp.get_station() == station:

                print "SP: %f, %f"%(sp.get_position().x(), sp.get_position().y())
                for c in sp.get_channels():
                    found_clusters.append(c)
                    print " + C:", c.get_plane(), c.get_channel(), c.is_used(), c.get_npe()
                print ""

        print "UNASSIGNED:"
        for c in scifi_recon_event.clusters():
            if c.get_tracker() == tracker and\
               c.get_station() == station and\
               not c in found_clusters:
                
                print c.get_plane(), c.get_channel(), c.is_used(), c.get_npe()
