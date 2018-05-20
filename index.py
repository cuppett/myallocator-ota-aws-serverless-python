#
# Copyright 2018 Stephen Cuppett
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import json

from controllers import SetupPropertyDatabaseController, GetRoomTypesDatabaseController
from controllers import GetBookingListController, GetBookingIdController, BaseController
from controllers import MA_OTA_PARAM_VERB


def router(event, context):
    # Body nested via API Gateway
    if 'body' in event:
        body = json.loads(event['body'])
    else:
        body = event

    if MA_OTA_PARAM_VERB in body and body[MA_OTA_PARAM_VERB] == 'SetupProperty':
        controller = SetupPropertyDatabaseController(body)
    elif MA_OTA_PARAM_VERB in body and body[MA_OTA_PARAM_VERB] == 'GetRoomTypes':
        controller = GetRoomTypesDatabaseController(body)
    elif MA_OTA_PARAM_VERB in body and body[MA_OTA_PARAM_VERB] == 'GetBookingList':
        controller = GetBookingListController(body)
    elif MA_OTA_PARAM_VERB in body and body[MA_OTA_PARAM_VERB] == 'GetBookingId':
        controller = GetBookingIdController(body)
    else:
        controller = BaseController(body)

    data = controller.handle()

    return {'statusCode': 200,
            'body': data,
            'headers': {'Content-Type': 'application/json'}}
