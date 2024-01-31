using System;
using System.Collections.Generic;
using UnityEngine;
using Newtonsoft.Json;
using System.Linq;
using System.Data;


public class Main : MonoBehaviour
{


    [SerializeField] private WSConnection _connection;
    [SerializeField] private Material _defaultMaterial;

    private List<Robot> _robots;
    private List<GameObject> _spawnedRobots = new List<GameObject>();
    private bool loaded = false; // TODO just temp

    void Update() {
        if (loaded) spawn_robots("panda_arm_hand");
    }


    // Start is called before the first frame update
    void Start()
    {
        _connection.subscribe("DATA", process_entity);
    }



    void process_entity(string data)
    {
        try {
            var robot = JsonConvert.DeserializeObject<List<Robot>>(data);
            _robots = robot;
            loaded = true;
            _connection.Send(MessageType.MSG, "Done");
        }  catch (Exception ex) { Debug.LogError(ex.Message); _connection.Send(MessageType.MSG, ex.Message); }
        
    }

    Mesh create_mesh(MeshData data) {
        
        var mesh =  new Mesh
        {
            vertices = data.Vertices.Select(v => new Vector3(v[0], v[1], v[2])).ToArray(),
            triangles = data.Indices.SkipWhile(indices => indices.Count != 3).SelectMany(innerList => innerList).ToArray()
        };

        mesh.RecalculateNormals();
        mesh.Optimize();  

        return mesh;
    }

    void create_visual(GameObject parent, Visual visual) {

        GameObject visuals = new GameObject(visual.Name);
        visuals.transform.SetParent(parent.transform);
    
        var spos = new Vector3(visual.Position[0], visual.Position[1],visual.Position[2]);
        var srot = Quaternion.Euler(visual.Rotation[0], visual.Rotation[1], visual.Rotation[2]); 
        visuals.transform.SetLocalPositionAndRotation(spos, srot);


        for (int i = 0; i < visual.Meshes.Count; i++) {
            
            GameObject obj = new GameObject($"node{i}");

            obj.AddComponent<MeshRenderer>().material = _defaultMaterial;
            obj.AddComponent<MeshFilter>().mesh = create_mesh(visual.Meshes[i]);

            obj.transform.SetParent(visuals.transform);
            obj.transform.localRotation = Quaternion.Euler(-90, 0, 0);
        }
      
    }
    
    GameObject create_link(GameObject parent, Link link, Robot robot) {
        
        GameObject linkObj = new GameObject(link.Name);
        linkObj.transform.SetParent(parent.transform);

        var pos =  new Vector3(link.Position[0], link.Position[1], link.Position[2]);
        var rot =  Quaternion.Euler(link.Rotation[0], link.Rotation[1], link.Rotation[2]);
        linkObj.transform.SetLocalPositionAndRotation(pos, rot);

        if (!string.IsNullOrEmpty(link.VisualName)) create_visual(linkObj, robot.Visuals[link.VisualName]); 

        var child = robot.Joints.Values.FirstOrDefault(joint => joint.ParentLink == link.Name);
        if (child == null) return linkObj;
        return create_joint(linkObj, child, robot);
    }

    GameObject create_joint(GameObject parent, Joint joint, Robot robot) {

        GameObject jointObj = new GameObject(joint.Name);
        jointObj.transform.SetParent(parent.transform);

        var pos =  new Vector3(joint.Position[0], joint.Position[1], joint.Position[2]);
        var rot =  Quaternion.Euler(joint.Rotation[0], joint.Rotation[1], joint.Rotation[2]);
        jointObj.transform.SetLocalPositionAndRotation(pos, rot);

        return create_link(jointObj, robot.Links[joint.ChildLink], robot);
    }

    void spawn_robots(string name) {

        loaded = false;
    
        foreach (var robot in _spawnedRobots) Destroy(robot);
        _spawnedRobots.Clear();


        foreach (Robot robot in _robots) {

            GameObject robotObj = new GameObject(robot.Name);
            create_link(robotObj, robot.Links[robot.StartLink], robot);
            _spawnedRobots.Add(robotObj);
        }
    }

    
}
