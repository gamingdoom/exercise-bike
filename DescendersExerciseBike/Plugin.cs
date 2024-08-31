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
    private const int PORT = 33356;
    private const float BIKE_HEIGHT = 0.6f;
    private const float HEIGHT_TOLERANCE = 0.08f;
    private const float GRAVITY = -12.9f;
 
    internal static new ManualLogSource Logger;
    internal static Socket client = null;

    internal static float gravityVelocity = 0.0f;
        
    private void Awake()
    {
        // Plugin startup logic
        Logger = base.Logger;
        Logger.LogInfo($"Plugin {MyPluginInfo.PLUGIN_GUID} is loaded!");

        client = new Socket(AddressFamily.InterNetwork, SocketType.Dgram, ProtocolType.Udp);
        client.Connect("127.0.0.1", PORT);
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

        client.ReceiveTimeout = 10;

        client.Receive(buffer, 4, SocketFlags.None);

        float recieved_velocity = BitConverter.ToSingle(buffer, 0);

        var player = GameObject.Find("Player_Human");

        Vector3 velocity = player.transform.forward * recieved_velocity;
        
        // Add Gravity
        if (Physics.Raycast(player.transform.position, -player.transform.up, out var hit)){
            Logger.LogInfo(hit.distance);
            if (hit.distance < BIKE_HEIGHT + HEIGHT_TOLERANCE){
                gravityVelocity = 0.0f;
                Logger.LogInfo("Grounded");
            } else {
                gravityVelocity += GRAVITY * Time.deltaTime;
                Logger.LogInfo("Not Grounded");
                Logger.LogInfo(gravityVelocity);
            }
        }

        player.SendMessage("SetVelocity", velocity + Vector3.up * gravityVelocity);
    }

    private void OnDestroy()
    {
        client.Close();
    }
}
