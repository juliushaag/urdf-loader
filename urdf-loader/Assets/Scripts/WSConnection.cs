using System.Collections.Generic;
using UnityEngine;
using NativeWebSocket;
using System.Net;
using System.Net.NetworkInformation;
using System.Threading.Tasks;
using System.Collections;
using System.Net.Sockets;

// Every send message has a header to specify its type 
public enum MessageType
{
    CMD,
    MSG,
    DAT
}

public class WSConnection : MonoBehaviour
{
    private enum ClientState
    {
        Searching = 0,
        Connected = 1,
        Disconnected = 2,
        Reconnecting = 3,
        Closing = 4,
        Closed = 5,
    }


    public delegate void Subscriber(string message);

    public int port;

    private Dictionary<string, Subscriber> subscribers = new Dictionary<string, Subscriber>();


    private WebSocket _webSocket = null;
    private string _connectedIP = null;
    private ClientState _clientState = ClientState.Disconnected;

    private string _buffer = "";


    // Start is called before the first frame update

    public void subscribe(string header, Subscriber callback) => subscribers.Add(header, callback);

    public void unsubscribe(string header) => subscribers.Remove(header);


    // Action for object messages and text messages

    static string HEADER_SEPERATOR = ":::";

    public void Send(MessageType type, string text)
    {

        string header = type switch
        {
            MessageType.CMD => "CMD",
            MessageType.DAT => "DAT",
            MessageType.MSG => "MSG",
            _ => "INV"
        };

        _webSocket.SendText(header + HEADER_SEPERATOR  + text);
    }


    async void OnApplicationQuit()
    {
        if (_webSocket != null) await _webSocket.Close();
    }

    public void Update()
    {
        if (_clientState == ClientState.Connected)
        {
            _webSocket.DispatchMessageQueue();
            return;
        }

        if (_clientState != ClientState.Disconnected) return;


        if (_connectedIP != null)
        {
            _clientState = ClientState.Reconnecting;
            StartCoroutine(Reconnect());
            return;
        }

        _clientState = ClientState.Searching;
        StartCoroutine(SearchForWebSocket());
    }


    private IEnumerator Reconnect()
    {

        yield return StartCoroutine(TestWebSockets(_connectedIP));

        if (_clientState == ClientState.Reconnecting) _clientState = ClientState.Disconnected;
    }

    private IEnumerator SearchForWebSocket()
    {
        Debug.Log($"Searching for server");

        List<Coroutine> coroutineList = new List<Coroutine>();
        foreach (string ipAddress in GetTestIPList())
        {
            if (_clientState == ClientState.Connected) break;
            
            coroutineList.Add(StartCoroutine(TestWebSockets(ipAddress)));
        }
        foreach (Coroutine coroutine in coroutineList)
        {
            yield return coroutine;
        }

        if (_connectedIP == null) _clientState = ClientState.Disconnected;
    }


    private IEnumerator TestWebSockets(string ipAddress)
    {
        WebSocket testWebSocket = new WebSocket($"ws://{ipAddress}:{port}");

        Task connectTask = testWebSocket.Connect();
        yield return new WaitUntil(() =>
        {
            return testWebSocket.State == WebSocketState.Open ||
                    testWebSocket.State == WebSocketState.Closed;
        });

        if (testWebSocket.State == WebSocketState.Open && _webSocket == null)
        {
            Debug.Log($"Found a WebSocket server in {ipAddress}");
            _connectedIP = ipAddress;
            _webSocket = testWebSocket;
            _clientState = ClientState.Connected;

            _webSocket.OnClose      += OnWSClose;
            _webSocket.OnError      += OnWSError;
            _webSocket.OnMessage    += OnWSMessage;


            Task.Run(async () =>
            {
                await connectTask;
                Debug.Log($"Quit WebSocket run thread");
                _clientState = ClientState.Disconnected;
                _webSocket = null;
            });
        }

    }

    private void OnWSClose(WebSocketCloseCode ws_event) {
        Debug.Log($"Connection with {_connectedIP} is closed!");
        _clientState = ClientState.Reconnecting;
    }

    private void OnWSError(string error) {
        _clientState = ClientState.Reconnecting;
    }

    private void OnWSMessage(byte[] bytes) {
        
        string msg = System.Text.Encoding.UTF8.GetString(bytes);

        _buffer += msg;
        
        if (!msg.EndsWith("</>")) return;

        _buffer = _buffer.Substring(0, _buffer.Length - "</>".Length);
        string []split = _buffer.Split(HEADER_SEPERATOR);
        _buffer = "";

        if (split.Length != 2) {
            Debug.LogWarning($"Invalid message formatting {msg}, this message will be ignored");
            return;
        }



        string header = split[0];
        string content = split[1];

        if (!subscribers.ContainsKey(header)) Debug.LogWarning($"Invalid message header received {header}"); // error
        else Task.Run(() => subscribers[header].Invoke(content)); // call callback 
    }

   
    private static List<string> GetTestIPList()
    {
        List<string> ipSearchList = new List<string>();

        foreach (NetworkInterface adapter in NetworkInterface.GetAllNetworkInterfaces())
        {
            NetworkInterfaceType type = adapter.NetworkInterfaceType;

            //easier to read when split
            if (type != NetworkInterfaceType.Wireless80211 && type != NetworkInterfaceType.Ethernet) continue;
            if (adapter.OperationalStatus != OperationalStatus.Up || !adapter.Supports(NetworkInterfaceComponent.IPv4)) continue;

            foreach (UnicastIPAddressInformation address in adapter.GetIPProperties().UnicastAddresses)
            {
                if (address.Address.AddressFamily == AddressFamily.InterNetwork) GetSubnetIPs(address.Address, ipSearchList);
            }
        }


        ipSearchList.Add("127.0.0.1");
        return ipSearchList;
    }


    private static void GetSubnetIPs(IPAddress ipAddress, List<string> ip_addresses)
    {

        byte[] networkAddressBytes = ipAddress.GetAddressBytes();
        int byte_length = networkAddressBytes.Length - 1;

        for (byte i = 1; i < 255; i++)
        {
            networkAddressBytes[byte_length] = i;
            ip_addresses.Add(new IPAddress(networkAddressBytes).ToString());
        }
    }
}
