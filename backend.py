import json
import math
import os
import time
import numpy as np
from udata import UData, UEntity, UHeaderType, UMaterial, UMesh, UJoint, ULink, UVisual
from scipy.spatial.transform import Rotation as R
from print_color import print as cprint
from parsers.urdf_parser import URDFJoint, URDFLink, URDFVisual, URDFData 
import trimesh
import trimesh.visual.material as TriMat
import websockets
import asyncio


FILE_PATH = "res/models/pybullet/robots/panda_arm_hand_without_cam.urdf"
FOLDER = os.path.dirname(FILE_PATH)


def mj2unity_pos(pos): return [-pos[1], pos[2], pos[0]]
def mj2unity_euler(rot): return [rot[1], -rot[2], -rot[0]]

def decompose_transform_matrix(matrix):
    u, sigma, vt = np.linalg.svd(matrix[:3, :3])
    rot = R.from_matrix(np.dot(u, np.dot(np.diag(sigma), vt))).as_euler("zyx")
    return rot.tolist(), matrix[:3, 3].tolist()

_meshes = {}


def convert_material(material : TriMat.PBRMaterial) -> UMaterial:
  material : TriMat.SimpleMaterial = material.to_simple() 

  return UMaterial(
    name=material.name,
    specular=material.specular.tolist(),
    ambient=material.ambient.tolist(),
    diffuse=material.diffuse.tolist(),
    glossiness=material.glossiness,
  )

def convert_mesh(mesh : trimesh.base.Trimesh, matrix : np.ndarray, name : str) -> UMesh:


  verts = np.around(mesh.vertices, decimals=5) # load vertices with max 5 decimal points
  verts[:, 0] *= -1 # reverse x pos of every vertex
  verts = verts.tolist()

  norms = np.around(mesh.vertex_normals, decimals=5) # load normals with max 5 decimal points
  norms[:, 0] *= -1 # reverse x pos of every normal
  norms = norms.tolist()

  indices = mesh.faces[:, [2, 1, 0]].flatten().tolist() # reverse winding order 

  rot, pos = decompose_transform_matrix(matrix) # decompose matrix 

  # this needs to be tested
  pos = [-pos[1], pos[2], -pos[0]]
  rot = [-rot[1] - math.pi / 2, -rot[2], math.pi / 2 - rot[0] ]
  scale = [1, 1, 1]

  return UMesh(
    name=name, 
    position=pos, 
    rotation=rot, 
    scale=scale, 
    indices=indices, 
    vertices=verts, 
    normals=norms, 
    material=convert_material(mesh.visual.material)
  )


def convert_visual(visual : URDFVisual) -> UVisual:

  file = visual.geometry.fileName.replace("package:/", FOLDER) # file specified in the urdf, origin different fot every urdf file 
  if FOLDER not in file: file = FOLDER + file # sometimes there is no "package:/" in the name 

  if file not in _meshes: # so we dont load one mesh twice (gripper fingers)
    scene = trimesh.load(file, force='scene')
    meshes = [convert_mesh(scene.geometry[item['geometry']], item['matrix'], item['geometry']) for item in scene.graph.transforms.edge_data.values()] # TODO: refine this
    _meshes[file] = meshes

  meshes = _meshes[file]

  hasOrigin = visual.origin is not None
  return UVisual(
    name=visual.name,
    type = visual.geometry.type,
    position=visual.origin.position if hasOrigin else [0.0, 0.0, 0.0],
    rotation= [visual.origin.rotation[0], visual.origin.rotation[2], visual.origin.rotation[1]] if hasOrigin else [0.0, 0.0, 0.0], # TODO: WTF ??
    scale = visual.geometry.scale,
    meshes = meshes
  )

def convert_link(link : URDFLink) -> ULink:
  hasOrigin = link.origin is not None
  hasVisual = link.visual is not None
  return ULink(
    name=link.name,
    visualName=link.visual.name if hasVisual else None,
    position=link.origin.position if hasOrigin else [0.0, 0.0, 0.0],
    rotation=link.origin.rotation if hasOrigin else [0.0, 0.0, 0.0]
  )

def convert_joint(joint : URDFJoint) -> UJoint:
  hasOrigin = joint.origin is not None
  hasLimit = joint.limit is not None
  return UJoint(
    name = joint.name,
    parentLink = joint.parent,
    childLink = joint.child,
    type = joint.type, # TODO convert this properly 
    axis = mj2unity_pos(joint.axis),
    position = mj2unity_pos(joint.origin.position) if hasOrigin else [0.0, 0.0, 0.0],
    rotation = mj2unity_euler(joint.origin.rotation) if hasOrigin else [0.0, 0.0, 0.0, 1.0],
    minRot=joint.limit.lower if hasLimit else 0.0,
    maxRot=joint.limit.upper if hasLimit else 0.0,
  )


def convert_urdf(data : URDFData) -> UEntity:
  return UEntity (
    name = data.name,
    links=[convert_link(link) for link in data.links],
    joints=[convert_joint(joint) for joint in data.joints],
    visuals=[convert_visual(link.visual) for link in data.links if link.visual is not None],
    manipulable = False
  )

start = time.monotonic()

data = URDFData.from_file(FILE_PATH)

header = UData([convert_urdf(data)])
data = header.package()
string_data = json.dumps(data, separators=(',', ':'))

dia_start = time.monotonic()
# with open("test.json", "w") as fp: json.dump(data, fp=fp, separators=(',', ':'))

end = time.monotonic()
cprint(f"Compiling took {dia_start - start :.2f}s (debugging {end - dia_start:.2f})", tag="TIME", tag_color="blue", color='white')

async def ws_server(websocket, path):

  async def send(type : UHeaderType, data : str):
    data = type + ":::" + data + "</>"      
    MAX_SIZE : int = 2**20
    parts = len(data) // MAX_SIZE + (1 if len(data) % MAX_SIZE else 0)
    for i in range(parts): await websocket.send(data[i * MAX_SIZE:(i + 1) * MAX_SIZE].encode())
  

  colors = {
    "MSG" : ("green", "white"),
    "ERR" : ("red", "white"),
  }

  fprint = lambda y, x: cprint(x, tag=y, tag_color=colors[y][0], color=colors[y][1])

  cprint("WebSocket: Server Started.", tag="INFO", tag_color="blue", color='white')
  await send(UHeaderType.DATA, string_data)

  try:
    async for message in websocket:
      fprint(*message.split(":::"))
  except websockets.exceptions.ConnectionClosedError:
    print("Client disconneted abnormaly")
  


# Start the WebSocket server
start_server = websockets.serve(ws_server, "localhost", 8053)
try:
  cprint("Waiting for connection", tag="SERVER", tag_color="blue", color='white')
  asyncio.get_event_loop().run_until_complete(start_server)
  asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
  print("Closing app")
