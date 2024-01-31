import dataclasses
import json
import math
import os
import numpy as np
from dataclasses import dataclass
from typing import Optional, Self, List, Tuple, Union, dataclass_transform
from collada import Collada, primitive
import time
from udata import UData, UHeaderType, UMaterial, UMesh, URobot, UJoint, ULink, UVisual
from scipy.spatial.transform import Rotation as R
from pprint import pprint
from collada import Collada
from print_color import print as cprint

from parsers.urdf_parser import URDFJoint, URDFLink, URDFVisual, URDFData 

def pad(text, max=20): 
  if type(text) != str: text = str(text)
  if len(text) > max: return text[:max-3] + "." * 3
  else: return text + " " * (max - len(text)) 

start = time.monotonic()

FILE_PATH = "res/models/test/panda.urdf"
FOLDER = os.path.dirname(FILE_PATH)


data = URDFData.from_file(FILE_PATH)

def mj2unity_pos(pos): return [-pos[1], pos[2], pos[0]]


def mj2unity_euler(rot):
  return [rot[2], rot[1], -rot[0]]

def decompose_transform_matrix(matrix):
    # Extract the upper left 3x3 submatrix (rotation part)
    r = matrix[:3, :3]
    
    # Perform SVD decomposition
    u, sigma, vt = np.linalg.svd(r)
    
    # Construct the rotation matrix R as UV^T
    r = R.from_matrix(np.dot(u, np.dot(np.diag(sigma), vt))).as_euler("zyx")

    
    # Obtain the translation part
    t = matrix[:3, 3]

    return r, t


def convert_visual(visual : URDFVisual) -> UVisual:
  file = visual.geometry.fileName.replace("package:/", FOLDER)
  collada_file = Collada(file) 

  # materials = []
  # for material in collada_file.materials:
  #   materials += [UMaterial(
  #     material.name,
  #     material.id,
  #     material.effect.emission,
  #     material.effect.ambient,
  #     material.effect.diffuse,
  #     material.effect.specular,
  #     material.effect.shininess,
  #     material.effect.reflective,
  #     material.effect.reflectivity,
  #     material.effect.transparent,
  #     material.effect.transparency
  #   )]


  meshes = []
  for node in collada_file.scene.nodes:
    id = node.id
    matrix = node.matrix

    rot, pos = decompose_transform_matrix(matrix)
    pos = pos.tolist()
    pos = [-pos[1], pos[2], -pos[0]]
    rot = rot.tolist()
    rot[0] -= math.pi / 2
    rot[2] += math.pi / 2
    scale = [1, 1, 1]

    for child in node.children:
      mat = child.materials[0].target.id

      for prim in child.geometry.primitives:
        meshes += [UMesh(id, pos, rot, scale, prim.vertex_index.tolist(), prim.vertex.tolist(), material=mat)]

  hasOrigin = visual.origin is not None
  result = UVisual(
    name=visual.name,
    type = visual.geometry.type,
    position=mj2unity_pos(visual.origin.position) if hasOrigin else [0.0, 0.0, 0.0],
    rotation=mj2unity_euler(visual.origin.rotation) if hasOrigin else [0.0, 0.0, 0.0],
    scale = visual.geometry.scale,
    meshes = meshes,
    materials=[]
  )

  result.rotation[1] += math.pi / 2

  return result

def convert_link(link : URDFLink) -> ULink:
  position = link.origin.position if link.origin is not None else [0.0, 0.0, 0.0]
  rotation = link.origin.rotation if link.origin is not None else [0.0, 0.0, 0.0]
  vis_name = link.visual.name if link.visual is not None else None


  return ULink(
    name = link.name,
    visualName = vis_name,
    position=position,
    rotation=rotation
  )

def convert_joint(joint : URDFJoint) -> UJoint:

  result = UJoint(
    name = joint.name,
    parentLink = joint.parent,
    childLink = joint.child,
    type = joint.type, # TODO convert this properly 
    axis = mj2unity_pos(joint.axis),
    position = mj2unity_pos(joint.origin.position) if joint.origin is not None else [0.0, 0.0, 0.0],
    rotation = mj2unity_euler(joint.origin.rotation) if joint.origin is not None else [0.0, 0.0, 0.0, 1.0]
  )
  return result


def convert_urdf(data : URDFData) -> URobot:
  robot = URobot(
    name = data.name,
    links=[convert_link(link) for link in data.links],
    joints=[convert_joint(joint) for joint in data.joints],
    visuals=[convert_visual(link.visual) for link in data.links if link.visual is not None],
    manipulable = False
  )
  return robot



end = time.monotonic()
print(f"Took { end - start } s")
start = end

header = UData([convert_urdf(data)])
data = header.package()
string_data = json.dumps(data)

end = time.monotonic()
print(f"Took { end - start } s")

with open("test.json", "w") as fp: json.dump(data, indent=2, fp=fp)


import websockets
import asyncio

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
  
    print("WebSocket: Server Started.")
    ws_start = time.monotonic()

    await send(UHeaderType.DATA, string_data)
    try:
      async for message in websocket:
       fprint(*message.split(":::"))
    except websockets.exceptions.ConnectionClosedError:
      print("Client disconneted abnormaly")
    except Exception:
      print("Closing websocket")


# Start the WebSocket server
start_server = websockets.serve(ws_server, "localhost", 8053)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()