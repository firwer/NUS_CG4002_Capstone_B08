﻿using System;
using System.Xml.Serialization;
using UnityEngine;

namespace M2MqttUnity
{
    /// <summary>
    /// Serializable settings for MQTT broker configuration.
    /// </summary>
    [Serializable]
    [XmlType(TypeName = "broker-settings")]
    public class BrokerSettings
    {
        [Tooltip("Address of the host running the broker")]
        public string host = "35.247.174.182";

        [Tooltip("Port used to access the broker")]
        public int port = 1884;

        [Tooltip("Encrypted access to the broker")]
        public bool encrypted = false;

        [Tooltip("Optional alternate addresses, used if the previous host is not accessible")]
        public string[] alternateAddress;
    }
}

