using System;
using System.Collections.Generic;
using UnityEngine;
using Newtonsoft.Json;
using System.Linq;
using System.Data;
using System.IO;
using System.IO.Compression;

public class Main : MonoBehaviour
{


    [SerializeField] private WSConnection _connection;
    [SerializeField] private Material _defaultMaterial;

    private List<Entity> _entities;
    private List<GameObject> _spawnedEntities = new List<GameObject>();
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
            _entities = JsonConvert.DeserializeObject<List<Entity>>(data);
            _connection.Send(MessageType.MSG, "Model loaded sucessfully");
            loaded = true;
        }  catch (Exception ex) { Error(ex.Message); }
        
    }

    Mesh create_mesh(MeshData data) {
        

        
        var mesh =  new Mesh
        {
            vertices = data.Vertices.Select(v => new Vector3(v[0], v[1], v[2])).ToArray(),
            normals = data.Normals.Select(v => new Vector3(v[0], v[1], v[2])).ToArray(),
            triangles = data.Indices
        };

        mesh.Optimize();  

        return mesh;
    }


    void create_visual(GameObject parent, Visual visual) {

        GameObject visuals = new GameObject("Visuals");
        visuals.transform.SetParent(parent.transform);
        

        for (int i = 0; i < visual.Meshes.Count; i++) {
            MeshData mesh = visual.Meshes[i];

            GameObject obj = new GameObject(mesh.Name);


            var renderer = obj.AddComponent<MeshRenderer>();
            obj.AddComponent<MeshFilter>().mesh = create_mesh(mesh); 

            if (mesh.Material != null) {
                Material mat = new Material(Shader.Find("Standard"));

                mat.SetColor("_Color",new Color(mesh.Material.Diffuse[0] / 255, mesh.Material.Diffuse[1] / 255, mesh.Material.Diffuse[2] / 255, mesh.Material.Diffuse[3] / 255));
                mat.SetColor("_SpecColor", new Color(mesh.Material.Specular[0] / 255, mesh.Material.Specular[1] / 255, mesh.Material.Specular[2] / 255, mesh.Material.Specular[3] / 255));
                mat.SetColor("_EmissionColor", new Color(mesh.Material.Ambient[0] / 255, mesh.Material.Ambient[1] / 255, mesh.Material.Ambient[2] / 255, mesh.Material.Ambient[3] / 255));
                
                renderer.material = mat;
            }
         
            obj.transform.localScale = new Vector3(mesh.Scale[0], mesh.Scale[1], mesh.Scale[2]);
            obj.transform.localPosition = new Vector3(mesh.Position[0], mesh.Position[1], mesh.Position[2]);
            obj.transform.localEulerAngles = new Vector3(mesh.Rotation[0], mesh.Rotation[1], mesh.Rotation[2])  * Mathf.Rad2Deg;

            obj.transform.SetParent(visuals.transform);
        }

        
        visuals.transform.localPosition = new Vector3(visual.Position[0], visual.Position[1],visual.Position[2]);
        visuals.transform.localEulerAngles = new Vector3(visual.Rotation[0], visual.Rotation[1], visual.Rotation[2]) * Mathf.Rad2Deg;      
    }
    GameObject create_link(GameObject parent, Link link, Entity entity) {

        GameObject jointObj = new GameObject(link.Name);
        jointObj.transform.SetParent(parent.transform);

        if (!string.IsNullOrEmpty(link.VisualName)) {
            create_visual(jointObj, entity.Visuals[link.VisualName]); 
        }

        var joints = entity.Joints.Values.Where(joint => joint.ParentLink == link.Name);

        foreach (var jnt in joints) {
            create_joint(jointObj, jnt, entity);   
        }

        return jointObj;
    }

    
    GameObject create_joint(GameObject parent, Joint joint, Entity entity) {

        var linkObj = create_link(parent, entity.Links[joint.ChildLink], entity);
    
        linkObj.transform.localPosition = new Vector3(joint.Position[0], joint.Position[1], joint.Position[2]);
        linkObj.transform.localEulerAngles = new Vector3(joint.Rotation[0], joint.Rotation[1], joint.Rotation[2]) * Mathf.Rad2Deg;


        var controller = linkObj.AddComponent<JointController>(); // setup controller script
        controller.jointName = joint.Name;
        controller.maxRot = joint.MaxRot * Mathf.Rad2Deg;
        controller.minRot = joint.MinRot * Mathf.Rad2Deg;
        controller.axis = new Vector3(joint.Axis[0], joint.Axis[1], joint.Axis[2]);
        controller.type = joint.Type;

        return linkObj;
    }

    void spawn_robots(string name) {

      loaded = false;
  
      foreach (var robot in _spawnedEntities) Destroy(robot);
      _spawnedEntities.Clear();

      try {
        foreach (Entity robot in _entities) {

            GameObject robotObj = new GameObject(robot.Name);
            create_link(robotObj, robot.Links[robot.StartLink], robot);
            _spawnedEntities.Add(robotObj);
        }
      } catch (Exception ex) { Error(ex.Message); }
        
    }

    private void Error(string message) {
        if (_connection != null) _connection.Send(MessageType.ERR, message);
        Debug.LogError(message);
    }
    
}
