# Nuki
# Info
Plugin for integrating [Nuki Smartlock](https://nuki.io/de/smart-lock/) into smarthome.py facilitating triggering lock actions and getting status information from it.
# Requirements
You need a [Nuki Bridge](https://nuki.io/de/bridge/) which is already paired with your Nuki Smartlock(s).
# Configuration
## plugin.conf
```
[nuki]
    class_name = Nuki
    class_path = plugins.nuki
    bridge_ip = 192.168.1.10
    bridge_port = 8080
    bridge_api_token = q1W2e3
    #bridge_callback_ip = 192.168.0.2
    #bridge_callback_port = 8090
```

### Attributes
* 
`bridge_ip` : IP address of the Nuki Bridge*
* `bridge_port` : Port number of the Nuki Bridge*
* `bridge_api_token` : Token for authentification of the API connection*
* `bridge_callback_ip`: IP address of the TCP dispatcher which is handling the Bridge callback requests. By default, the local IP address is used
* `bridge_callback_port` : Port number of the TCP dispatcher. By default, port number 8090 is used.

*This information can be set via the Nuki App

## item.conf

### nukiId
This attribute connects the related item with the correspondig Nuki Smart Lock. The status of Smart Lock is sent to this item  	respectively can be set via this item. Its type is `string`.

#### Possible lock states:
* uncalibrated
* locked
* unlocking
* unlocked
* locking
* unlatched
* unlatched (lock 'n' go)
* unlachting
* motor blocked
* undefined

#### Possible lock actions:
* unlock
* lock
* unlatch
* lock 'n' go
* lock 'n' go with unlatch

The `nukiId` can be figured out via the REST API of the Nuki Bridge (see API documentation) or by just (re)starting the smarthome.py server with the configured Nuki plugin. The `name` and the `nukiId` of all paired Nuki Locks will be written to the log file of smarthome.py.

### nukiBatteryState
With this attribute you can check wheter the batteries of the corresponding Nuki Smart Lock has to be replaced or not. You have to assign the `nukiId` of the Smart Lock which battery you want to monitor. The return value type is `boolean`. 
* `false` : Batteries are good. No need to replace it.
* `true` : Batteries are low. Please replace as soon as possible.

### Example:
```
[Nuki_Smart_Lock]
  type = str
  nukiId = 50528385
  [[Battery_Alarm]]
    type = bool
    nukiBatteryState = 50528385
```
