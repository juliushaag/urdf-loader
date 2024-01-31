using System;
using System.Collections.Generic;

[Serializable]
public class MeshData
{
    public string Name { get; set; }
    public List<float> Position { get; set; }
    public List<float> Rotation { get; set; }
    public List<float> Scale { get; set; }
    public List<List<int>> Indices { get; set; }
    public List<List<float>> Vertices { get; set; }
    public List<List<float>> Normals { get; set; }
    public List<float> Color { get; set; }
    public string Material {get; set; } 
}

[Serializable]
public class MatData
{
    public string Name { get; set; }
    public string Id { get; set; }
    public List<float> Emission { get; set; }
    public List<float> Ambient { get; set; }
    public List<float> Diffuse { get; set; }
    public List<float> Specular { get; set; }
    public float Shininess { get; set; }
    public List<float> Reflective { get; set; }
    public float Reflectivity { get; set; }
    public List<float> Transparent { get; set; }
    public float Transparency { get; set; }
}

[Serializable]
public class Visual
{
    public string Name { get; set; }
    public string Type { get; set; }
    
    public List<float> Position { get; set; }

    public List<float> Rotation { get; set; }

    public List<float> Scale { get; set; }

    public List<MeshData> Meshes { get; set; }

    
    public Dictionary<string, MatData> Materials { get; set; }
}


[Serializable]
public class Joint
{

    public string Name { get; set; }
    public List<float> Position { get; set; }
    public List<float> Rotation { get; set; }
    public string ParentLink { get; set; }
    public string ChildLink { get; set; }
    public string Type { get; set; }
    public List<float> Axis { get; set; }
}

[Serializable]
public class Link
{
    public string Name { get; set; }
    public string VisualName { get; set; }
    public List<float> Position { get; set; }
    public List<float> Rotation { get; set; }
}

[Serializable]
public class Robot
{
    public string Name { get; set; }
    public bool Manipulable { get; set; }

    public string StartLink { get; set; }
    public Dictionary<string, Joint> Joints { get; set; }

    public Dictionary<string, Link> Links { get; set; }

    public Dictionary<string, Visual> Visuals { get; set; } 
}