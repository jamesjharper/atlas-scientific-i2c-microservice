#!flask/bin/python

from enum import Enum

class AtlasScientificError(Exception):
    pass

class AtlasScientificDeviceNotReadyError(AtlasScientificError):
    pass

class AtlasScientificSyntaxError(AtlasScientificError):
    pass

class AtlasScientificNoDeviceAtAddress(AtlasScientificError):
    pass

class AtlasScientificResponseSyntaxError(AtlasScientificError):

    def __init__(self, felid, message):
        self.felid = felid
        self.message = message

class RequestResult(Enum):
    OK = 1
    SYNTAX_ERROR = 2
    NOT_READY = 254
    ACK = 255  # ok with no message response body

class AtlasScientificResponse(object):
    def __init__(self, response_bytes, response_timestamp):
        self.response_timestamp = response_timestamp

        try:
            self.status = RequestResult(response_bytes[0])
        except Exception as err:
            raise AtlasScientificResponseSyntaxError('status', str(err))
        
        try:
            if self.status == RequestResult.OK:
                # omit first byte, as it's the status bytes,
                # find the response length to strip the unused data
                length = AtlasScientificResponse.__find_response_length(response_bytes)
                self.attributes = response_bytes[1:length].decode('ascii').split(",")
            else:
                self.attributes = []
        except Exception as err:
            raise AtlasScientificResponseSyntaxError('body', str(err))


    def get_field(self, name, index):
        try:
            return self.attributes[index]
        except IndexError:
            raise AtlasScientificResponseSyntaxError(name, "expected field missing from response")
        except Exception as err:
            raise AtlasScientificResponseSyntaxError(name, str(err))

    def get_fields(self, name, start, end):
        try:
            return self.attributes[start:end]
        except IndexError:
            raise AtlasScientificResponseSyntaxError(name, "expected fields missing from response")
        except Exception as err:
            raise AtlasScientificResponseSyntaxError(name, str(err))

    @staticmethod
    def __find_response_length(response_bytes):
        # omit content after the first x00, as the device
        # may return more bytes then expected.
        l = response_bytes.find(b'\x00')
        # if no x00 was found, assume all bytes contain data    
        return l if l != -1 else None

class AtlasScientificDeviceOutput(object): 
    def __init__(self, device_response):
        # expected format ?O,%,MG"
        self.units = device_response.get_fields('output', 1, None)    

class AtlasScientificDeviceInfo(object): 
    def __init__(self, device_response, address):
        self.device_type = device_response.get_field('device_type', 1)
        self.version = device_response.get_field('version', 2)
        self.address = address
        self.vendor = 'atlas-scientific'

class AtlasScientificDeviceSample(object): 
    def __init__(self, symbol, value, value_type, timestamp):
        self.symbol = symbol
        self.value = value
        self.value_type = value_type
        self.timestamp = timestamp

    @staticmethod
    def from_expected_device_output(device_response, expected_output_units):

        result = []
        unit_index = 0
        for unit in expected_output_units:
            value = device_response.get_field('sample', unit_index)
            result.append(AtlasScientificDeviceSample(unit.symbol, value, unit.value_type, device_response.response_timestamp))
            unit_index = unit_index + 1
        return result
        
class AtlasScientificDeviceCompensationFactors(object): 
    def __init__(self, device_compensation_factors):      
        factors = (AtlasScientificDeviceCompensationFactor(f) for f in device_compensation_factors)
        self.factors = {f.factor:f for f in factors}

class AtlasScientificDeviceCompensationFactor(object): 
    def __init__(self, device_compensation_factor):
        
        # TODO: throw error if values are missing
        self.factor = device_compensation_factor.get('factor', None)
        self.symbol = device_compensation_factor.get('symbol', None)
        self.value = device_compensation_factor.get('value', None)


class AtlasScientificDeviceCalibrationPoint(object): 
    def __init__(self, calibration_point):        
        # TODO: throw error if values are missing
        self.point = calibration_point.get('point', None)
        self.actual_value = calibration_point.get('actual_value', None)