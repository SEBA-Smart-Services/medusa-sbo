import datetime as dt
import pandas as pd
from app.models import AssetPoint, LoggedEntity, LogTimeValue, Asset
from app import db, app


class LogSampleFetcher(object):

    def __init__(self, asset_point_id):
        self.set_point(asset_point_id)
        self.set_site_id()
        self.set_logged_entity()

    def set_point(self, asset_point_id):
        self.point = AssetPoint.query.filter_by(id=asset_point_id).one()

    def set_site_id(self):
        asset = Asset.query.filter_by(id=self.point.asset_id).one()
        self.site_id = asset.site_id

    def set_logged_entity(self):
        self.logged_entity = LoggedEntity.query.filter_by(id=self.point.loggedentity_id, site_id=self.site_id).first()

    def range(
        self,
        start_datetime=dt.datetime.now() - dt.timedelta(days=1),
        end_datetime=dt.datetime.now(),
        as_list=False
    ):
        """
        return a series of log samples (datetimestamp, value)
        either as a list of lists or as a pandas series
        """
        app.logger.info("self.logged_entity.id: " + str(self.logged_entity.id))
        samples = LogTimeValue.query.filter(
            LogTimeValue.parent_id == self.logged_entity.id,
            LogTimeValue.datetimestamp >= start_datetime,
            LogTimeValue.datetimestamp <= end_datetime
        ).all()
        app.logger.info("samples: " + str(samples))
        if as_list:
            return self.to_list(samples)
        else:
            return self.to_series(samples)

    def to_series(self, samples):
        """
        convert samples to Pandas Series object
        """
        timestamps = [entry.datetimestamp for entry in samples]
        app.logger.info("samples: " + str(timestamps))
        values = [entry.float_value for entry in samples]
        app.logger.info("samples: " + str(values))

        # if list is empty, index is automatically assigned as Index rather than DatetimeIndex. So manually fix this
        if samples == []:
            timestamps = pd.DatetimeIndex([])

        series = pd.Series(values, index=timestamps)

        return series

    def to_list(self, samples):
        """
        convert samples to list of lists, eg:
            [
                ['2017-08-24 21:33:08', 23.22],
                ['2017-08-24 21:35:44', 23.41],
                ...
            ]
        """
        headers = [['Time', 'Value']]
        app.logger.info("headers: " + str(headers))
        series = [[entry.datetimestamp, entry.float_value] for entry in samples]
        if len(series) == 0:
            series = [[0, 0]]
        app.logger.info("series: " + str(series))
        sample_list = headers + series
        app.logger.info("samples: " + str(sample_list))
        return sample_list


    # def something(self):
    #     point = AssetPoint.query.filter(AssetPoint.type.has(name=point_name), AssetPoint.asset==self.asset).one()
    #     value_list = self.session.query(LogTimeValue).filter_by(parent_id=point.loggedentity_id).order_by(LogTimeValue.datetimestamp.desc()).limit(quantity).all()
    #     return self.to_series(value_list)
    #
    # # grab a fixed number of samples
    # def latest_qty(self, point_name, quantity):
    #     point = AssetPoint.query.filter(AssetPoint.type.has(name=point_name), AssetPoint.asset==self.asset).one()
    #     value_list = self.session.query(LogTimeValue).filter_by(parent_id=point.loggedentity_id).order_by(LogTimeValue.datetimestamp.desc()).limit(quantity).all()
    #     return self.to_series(value_list)
    #
    # # grab a time-based range of samples, ending at now
    # def latest_time(self, point_name, timedelta):
    #     point = AssetPoint.query.filter(AssetPoint.type.has(name=point_name), AssetPoint.asset==self.asset).one()
    #     value_list = self.session.query(LogTimeValue).filter(LogTimeValue.parent_id == point.loggedentity_id, LogTimeValue.datetimestamp >= datetime.datetime.now()-timedelta).all()
    #     return self.to_series(value_list)
    #
    # # grab a time-based range of samples, with defined start and end time
    # def time_range(self, point_name, timedelta_start, timedelta_finish):
    #     point = AssetPoint.query.filter(AssetPoint.type.has(name=point_name), AssetPoint.asset==self.asset).one()
    #     value_list = self.session.query(LogTimeValue).filter(LogTimeValue.parent_id == point.loggedentity_id, LogTimeValue.datetimestamp >= datetime.datetime.now()-timedelta_start, \
    #         LogTimeValue.datetimestamp <= datetime.datetime.now()-timedelta_finish).all()
    #     return self.to_series(value_list)
