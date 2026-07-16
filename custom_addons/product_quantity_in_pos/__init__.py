from . import models

def _enable_storage_locations(env):
    location = env['res.config.settings'].create({'group_stock_multi_locations':True})
    location.set_values()
