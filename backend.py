import functools
import json
import math
import os
from typing import Dict, List
import time
import numpy as np
from udata import UData, UHeaderType, UMesh, URobot, UJoint, ULink, UVisual
from scipy.spatial.transform import Rotation as R
from print_color import print as cprint
from parsers.urdf_parser import URDFJoint, URDFLink, URDFVisual, URDFData 
import trimesh
# ws imports
import websockets
import asyncio


# FILE_PATH = "res/models/test/panda.urdf"

FILE_PATH = "res/models/pybullet/robots/panda_arm_hand.urdf"
FOLDER = os.path.dirname(FILE_PATH)


def mj2unity_pos(pos): return [-pos[1], pos[2], pos[0]]
def mj2unity_euler(rot): return [rot[2], rot[1], -rot[0]]

def decompose_transform_matrix(matrix):
    u, sigma, vt = np.linalg.svd(matrix[:3, :3])
    rot = R.from_matrix(np.dot(u, np.dot(np.diag(sigma), vt))).as_euler("zyx")
    return rot.tolist(), matrix[:3, 3].tolist()

_meshes = {}

def convert_mesh(mesh : trimesh.base.Trimesh, matrix : np.ndarray, name : str) -> UMesh:
  conv = lambda x: [-x[0], x[1], x[2]]

  verts = [conv(x) for x in mesh.vertices]
  norms = [conv(x) for x in mesh.vertex_normals]
  indices = np.concatenate((mesh.faces[:, [2]], mesh.faces[:, [1]], mesh.faces[:, [0]]), axis=1).flatten().tolist()

  rot, pos = decompose_transform_matrix(matrix)
  pos = [-pos[1], pos[2], -pos[0]]
  rot[0] -= math.pi / 2
  rot[2] += math.pi / 2
  scale = [1, 1, 1]

  return UMesh(name, pos, rot, scale, indices, verts, norms)


def convert_visual(visual : URDFVisual) -> UVisual:
  file = visual.geometry.fileName.replace("package:/", FOLDER)
  if FOLDER not in file: file = FOLDER + file

  if file not in _meshes:
    scene = trimesh.load(file, force='scene')
    meshes = [convert_mesh(scene.geometry[item['geometry']], item['matrix'], item['geometry']) for item in scene.graph.transforms.edge_data.values()]
    _meshes[file] = meshes

  meshes = _meshes[file]

  hasOrigin = visual.origin is not None
  # if hasOrigin: print(visual.name, visual.origin.rotation)
  return UVisual(
    name=visual.name,
    type = visual.geometry.type,
    position=mj2unity_pos(visual.origin.position) if hasOrigin else [0.0, 0.0, 0.0],
    rotation=visual.origin.rotation if hasOrigin else [0.0, 0.0, 0.0],
    scale = visual.geometry.scale,
    meshes = meshes,
    materials=[]
  )

def convert_link(link : URDFLink) -> ULink:
  return ULink(
    name = link.name,
    visualName = link.visual.name if link.visual is not None else None,
    position = link.origin.position if link.origin is not None else [0.0, 0.0, 0.0],
    rotation = link.origin.rotation if link.origin is not None else [0.0, 0.0, 0.0]
  )

def convert_joint(joint : URDFJoint) -> UJoint:
  return UJoint(
    name = joint.name,
    parentLink = joint.parent,
    childLink = joint.child,
    type = joint.type, # TODO convert this properly 
    axis = mj2unity_pos(joint.axis),
    position = mj2unity_pos(joint.origin.position) if joint.origin is not None else [0.0, 0.0, 0.0],
    rotation = mj2unity_euler(joint.origin.rotation) if joint.origin is not None else [0.0, 0.0, 0.0, 1.0]
  )


def convert_urdf(data : URDFData) -> URobot:
  return URobot(
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
string_data = json.dumps(data)

dia_start = time.monotonic()
with open("test.json", "w") as fp: json.dump(data, indent=2, fp=fp)

end = time.monotonic()
cprint(f"Compiling took {dia_start - start :.2f}s (debugging {end - dia_start:.2f})", tag="TIME", tag_color="blue", color='white')


async def ws_server(websocket, path):


    async def send(type : UHeaderType, data : str):
      data = type + ":::" + data + "</>"      
      MAX_SIZE : int = 2**20
      parts = len(data) // MAX_SIZE + (1 if len(data) % MAX_SIZE else 0)
      for i in range(parts): await websocket.send(data[i * MAX_SIZE:(i + 1) * MAX_SIZE])
    

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
  asyncio.get_event_loop().run_until_complete(start_server)
  asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
  print("Closing app")
