#!/usr/bin/env python



""" perdiemmodel.py
This module implements classes which determine the behavior of routes
with respect to perdiem- how much is paid and under what circumstances
"""

_hermes_svn_id_="$Id$"

import ipath

class PerDiemModel:
    """
    A representation of the perdiem policy of a route.
    """
    def __init__(self):
        """
        This is the base class; the user is not expected to instantiate
        this type directly.
        """
        pass

    def __str__(self):
        return "<PerDiemModel>"

    def calcPerDiemDays(self, tripJournal, homeWH):
        """
        This function is called once at the end of each full round trip for any
        shipping process to calculate the number of days of per diem pay the
        driver is to receive, based on the details of the just- completed trip.

        tripJournal is a list of tuples describing the steps of the
        just-completed trip.  tripJournal entries all start with
        (stepname, legStartTime, legEndTime, legConditions...);
        see the description of warehouse.createTravelGenerator for additional
        details.

        homeWH is the warehouse which is the driver's 'home'; that is, where
        the driver might be expected to sleep for free. Typically legEndTime
        for one leg will equal legStartTime for the next.

        The return value of this function is expected to be a number.
        """
        raise RuntimeError("PerDiemModel.calcPerDiemDays called")

    def calcPerDiemAmountTriple(self, tripJournal, homeWH):
        """
        This function is called once at the end of each full round trip for any
        shipping process to calculate the per diem pay the driver is to
        receive, based on the details of the just- completed trip.

        tripJournal is a list of tuples describing the steps of the
        just-completed trip.  tripJournal entries all start with
        (stepname, legStartTime, legEndTime, legConditions...);
        see the description of warehouse.createTravelGenerator for additional
        details.

        homeWH is the warehouse which is the driver's 'home'; that is, where
        the driver might be expected to sleep for free. Typically legEndTime
        for one leg will equal legStartTime for the next.

        The return value of this function is expected to to be a tuple
        of the form (amount, currencyCode, baseYear).
        """
        raise RuntimeError("PerDiemModel.calcPerDiemAmountTriple called")
