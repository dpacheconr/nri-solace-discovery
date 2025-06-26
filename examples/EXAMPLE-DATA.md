# Example Data Files

This folder contains JSON files showing the structure of data returned by the Solace integration commands. These files have been sanitized to remove environment-specific details and reduced in size for better readability.

## Sample Data

For each API endpoint, the integration collects various metrics depending on the resource type:

### VPN Metrics
```json
{
  "timestamp": "2025-06-25T11:15:31",
  "data": [
    {
      "msgVpnName": "vpn1",
      "enabled": true,
      "state": "up",
      "averageRxMsgRate": 12.5,
      "averageTxMsgRate": 8.3,
      "maxConnectionCount": 1000,
      "msgSpoolUsage": 230,
      "maxMsgSpoolUsage": 5000
    },
    {
      "msgVpnName": "vpn2",
      "enabled": true,
      "state": "up",
      "averageRxMsgRate": 5.2,
      "averageTxMsgRate": 3.1,
      "maxConnectionCount": 500,
      "msgSpoolUsage": 120,
      "maxMsgSpoolUsage": 2500
    }
  ]
}
```

### Queue Metrics
```json
{
  "timestamp": "2025-06-25T11:16:15",
  "vpnName": "vpn1",
  "data": [
    {
      "queueName": "queue1",
      "msgVpnName": "vpn1",
      "accessType": "exclusive",
      "durable": true,
      "averageRxMsgRate": 4.2,
      "averageTxMsgRate": 3.8,
      "msgSpoolUsage": 120,
      "maxMsgSpoolUsage": 5000,
      "bindSuccessCount": 5
    },
    {
      "queueName": "queue2", 
      "msgVpnName": "vpn1",
      "accessType": "non-exclusive",
      "durable": true,
      "averageRxMsgRate": 1.5,
      "averageTxMsgRate": 1.3,
      "msgSpoolUsage": 50,
      "maxMsgSpoolUsage": 5000,
      "bindSuccessCount": 3
    }
  ]
}
```

### Topic Endpoint Metrics
```json
{
  "timestamp": "2025-06-25T11:16:42",
  "vpnName": "vpn1",
  "data": [
    {
      "topicEndpointName": "topic1",
      "msgVpnName": "vpn1",
      "accessType": "exclusive",
      "durable": true,
      "averageRxMsgRate": 2.8,
      "averageTxMsgRate": 2.5,
      "msgSpoolUsage": 75,
      "maxMsgSpoolUsage": 5000
    }
  ]
}
```

### Bridge Metrics
```json
{
  "timestamp": "2025-06-25T11:18:00",
  "vpnName": "vpn1",
  "data": [
    {
      "bridgeName": "bridge1",
      "msgVpnName": "vpn1",
      "enabled": true,
      "state": "up",
      "averageRxMsgRate": 1.2,
      "averageTxMsgRate": 1.0
    }
  ]
}
```

### Client Connection Metrics
```json
{
  "timestamp": "2025-06-25T11:18:19",
  "vpnName": "vpn1",
  "data": [
    {
      "clientName": "client1",
      "msgVpnName": "vpn1",
      "clientUsername": "app_user",
      "averageRxMsgRate": 3.5,
      "averageTxMsgRate": 2.8,
      "platform": "Linux-x86_64",
      "uptime": 3600
    }
  ]
}
```
