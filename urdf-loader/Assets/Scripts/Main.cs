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
            _robots = JsonConvert.DeserializeObject<List<Robot>>(data);
            _connection.Send(MessageType.MSG, "Model loaded sucessfully");
            loaded = true;
        }  catch (Exception ex) { Error(ex.Message); }
        
    }



    Mesh create_mesh(MeshData data) {
        
        var mesh =  new Mesh
        {
            vertices = data.Vertices.Select(v => new Vector3(v[0], v[1], v[2])).ToArray(),
            normals = data.Normals.Select(v => new Vector3(v[0], v[1], v[2])).ToArray(),
            triangles = data.Indices.ToArray()
        };

        mesh.Optimize();  

        return mesh;
    }


    void create_visual(GameObject parent, Visual visual) {

        GameObject visuals = new GameObject("Visuals");
        visuals.transform.SetParent(parent.transform);
        
        visuals.transform.localPosition = new Vector3(visual.Position[0], visual.Position[1],visual.Position[2]);
        visuals.transform.localEulerAngles = new Vector3(visual.Rotation[0], visual.Rotation[1], visual.Rotation[2]) * 180f / Mathf.PI;
    

        for (int i = 0; i < visual.Meshes.Count; i++) {
            MeshData mesh = visual.Meshes[i];

            GameObject obj = new GameObject(mesh.Name);

            obj.AddComponent<MeshRenderer>().material = _defaultMaterial;
            obj.AddComponent<MeshFilter>().mesh = create_mesh(mesh); 
         
            obj.transform.localScale = new Vector3(mesh.Scale[0], mesh.Scale[1], mesh.Scale[2]);
            obj.transform.localPosition = new Vector3(mesh.Position[0], mesh.Position[1], mesh.Position[2]);
            obj.transform.localEulerAngles = new Vector3(mesh.Rotation[0], mesh.Rotation[1], mesh.Rotation[2])  * 180f / Mathf.PI; 

            obj.transform.SetParent(visuals.transform);
        }
      
    }
    GameObject create_link(GameObject parent, Link link, Robot robot) {

        GameObject jointObj = new GameObject(link.Name);
        jointObj.transform.SetParent(parent.transform);

        if (!string.IsNullOrEmpty(link.VisualName)) create_visual(jointObj, robot.Visuals[link.VisualName]); 
        // Collision could be created here

        var joints = robot.Joints.Values.Where(joint => joint.ParentLink == link.Name);



        foreach (var jnt in joints) create_joint(jointObj, jnt, robot);   
        
        return jointObj;
    }

    
    GameObject create_joint(GameObject parent, Joint joint, Robot robot) {

        var linkObj = create_link(parent, robot.Links[joint.ChildLink], robot);
    
        linkObj.transform.localPosition = new Vector3(joint.Position[0], joint.Position[1], joint.Position[2]);
        linkObj.transform.localEulerAngles = new Vector3(joint.Rotation[0], joint.Rotation[1], joint.Rotation[2]) * 180f / Mathf.PI;
    
        return linkObj;
    }

    void spawn_robots(string name) {

        loaded = false;
    
        foreach (var robot in _spawnedRobots) Destroy(robot);
        _spawnedRobots.Clear();

        try {
            foreach (Robot robot in _robots) {

                GameObject robotObj = new GameObject(robot.Name);
                create_link(robotObj, robot.Links[robot.StartLink], robot);
                _spawnedRobots.Add(robotObj);
            }
        } catch (Exception ex) { Error(ex.Message); }
        
    }

    private void Error(string message) {
        if (_connection != null) _connection.Send(MessageType.ERR, message);
        Debug.LogError(message);
    }
    
}
