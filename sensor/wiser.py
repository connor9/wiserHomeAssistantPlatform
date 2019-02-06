"""
Sensor Platform Device for Wiser System


https://github.com/asantaga/wiserHomeAssistantPlatform
Angelo.santagata@gmail.com

"""
import logging

import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.const import ATTR_BATTERY_LEVEL
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.icon import icon_for_battery_level
from homeassistant.const import (
    CONF_ENTITY_NAMESPACE,
    STATE_UNKNOWN, ATTR_ATTRIBUTION)

_LOGGER = logging.getLogger(__name__)
DOMAIN = "wiser"


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    handler = hass.data[DOMAIN] # Get Handler
    handler.update()

    wiserDevices= []

    _LOGGER.debug('sensor-setup_platform-get_all_devices+hot_water')
    # Process  general devices
    for device in handler.getWiserHubManager().get_all_devices():
        wiserDevices.append(WiserDevice(device.id, handler, device.product_type)) #wiserDevices.append(WiserDevice(device.get('id'),handler,device.get("ProductType")))

    wiserDevices.append(WiserSystemCircuitState(handler,"HEATING"))

    # Dont display Hotwater if hotwater not supported
    # https://github.com/asantaga/wiserHomeAssistantPlatform/issues/8
    if handler.getWiserHubManager().has_hot_water():
        wiserDevices.append(WiserSystemCircuitState(handler,"HOTWATER"))

    wiserDevices.append(WiserSystemCloudSensor(handler))
    wiserDevices.append(WiserSystemOperationModeSensor(handler))

    add_devices(wiserDevices)
    

""" 
Definition of Wiser Device
"""
class WiserDevice(Entity):
    def __init__(self, deviceId,handler,sensorType):
            
        """Initialize the sensor."""
        _LOGGER.info('Wiser Device Init')
      
        self.handler=handler
        self.deviceId=deviceId
        self.sensorType=sensorType

    def update(self):
        _LOGGER.debug('**********************************')
        _LOGGER.debug('Wiser Device Update requested')
        _LOGGER.debug('**********************************')
        self.handler.update()

    @property
    def icon(self):
        iconList={
                'Poor':'mdi:wifi-strength-1',
                'Medium':'mdi:wifi-strength-2',
                'Good':'mdi:wifi-strength-3',
                'VeryGood':'mdi:wifi-strength-4'
                }
        try:
            _LOGGER.debug('icon - get_Device %s',self.deviceId)
            return iconList[self.handler.getWiserHubManager().get_device(self.deviceId).displayed_signal_strength]
        except KeyError as ex:
            # Handle anything else as no signal
            return 'mdi:wifi-strength-alert-outline'

    @property
    def name(self):
        #Return the name of the Device
        _LOGGER.debug('name - get_Device %s',self.deviceId)
        device = self.handler.getWiserHubManager().get_device(self.deviceId)
        
        productType = type(device)

        if (productType == "draytonwiser.device.Controller"):
            return "Wiser Heathub"  # Only ever one of these
        elif (productType =="draytonwiser.device.iTRV" or "draytonwiser.device.RoomStat"):
            device_room_name = "Unknown"
            if device.room_id is not None:
                _LOGGER.debug('name - get_Device + get_room %s',device.room_id)
                device_room = self.handler.getWiserHubManager().get_room(device.room_id)
                device_room_name = device_room.name

            return "Wiser " + device.product_type + "-" + device_room_name # Multiple ones get automagically number _n by HA
        else:
            return "Wiser "+ device.product_type + "-" + str(device.serial_number)
 
    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    #Assumption 32 = 100% battery
    @property
    def battery_level(self):
        _LOGGER.debug('battery_level - get_Device %s',self.deviceId)
        return self.handler.getWiserHubManager().get_device(self.deviceId).get_battery_percentage()
    
    @property
    def device_state_attributes(self):
        _LOGGER.debug('State attributes for {} {}'.format(self.deviceId,self.sensorType))

        attrs={}
        _LOGGER.debug('device_state_attributes - get_Device %s',self.deviceId)
        device = self.handler.getWiserHubManager().get_device(self.deviceId)
        # Generic attributes
        attrs['vendor'] = "Drayton Wiser"
        attrs['product_type']= device.product_type
        attrs['model_identifier'] = device.model_identifier
        attrs['device_lock_enabled'] = device.device_lock_enabled
        attrs['displayed_signal_strength'] = device.displayed_signal_strength
        attrs['firmware'] = device.active_firmware_version

        # if device.reception_of_device != None:
        #     attrs['device_reception_RSSI'] = device.rReception_of_device["Rssi"]
        #     attrs['device_reception_LQI'] = device.rReception_of_device["Lqi"]
            
        # if deviceData.get("ReceptionOfController")!=None:
        #     attrs['controller_reception_RSSI'] = deviceData.get("ReceptionOfController").get("Rssi")
        #     attrs['device_reception_LQI'] = deviceData.get("ReceptionOfController").get("Lqi")
            
        if self.sensorType in ['RoomStat','iTRV','SmartPlug']:
            attrs['battery_voltage']=device.battery_voltage
            attrs['battery_level']=device.battery_level
            attrs['serial_number']=device.serial_number

        if self.sensorType=='RoomStat':
            attrs['humidity']=device.measurement.measured_humidity

        return attrs
    @property
    def state(self):
        _LOGGER.debug('**********************************')
        _LOGGER.debug('Wiser Device state requested deviceId : %s',self.deviceId)
        _LOGGER.debug('**********************************')

        _LOGGER.debug('state - get_Device %s',self.deviceId)
        return self.handler.getWiserHubManager().get_device(self.deviceId).displayed_signal_strength
        

