import unittest
import api
from unittest.mock import Mock

from parameterized import parameterized
from i2c import I2CBus

class ModelValidationTests(unittest.TestCase):
 
    def setUp(self):
        self.i2cbus = I2CBus()
        self.i2cbus.read = Mock()
        self.i2cbus.write = Mock()
        self.i2cbus.ping = Mock() 
        
        self.app = api.create_app(self.i2cbus).test_client()

    @parameterized.expand([
        [
            'when_compensation_factor_missing', 
            'post', '/api/device/97/sample/compensation', 
            [{
                #'factor': 'salinity', is missing!
                'symbol': 'μS', 
                'value': '50000'
            }],
        ],
        [
            'when_compensation_factor_does_not_exist', 
            'post', '/api/device/97/sample/compensation', 
            [{
                'factor': 'not a real value',
                'symbol': 'μS', 
                'value': '50000'
            }],
        ],
        [
            'when_compensation_factor_unit_does_not_match_expected_units', 
            'post', '/api/device/97/sample/compensation', 
            [{
                'factor': 'salinity',
                'symbol': 'microcentury', 
                'value': '50000'
            }],
        ],
        [
            'when_compensation_symbol_missing',
            'post', '/api/device/97/sample/compensation',
            [{
                'factor': 'salinity', 
                #'symbol': 'μS', is missing!
                'value': '50000'
            }],
        ],
        [
            'when_compensation_value_missing',
            'post', '/api/device/97/sample/compensation',
            [{
                'factor': 'salinity', 
                'symbol': 'μS', 
                #'value': '50000' is missing!
            }],
        ],
    ])
    def test_should_return_invalid_request_error(self, name, method, url, request_body):

        self.i2cbus.read.side_effect = [ 
                b'\x01?I,DO,1.98\00',
            ]

        # Act
        http_method = getattr(self.app, method)
        response = http_method(url, json=request_body, follow_redirects=True)
        
        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(b'{"message": "Request contains a missing or incorrectly formatted felid.", "error_code": "INVALID_REQUEST_ERROR"}\n', response.data)

    @parameterized.expand([
        [
            'when_compensation_factor_does_not_exist_for_device', 
            'post', '/api/device/97/sample/compensation', 
            [{
                'factor': 'not a real value',
                'symbol': 'μS', 
                'value': '50000'
            }],
        ],
        [
            'when_compensation_factor_unit_does_not_match_the_expected_units', 
            'post', '/api/device/97/sample/compensation', 
            [{
                'factor': 'salinity',
                'symbol': 'microcentury', 
                'value': '50000'
            }],
        ],
        [
            'when_compensation_factor_value_was_not_a_float', 
            'post', '/api/device/97/sample/compensation', 
            [{
                'factor': 'salinity',
                'symbol': 'microcentury', 
                'value': 'not a float!'
            }],
        ],
    ])
    def test_should_return_invalid_request(self, name, method, url, request_body):
        self.i2cbus.read.side_effect = [ 
                b'\x01?I,DO,1.98\00',
            ]

        # Act
        http_method = getattr(self.app, method)
        response = http_method(url, json=request_body, follow_redirects=True)
        
        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(b'{"message": "Request contains a missing or incorrectly formatted felid.", "error_code": "INVALID_REQUEST_ERROR"}\n', response.data)


    @parameterized.expand([
        [
            'when_calibration_point_missing',
            'put', '/api/device/99/sample/calibration',
            {
                #'point': 'high', is missing!
                'actual_value': '10.0'
            },
        ],
        [
            'when_calibration_actual_value_missing',
            'put', '/api/device/99/sample/calibration',
            {
                'point': 'high', 
                # 'actual_value': '10.0' is missing!
            },
        ],
        [
            'when_calibration_point_was_not_an_expected_value',
            'put', '/api/device/99/sample/calibration',
            {
                'point': 'the_low_point',
                'actual_value': '10.0'
            },
        ],
        
        [
            'when_calibration_value_was_not_a_float',
            'put', '/api/device/99/sample/calibration',
            {
                'point': 'the_low_point',
                'actual_value': 'not a number'
            },
        ],
    ])
    def test_should_return_invalid_request_for_ph_device(self, name, method, url, request_body):
        self.i2cbus.read.side_effect = [ 
                b'\x01?i,pH,1.98\00' # pH device expects a calibration point
            ]

        # Act
        http_method = getattr(self.app, method)
        response = http_method(url, json=request_body, follow_redirects=True)
        
        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(b'{"message": "Request contains a missing or incorrectly formatted felid.", "error_code": "INVALID_REQUEST_ERROR"}\n', response.data)


if __name__ == '__main__':
    unittest.main()
