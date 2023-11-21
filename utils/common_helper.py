class Common:
    @staticmethod
    def get_wace_against_due_date(ce_json_new: dict, ce_json_old: dict) -> dict:
        """
        helper function to find the (WACE) weighted average collection efficiency for a particular due date using
        new user's collection efficiency data and old user's collection efficiency data
        :param ce_json_new: collection efficiencies for new users for a particular nbfc for a particular date
        :param ce_json_old: collection efficiencies for new users for a particular nbfc for a particular date
        collection efficiencies in both dicts are in floats like 0.045, 0.0007, 0.25 etc.
        :return: a json containing ce's we for all dps ( Delay in payment date) for a particular due_date
        Weighted Average Collection Efficiency= [(%of loans given to new user * CE)+(%of loans given to old user * CE)]
        """
        wace_dict = {}
        for dpd in range(-7, 46):
            ce_avg = 0
            if str(dpd) in ce_json_new:
                ce_avg += ce_json_new[str(dpd)]
            if str(dpd) in ce_json_old:
                ce_avg += ce_json_old[str(dpd)]

            dpd_date = str(dpd)
            wace_dict[dpd_date] = ce_avg

        return wace_dict
