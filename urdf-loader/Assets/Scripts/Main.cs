using System;
using System.Collections.Generic;
using UnityEngine;
using Newtonsoft.Json;
using Unity.VisualScripting;
using System.Linq;

public class Main : MonoBehaviour
{

    [Serializable]
    private class Shape
    {
        public string Name { get; set; }
        public string Type { get; set; }
        
        public List<float> Position { get; set; }

        public List<float> Orientation { get; set; }

    }


    [Serializable]
    private class Joint
    {

        public string Name { get; set; }
        public int ParentIndex { get; set; }
        public string JointType { get; set; }
        public List<float> JointAxis { get; set; }
        public List<float> JointPos { get; set; }
        public List<float> JointRot { get; set; }
        public string MeshID { get; set; }
    }

    [Serializable]
    private class Robot
    {
        public string Name { get; set; }
        public bool Manipulable { get; set; }
        public int RootJointIndex { get; set; }
        public List<Joint> Joints { get; set; }
    }


    [Serializable]
    private class MeshData
    {
        public string ShapeName { get; set; }
        public List<List<float>> Vertices { get; set; }
        public List<List<int>> Indices { get; set; }
        public List<List<float>> Normals { get; set; }
        public List<float> Color { get; set; }
    }

    [SerializeField] private WSConnection connection;

    private Dictionary<string, Shape> _shapes = new Dictionary<string, Shape>();

    private Dictionary<string, List<MeshData>> _mesh = new Dictionary<string, List<MeshData>>();

    private Dictionary<string, Robot> _robots = new Dictionary<string, Robot>();

    private bool loaded = false; // TODO just temp

    void Update() {
        if (loaded) spawn_robots("panda_arm_hand");
    }


    // Start is called before the first frame update
    void Start()
    {
        connection.subscribe("ENTITY", process_entity);
        connection.subscribe("MESH", process_mesh);
        connection.subscribe("SHAPE", process_shape);
        connection.subscribe("BEACON", process_message);
    }

    void process_shape(string data)
    {
        try {
            Shape shape = JsonConvert.DeserializeObject<Shape>(data);
            _shapes.Add(shape.Name, shape);
        }  catch (JsonException ex)
        {
            Debug.Log("JSON Exception: " + ex.Message);
        }
    }

    void process_message(string data)
    {
        connection.Send(MessageType.MSG, data);
    }

    void process_mesh(string data)
    {
        try {
            var mesh = JsonConvert.DeserializeObject<MeshData>(data);

            if (!_mesh.ContainsKey(mesh.ShapeName)) _mesh.Add(mesh.ShapeName, new List<MeshData>());
            _mesh[mesh.ShapeName].Add(mesh);
        }  catch (JsonException ex)
        {
            Debug.Log("JSON Exception: " + ex.Message);
        }
    }

    void process_entity(string data)
    {

        Debug.Log(data);

        try {
            var robot = JsonConvert.DeserializeObject<Robot>(data);
            _robots.Add(robot.Name, robot);

            Debug.Log(_robots.Count);
            foreach (var kvp in _robots)
            {
                Debug.LogFormat("Key = {0}, Value = {1}", kvp.Key, kvp.Value);
            }

            loaded = true;
        }  catch (Exception ex)
        {
            Debug.Log("JSON Exception: " + ex.Message);
        }
    }

    Mesh create_mesh(MeshData data) {
        var mesh = new Mesh();
        
        mesh.vertices = data.Vertices.Select(v => new Vector3(v[0], v[1], v[2])).ToArray();
        // mesh.normals = data.Normals.Select(v => new Vector3(v[0], v[1], v[2])).ToArray();
        
        mesh.triangles = data.Indices.SelectMany(innerList => innerList).ToArray();

        Color[] colors = new Color[mesh.vertices.Length];
        for (int i = 0; i < colors.Length; i++) colors[i] = new Color(data.Color[0], data.Color[1], data.Color[2]);

        return mesh;
    }

    GameObject create_joint(GameObject parent, Joint joint) {


        
        GameObject jointObj = new GameObject(joint.Name);
        if (parent != null) jointObj.transform.parent = parent.transform;

        jointObj.transform.SetPositionAndRotation(
            new Vector3(joint.JointPos[0], joint.JointPos[1], joint.JointPos[2]), 
            new Quaternion(joint.JointRot[0], joint.JointRot[1], joint.JointRot[2], joint.JointRot[3])
        );

        if (joint.MeshID == null) return jointObj;

        // Shape shape = _shapes[joint.MeshID];

        GameObject visuals = new GameObject("visuals");
        visuals.transform.parent = jointObj.transform;
        
        // visuals.transform.SetPositionAndRotation(
        //     new Vector3(shape.Position[0], shape.Position[1],shape.Position[2]), 
        //     new Quaternion(shape.Orientation[0], shape.Orientation[1], shape.Orientation[2], shape.Orientation[3])
        // );




        List<MeshData> data = _mesh[joint.MeshID];

        int index = 0;
        foreach (var mesh in data) {
            GameObject obj = new GameObject($"visual{index}{mesh.ShapeName}");
            obj.AddComponent<MeshRenderer>();
            obj.AddComponent<MeshFilter>().mesh = create_mesh(mesh);
            

            obj.transform.parent = visuals.transform;
            
        }

        return jointObj;
    }

    void spawn_robots(string name) {

        loaded = false;
        
        Robot robot = _robots[name];


        var root = create_joint(null, robot.Joints[0]);
        List<GameObject> realizedJoints = new List<GameObject>{ root };

        for (int i = 1; i < robot.Joints.Count; i++) {
            Debug.Log(i);
            realizedJoints.Add(create_joint(realizedJoints[robot.Joints[i].ParentIndex], robot.Joints[i]));
        }
    }

    
}
