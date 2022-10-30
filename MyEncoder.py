# -*- coding: utf-8 -*-
# Created by panlong on 2021/7/30
# Copyright (c) 2021 panlong. All rights reserved.

import json


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return str(obj, encoding='utf-8')

        return json.JSONEncoder.default(self, obj)
