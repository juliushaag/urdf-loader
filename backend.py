import dataclasses
import json
import os
import numpy as np
from dataclasses import dataclass
from typing import Optional, Self, List, Tuple, Union, dataclass_transform
from collada import Collada, primitive
import time
from udata import UData, UHeaderType, UMesh, URobot, UJoint, ULink, UVisual

from parsers.urdf_parser import URDFJoint, URDFLink, URDFVisual, URDFData 

start = time.monotonic()

FILE_PATH = "res/models/pybullet/robots/panda_arm_hand.urdf"
FOLDER = os.path.dirname(FILE_PATH)


data = URDFData.from_file(FILE_PATH)

def mj2unity_pos(pos): return [-pos[1], pos[2], pos[0]]


def mj2unity_euler(rot): return [-rot[1], rot[2], rot[0]]




def convert_visual(visual : URDFVisual) -> UVisual:
  file = FOLDER + visual.geometry.fileName
  collada_file = Collada(file) 
  meshes = [UMesh(indices=prim.vertex_index.tolist(), vertices=prim.vertex.tolist()) for geom in collada_file.geometries for prim in geom.primitives]


  hasOrigin = visual.origin is not None
  return UVisual(
    name=visual.name,
    type = visual.geometry.type,
    position=mj2unity_pos(visual.origin.position) if hasOrigin else [0.0, 0.0, 0.0],
    rotation=mj2unity_euler(visual.origin.rotation) if hasOrigin else [0.0, 0.0, 0.0],
    scale = visual.geometry.scale,
    meshes = meshes
  )

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
  return UJoint(
    name = joint.name,
    parentLink = joint.parent,
    childLink = joint.child,
    jointType = joint.type, # TODO convert this properly 
    jointAxis = mj2unity_pos(joint.axis),
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



end = time.monotonic()
print(f"Took { end - start } s")
start = end

header = UData([convert_urdf(data)])
data = header.package()
string_data = json.dumps(data)

end = time.monotonic()
print(f"Took { end - start } s")

# with open("test.json", "w") as fp: fp.write(string_data)

import websockets
import asyncio

async def ws_server(websocket, path):


    async def send(type : UHeaderType, data : str):
      data = type + ":::" + data + "</>"      
      MAX_SIZE : int = 2**20
      parts = len(data) // MAX_SIZE + (1 if len(data) % MAX_SIZE else 0)
      for i in range(parts): await websocket.send(data[i * MAX_SIZE:(i + 1) * MAX_SIZE])
      

    print("WebSocket: Server Started.")
    ws_start = time.monotonic()

    await send(UHeaderType.DATA, string_data)
    try:
      async for message in websocket:
       print(f"Took {time.monotonic() - ws_start}")
       print(message)
    except websockets.exceptions.ConnectionClosedError:
      print("Client disconneted abnormaly")

    print("Websocket closed")


# Start the WebSocket server
start_server = websockets.serve(ws_server, "localhost", 8053)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()