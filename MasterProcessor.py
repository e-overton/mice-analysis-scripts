"""
Master processor which assosiates scifi reconstruction
objects with each other, before calling the specific
function processor codes.

This means that the lowest level digit processors
process each digit, with assosiated infomation such
as spacepoints and tracks.
"""


class MasterProcessor:

    def __init__(self,
                 digit_processors=[],
                 cluster_processors=[],
                 spacepoint_processors=[],
                 straight_processors=[],
                 helical_processors=[]):
        """
        Store the processor functions. These must have a
        "process" function, which gets called.
        """
        self.digit_processors = digit_processors
        self.cluster_processors = cluster_processors
        self.spacepoint_processors = spacepoint_processors
        self.straight_processors = straight_processors
        self.helical_processors = helical_processors

    def reset(self):
        """
        Reset functionality, between spills
        """
        del self.recon

    def __call__(self, scifirecon):
        """
        Call the processor, this causes all data in the recon
        object to be processed by attached processors...
        """

        self.recon = scifirecon

        self._generateUnusedLists(self.recon)

        self._process()

        self._process_end()

        self.reset()

    def _generateUnusedLists(self, recon):
        """
        Generate unused lists from recon object
        """
        self.digits_used = [False]*len(recon.digits())
        self.clusters_used = [False]*len(recon.clusters())
        self.spacepoints_used = [False]*len(recon.spacepoints())
        self.straights_used = [False]*len(recon.straightprtracks())
        self.helicals_used = [False]*len(recon.helicalprtracks())

    def _process(self):
        """
        Sequentially process all data, from top to bottom, in order
        to include "unassiosated" things.
        """

        for h in range(len(self.helicals_used)):
            self._processHelical(self.recon.helicalprtracks()[h], h)

        for s in range(len(self.straights_used)):
            self._processStraight(self.recon.straightprtracks()[s], s)

        for sp in range(len(self.spacepoints_used)):
            if not self.spacepoints_used[sp]:
                self._processSpacepoint(self.recon.spacepoints()[sp],
                                        None)

        for c in range(len(self.clusters_used)):
            if not self.clusters_used[c]:
                self._processCluster(self.recon.clusters()[c],
                                     None, None)

        for d in range(len(self.digits_used)):
            if not self.digits_used[d]:
                self._processDigit(self.recon.digits()[d],
                                   None, None, None)

    def _processHelical(self, helical, helical_id):
        """
        For each helical track, process, process spacepoints,
        then set as done
        """

        for pro in self.helical_processors:
            pro.process(helical)

        for sp in helical.get_spacepoints():
            self._processSpacepoint(sp, helical)

        self.helicals_used[helical_id] = True

    def _processStraight(self, straight, straight_id):
        """
        For each straight track, process, process spacepoints,
        then set as done
        """
        for pro in self.straight_processors:
            pro.process(straight)

        for sp in straight.get_spacepoints():
            self._processSpacepoint(sp, straight)

        self.straights_used[straight_id] = True

    def _processSpacepoint(self, spacepoint, track):
        """
        For each spacepoint track, process, process clusters,
        then set as done.
        """
        for pro in self.spacepoint_processors:
            pro.process(spacepoint, track)

        for cluster in spacepoint.get_channels():
            self._processCluster(cluster, spacepoint, track)

        # Locate the spacepoint in the master list and flag
        # as processed.
        for i, evt_sp in enumerate(self.recon.spacepoints()):
            if (evt_sp.get_npe() == spacepoint.get_npe()):
                self.spacepoints_used[i] = True

    def _processCluster(self, cluster, spacepoint, track):
        """
        For each straight track, process, process digits,
        then set as done
        """
        for pro in self.cluster_processors:
            pro.process(cluster, spacepoint, track)

        for digit in cluster.get_digits():
            self._processDigit(digit, cluster, spacepoint, track)

        # Locate the spacepoint in the master list and flag
        # as processed.
        for i, evt_clst in enumerate(self.recon.clusters()):
            if (evt_clst.get_npe() == cluster.get_npe()):
                self.clusters_used[i] = True

    def _processDigit(self, digit, cluster, spacepoint, track):
        """
        For each straight track, process digit, then set as done.
        """
        for pro in self.digit_processors:
            pro.process(digit, cluster, spacepoint, track)

        # Locate the spacepoint in the master list and flag
        # as processed.
        for i, evt_digit in enumerate(self.recon.digits()):
            if (evt_digit.get_npe() == digit.get_npe()):
                self.digits_used[i] = True

    def _process_end(self):
        """
        Call a process_end function on all processors
        to do any "end of recon" tasks.
        """

        for process_list in [self.digit_processors,
                             self.cluster_processors,
                             self.spacepoint_processors,
                             self.straight_processors,
                             self.helical_processors]:

            for process in process_list:
                # try:
                process.process_end(self.recon)
                # except AttributeError:
                #    continue


class dummy_digit_processor:

    def process(self, digit, cluster, spacepoint, track):
        print ("digit: %r, cluster %r, spacepoint %r, track %r" %
               ((digit is not None), (cluster is not None),
                (spacepoint is not None), (track is not None)))

