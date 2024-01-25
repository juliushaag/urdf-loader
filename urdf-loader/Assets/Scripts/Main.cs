using System;
using System.Collections.Generic;
using UnityEngine;
using Newtonsoft.Json;
using Unity.VisualScripting;
using System.Linq;
using System.Threading;

public class Main : MonoBehaviour
{

    [Serializable]
    private class Shape
    {
        public string Name { get; set; }
        public string Type { get; set; }
        
        public List<float> Position { get; set; }

        public List<float> Rotation { get; set; }

        public List<MeshData> Meshes { get; set; }

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

    [Serializable]
    private class Data {
        public List<Robot> Robots { get; set; }

        public Dictionary<string, Shape> Shapes { get; set; }
    }

    [SerializeField] private WSConnection connection;

    [SerializeField] private Material robot_material;

    private List<Data> _robots = new List<Data>();
    private bool loaded = false; // TODO just temp

    void Update() {
        if (loaded) spawn_robots("panda_arm_hand");
    }


    // Start is called before the first frame update
    void Start()
    {
        connection.subscribe("DATA", process_entity);
    }



    void process_entity(string data)
    {
        try {
            var robot = JsonConvert.DeserializeObject<Data>(data);
            _robots.Add(robot);
            loaded = true;
            connection.Send(MessageType.MSG, "Done");
        }  catch (Exception ex) { Debug.LogError(ex.Message); }
        
    }

    Mesh create_mesh(MeshData data) {
        var mesh = new Mesh();
        
        Debug.Log(data.ShapeName);
        mesh.vertices = data.Vertices.Select(v => new Vector3(v[0], v[1], v[2])).ToArray();
        mesh.triangles = data.Indices.SelectMany(innerList => innerList).ToArray();

        Color[] colors = new Color[mesh.vertices.Length];
        for (int i = 0; i < colors.Length; i++) colors[i] = new Color(data.Color[0], data.Color[1], data.Color[2], data.Color[3]);

        return mesh;
    }

    GameObject create_joint(GameObject parent, Joint joint, Dictionary<string, Shape> shapes) {


        
        GameObject jointObj = new GameObject(joint.Name);
        jointObj.transform.SetParent(parent.transform);

        var pos =  new Vector3(joint.JointPos[0], joint.JointPos[1], joint.JointPos[2]);
        var rot =  new Quaternion(joint.JointRot[0], joint.JointRot[1], joint.JointRot[2], joint.JointRot[3]);
        rot.eulerAngles = new Vector3(rot.eulerAngles.x, rot.eulerAngles.y, rot.eulerAngles.z);
        jointObj.transform.SetLocalPositionAndRotation(pos, rot);

        if (joint.MeshID == null) return jointObj;


        GameObject visuals = new GameObject("visuals");
        visuals.transform.SetParent(jointObj.transform);
        
        Shape shape = shapes[joint.MeshID];
        var spos = new Vector3(shape.Position[0], shape.Position[1],shape.Position[2]);
        var srot = new Quaternion(shape.Rotation[0], shape.Rotation[1], shape.Rotation[2], shape.Rotation[3]); 
        visuals.transform.SetLocalPositionAndRotation(spos, srot);


        int index = 0;
        foreach (var mesh in shape.Meshes) {
            GameObject obj = new GameObject($"node{index}");
            obj.AddComponent<MeshRenderer>().material = robot_material;
            var meshComp = create_mesh(mesh);
            meshComp.RecalculateNormals();
            obj.AddComponent<MeshFilter>().mesh = meshComp;
            obj.transform.SetParent(visuals.transform, false);
            obj.transform.rotation = Quaternion.Euler(-90, 0, 0);
            index++;
        }

        return jointObj;
    }

    void spawn_robots(string name) {

        loaded = false;
        
        Data data = _robots[_robots.Count - 1];

        


        foreach (Robot robot in data.Robots) {
            
            GameObject jointObj = new GameObject(robot.Name);
            List<GameObject> realizedJoints = new List<GameObject>{ create_joint(jointObj, robot.Joints[0], data.Shapes) };

            for (int i = 1; i < robot.Joints.Count; i++) {
                realizedJoints.Add(create_joint(realizedJoints[robot.Joints[i].ParentIndex], robot.Joints[i], data.Shapes));
            }
        }
    }

    
}