""" 
Specific Sensor to display the status of heating or water circuit
"""
class WiserSystemCircuitState(Entity):
    # circuitType is HEATING HOTWATER
    def __init__(self,handler,circuitType):
            
        """Initialize the sensor."""
        _LOGGER.info('Wiser Circuit Sensor Init')
        self.handler = handler
        self.circuitType = circuitType

    def update(self):
        _LOGGER.debug('**********************************')
        _LOGGER.debug('Wiser Cloud Circut status Update requested')
        _LOGGER.debug('**********************************')
        self.handler.update()
    @property
    def icon(self):
        if self.circuitType=='HEATING':
            if self.state=="Off":
                return 'mdi:radiator-disabled'
            else:
                return "mdi:radiator"
        else:
            # HOT WATER
            if self.state=="Off":
                return 'mdi:water-off'
            else:
                return "mdi:water"

    @property
    def name(self):
        """Return the name of the Device """
        if self.circuitType=="HEATING":
            return "Wiser Heating"
        else:
            return "Wiser Hot Water"

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def device_state_attributes(self):
        """ returns additional info"""
        _LOGGER.debug('WiserSystemCircuitState - device_state_attributes - get_all_heating')
        attrs={}
        if self.circuitType=="HEATING":
           heatingChannels= self.handler.getWiserHubManager().get_all_heating_channels()
           for heatingChannel in heatingChannels:
               channelName=heatingChannel.name
               channelPctDmd=heatingChannel.percentage_demand
               channelRoomIds=heatingChannel.room_ids
               attrName="percentage_demand_{}".format(channelName)
               attrs[attrName]=channelPctDmd
               attrName2="room_ids_{}".format(channelName)
               attrs[attrName2]=channelRoomIds
        return attrs
           
    
    @property
    def state(self):
        _LOGGER.debug('**********************************')
        _LOGGER.debug('Wiser Cloud Circut STATE requested')
        _LOGGER.debug('**********************************')
        _LOGGER.debug('get_heating_relay_state')
        if self.circuitType=="HEATING":
            return self.handler.getWiserHubManager().get_heating_relay_state()
        else:
            return self.handler.getWiserHubManager().get_hotwater_relay_state()        
  

"""
Sensor to display the status of the Wiser Cloud
"""
class WiserSystemCloudSensor(Entity):
    def __init__(self,handler):
            
        """Initialize the sensor."""
        _LOGGER.info('Wiser Cloud Sensor Init - get_system')
        self.handler=handler
        self.cloudStatus=self.handler.getWiserHubManager().get_system().cloud_connection_status
      
    def update(self):
        _LOGGER.debug('Wiser Cloud Sensor Update requested - get_system')
        self.handler.update()
        self.cloudStatus=self.handler.getWiserHubManager().get_system().cloud_connection_status

    @property
    def icon(self):
        if self.cloudStatus =="Connected":
            return "mdi:cloud-check"
        else:
            return "mdi:cloud-alert"
    @property
    def name(self):
        """Return the name of the Device """
        return ("Wiser Cloud Status")

    @property
    def should_poll(self):
        """Return the polling state."""
        return True
    @property
    def state(self):
        _LOGGER.debug('**********************************')
        _LOGGER.debug('Wiser Cloud  status Update requested')
        _LOGGER.debug('**********************************')
        return self.cloudStatus
    
  
"""
Sensor to display the status of the Wiser Operation Mode (Away/Normal etc)
"""
class WiserSystemOperationModeSensor(Entity):
    def __init__(self,handler):
            
        """Initialize the sensor."""
        _LOGGER.info('Wiser Operation  Mode Sensor Init')
        self.handler=handler
        _LOGGER.debug('WiserSystemOperationModeSensor - init')
        self.overrideType=self.handler.getWiserHubManager().get_system().override_type
        self.awayTemperature=self.handler.getWiserHubManager().get_system().away_mode_set_point_limit
      
    def update(self):
        _LOGGER.debug('Wiser Operation Mode Sensor Update requested')
        self.handler.update()
        self.overrideType=self.handler.getWiserHubManager().get_system().override_type
        self.awayTemperature=self.handler.getWiserHubManager().get_system().away_mode_set_point_limit

    def mode(self):
        if self.overrideType and self.overrideType == "Away":
            return "Away"
        else:
            return "Normal"

    @property
    def icon(self):
        if self.mode() == "Normal":
            return "mdi:check"
        else:
            return "mdi:alert"

    @property
    def name(self):
        """Return the name of the Device """
        return ("Wiser Operation Mode")

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def state(self):
        return self.mode()

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        attrs = { "AwayModeTemperature": -1.0 }
        if self.awayTemperature:
            try:
                attrs["AwayModeTemperature"] = int(self.awayTemperature)/10.0
                _LOGGER.debug("Used value for awayTemperature", self.awayTemperature)
            except:
                _LOGGER.debug("Unexpected value for awayTemperature", self.awayTemperature)
        return attrs
