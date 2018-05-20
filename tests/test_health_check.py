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
import unittest
import index
import os
import json


SHARED_SECRET = 'test123'
os.environ['shared_secret'] = SHARED_SECRET


class TestHealthCase(unittest.TestCase):

    def test_health_response(self):

        event = {
            "verb": "HealthCheck",
            "mya_property_id": "",
            "ota_property_id": "",
            "shared_secret": SHARED_SECRET
        }

        result = index.router(event, None)

        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(result['headers']['Content-Type'], 'application/json')

        body = json.loads(result['body'])
        self.assertFalse('errors' in body)
        self.assertEqual(body['success'], True)

    def test_missing_property_id(self):

        event = {
            "verb": "HealthCheck",
            "ota_property_id": "",
            "shared_secret": SHARED_SECRET
        }

        result = index.router(event, None)

        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(result['headers']['Content-Type'], 'application/json')

        body = json.loads(result['body'])
        self.assertTrue('errors' in body)
        self.assertEqual(body['success'], False)

    def test_bad_health_response(self):

        event = {
            "verb": "HealthCheck",
            "mya_property_id": "",
            "ota_property_id": "",
            "shared_secret": 'wrong password'
        }

        result = index.router(event, None)

        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(result['headers']['Content-Type'], 'application/json')

        body = json.loads(result['body'])
        self.assertEqual(len(body['errors']), 1)
        self.assertEqual(body['success'], False)

    def test_health_response_body(self):

        body = {
            "verb": "HealthCheck",
            "mya_property_id": "",
            "ota_property_id": "",
            "shared_secret": SHARED_SECRET
        }
        event = {
            'body': json.dumps(body)
        }

        result = index.router(event, None)

        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(result['headers']['Content-Type'], 'application/json')

        body = json.loads(result['body'])
        self.assertFalse('errors' in body)
        self.assertEqual(body['success'], True)

    def test_missing_shared_secret(self):

        body = {
            "verb": "HealthCheck",
            "mya_property_id": "",
            "ota_property_id": ""
        }
        event = {
            'body': json.dumps(body)
        }

        result = index.router(event, None)

        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(result['headers']['Content-Type'], 'application/json')

        body = json.loads(result['body'])
        self.assertTrue('errors' in body)
        self.assertEqual(len(body['errors']), 1)
        self.assertEqual(body['success'], False)


if __name__ == '__main__':
    unittest.main()
