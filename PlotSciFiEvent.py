"""
Tool to plot the SciFi Event
"""

import ROOT


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
                for prj in ["zx", "zy", "xy"]:
                    obj_name = "tgpr_%s_%s_%s" % (tracker, track, prj)
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

        for tracker in ["us", "ds"]:
            for track in ["str", "hel", "nat"]:
                for prj in ["zx", "zy", "xy"]:
                    getattr(self, "tgpr_%s_%s_%s" %
                            (tracker, track, prj)).Set(0)

        for sp in scifi_recon_event.spacepoints():
            tracker = "us" if sp.get_tracker() == 0 else "ds"
            track = "nat"

            # Find track:
            find_npe = sp.get_npe()

            for trk in scifi_recon_event.straightprtracks():
                for tsp in trk.get_spacepoints():
                    if abs(tsp.get_npe() - find_npe) < 1E-3:
                        track = "str"

            for trk in scifi_recon_event.helicalprtracks():
                for tsp in trk.get_spacepoints():
                    if abs(tsp.get_npe() - find_npe) < 1E-3:
                        if track == "str":
                            print "already found a straight, but its helical!"
                        track = "hel"

            pos = sp.get_position()

            tg_zx = getattr(self, "tgpr_%s_%s_%s" % (tracker, track, "zx"))
            tg_zx.SetPoint(tg_zx.GetN(), pos.z(), pos.x())

            tg_zy = getattr(self, "tgpr_%s_%s_%s" % (tracker, track, "zy"))
            tg_zy.SetPoint(tg_zy.GetN(), pos.z(), pos.y())

            tg_xy = getattr(self, "tgpr_%s_%s_%s" % (tracker, track, "xy"))
            tg_xy.SetPoint(tg_xy.GetN(), pos.x(), pos.y())

    def draw(self):
        """
        Function to cause drawing of the plots...
        """

        self.c = ROOT.TCanvas("c", "c", 1024, 768)

        self.c.Divide(3, 2)

        # Top Left:
        for i, tracker in enumerate(["us", "ds"]):
            for j, prj in enumerate(["zx", "zy", "xy"]):

                self.c.cd(i*3+j+1)

                # Generate a multi graph:
                mg = ROOT.TMultiGraph()
                for track in ["str", "hel", "nat"]:
                    tg = getattr(self, "tgpr_%s_%s_%s" % (tracker, track, prj))
                    if tg.GetN() > 0:
                        mg.Add(tg, "p")
                        tg.SetMarkerColor(self.colors[track])
                        tg.SetMarkerStyle(20)

                mg.Draw("a")
                setattr(self, "mg_%s_%s" % (tracker, prj), mg)
