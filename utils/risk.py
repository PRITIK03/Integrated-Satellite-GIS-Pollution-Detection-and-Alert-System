"""
Shared risk assessment utilities for pollution detection system.
"""


class RiskAssessor:
    RISK_ORDER = [
        'good',
        'moderate',
        'unhealthy_sensitive',
        'unhealthy',
        'very_unhealthy',
        'hazardous',
    ]

    def __init__(self, thresholds):
        self.thresholds = thresholds

    def _level(self, value: float, thresholds: dict) -> str:
        if value <= thresholds['good']:
            return 'good'
        if value <= thresholds['moderate']:
            return 'moderate'
        if value <= thresholds['unhealthy_sensitive']:
            return 'unhealthy_sensitive'
        if value <= thresholds['unhealthy']:
            return 'unhealthy'
        if value <= thresholds['very_unhealthy']:
            return 'very_unhealthy'
        return 'hazardous'

    def assess(self, pm25: float, no2: float) -> str:
        pm25_risk = self._level(pm25, self.thresholds['PM2.5'])
        no2_risk = self._level(no2, self.thresholds['NO2'])
        return self.RISK_ORDER[max(self.RISK_ORDER.index(pm25_risk), self.RISK_ORDER.index(no2_risk))]


def assess_risk_level(pm25: float, no2: float, thresholds=None) -> str:
    from config import PollutionConfig
    return RiskAssessor(thresholds or PollutionConfig().POLLUTION_THRESHOLDS).assess(pm25, no2)
