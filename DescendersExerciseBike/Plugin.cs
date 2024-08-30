using System;
using System.Net.Sockets;
using System.Threading;
using BepInEx;
using BepInEx.Logging;
using UnityEngine;

namespace DescendersExerciseBike;

[BepInPlugin(MyPluginInfo.PLUGIN_GUID, MyPluginInfo.PLUGIN_NAME, MyPluginInfo.PLUGIN_VERSION)]
public class Plugin : BaseUnityPlugin
{
    internal static new ManualLogSource Logger;
    internal static Socket client = null;
        
    private void Awake()
    {
        // Plugin startup logic
        Logger = base.Logger;
        Logger.LogInfo($"Plugin {MyPluginInfo.PLUGIN_GUID} is loaded!");

        client = new Socket(AddressFamily.InterNetwork, SocketType.Dgram, ProtocolType.Udp);
        client.Connect("127.0.0.1", 33356);
    }

    private void Update()
    {
        // Send incline angle
        if (GameObject.Find("Player_Human")){
            var angle = GameObject.Find("Player_Human").transform.eulerAngles.x;
            if (angle < 180f) {
                angle = -angle;
            } else {
                angle = 360f - angle;
            }

            client.Send(BitConverter.GetBytes(angle));
        } else {
            client.Send(BitConverter.GetBytes(0f));
        }

        var buffer = new byte[4];

        client.ReceiveTimeout = 1000;

        client.Receive(buffer, 4, SocketFlags.None);

        float velocity = BitConverter.ToSingle(buffer, 0);

        Vector3 forward = GameObject.Find("Player_Human").transform.forward;
        
        GameObject.Find("Player_Human").SendMessage("SetVelocity", forward * velocity);

        //Logger.LogInfo(velocity);
    }
}
