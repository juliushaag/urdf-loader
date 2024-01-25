import dataclasses
import json
import os
import numpy as np
import pybullet as pb
from dataclasses import dataclass
from typing import Optional, Self, List, Tuple, Union, dataclass_transform
from collada import Collada
import time

from udata import UData, UHeaderType, UJointType, UMesh, UMeshType, UObjectType, URobot, URobotJoint, UShape


start = time.monotonic()

physicsClient = pb.connect(pb.DIRECT)

file_path = "res/models/pybullet/robots/panda_arm_hand.urdf"

robot_name = os.path.basename(file_path).split(".")[0]


# # Load a URDF model
robot = pb.loadURDF(file_path)


# pybullet doc https://docs.google.com/document/d/10sXEhzFRSnvFcl3XxNGhnD4N2SedqwdAvK3dsihxVUA/edit#heading=h.2ye70wns7io3

def urdf_to_joint_type(jointType : int) -> UJointType:
  match jointType:
    case pb.JOINT_REVOLUTE:   return UJointType.REVOLUTE
    case pb.JOINT_PRISMATIC:  return UJointType.PRISMATIC
    case pb.JOINT_SPHERICAL:  return UJointType.SPHERICAL
    case pb.JOINT_PLANAR:     return UJointType.PLANAR   
    case pb.JOINT_FIXED:      return UJointType.FIXED    
  

def urdf_to_mesh_type(meshType : int) -> UMeshType:
  match meshType:
    case pb.GEOM_MESH:      return UMeshType.GEOMETRIC 
    case pb.GEOM_BOX:       return UMeshType.BOX        
    case pb.GEOM_SPHERE:    return UMeshType.SPHERE     
    case pb.GEOM_CYLINDER:  return UMeshType.CYLINDER   
    case pb.GEOM_CAPSULE:   return UMeshType.CAPSULE    
    case pb.GEOM_PLANE:     return UMeshType.PLANE     
  

@dataclass
class MeshData:
  indices : List[int] 
  vertices : List[Tuple[float, float, float]]
  normals : List[Tuple[float, float, float]] = None

    
@dataclass
class VisualShapeInfo:
    id: int
    linkIndex: int
    geometryType: int
    dimensions: List[float]
    meshFile: str
    framePosition: List[float]
    frameOrientation: List[float]
    color: Tuple[float, float, float, float]
    meshData: List[MeshData] = None
    name : str = ""

    @staticmethod
    def load_meshes(robot) -> List[Self]:
      shape_data = pb.getVisualShapeData(robot)
      shapes = [VisualShapeInfo(*data) for data in shape_data]

      for shape in shapes:


        mesh = Collada(shape.meshFile) # Collada spec: https://www.khronos.org/files/collada_reference_card_1_4.pdf
        
        # for prim in obj.primitives(): # for loading materials in the future
        # materials.add(prim.material)
        shape.meshData = [MeshData(prim.indices, prim.vertex, prim.normal) for geom in mesh.geometries for prim in geom.primitives]
        name = os.path.basename(shape.meshFile.decode("utf-8")).split(".")[0]
        shape.name = name
      return shapes

@dataclass
class JointInfo:
  index : int
  name : str
  type : int
  qIndex : int #  the first position index in the positional state variables for this body
  uIndex : int  #  the first velocity index in the velocity state variables for this body
  flags : int # reserved
  jointDampingFactor : float
  jointFriction : float
  jointLowerLimit : float
  jointUpperLimit : float
  jointMaxForce : float
  jointMaxVelocity : float
  linkName : float
  jointAxis : (float, float, float)
  relPos : (float, float, float)
  relOrientation : (float, float, float, float)
  parentIndex : int
  shapeID : VisualShapeInfo = None
  
  @staticmethod
  def from_robot(robot, jointIndex) -> Self:
    return JointInfo(*pb.getJointInfo(robot, jointIndex))



num_elements = pb.getNumJoints(robot)
joints = [JointInfo.from_robot(robot, jointIndex) for jointIndex in range(num_elements)]
shapeInfo = VisualShapeInfo.load_meshes(robot)

for shape in shapeInfo: joints[shape.linkIndex].shapeID = shape.name

def mj2unity_pos(pos):
    return [pos[0], -pos[2], pos[1]]


def mj2unity_quat(quat):
    # note that the order is "[x, y, z, w]"
    return [quat[2], -quat[3], -quat[1], quat[0]]



def convert_shape(shape : VisualShapeInfo) -> UShape:
  pos = shape.framePosition
  rot = shape.frameOrientation
  return UShape(
    shape.name, 
    urdf_to_mesh_type(shape.geometryType), 
    pos, 
    rot, 
    shape.dimensions, 
    [UMesh(shape.name, mesh.indices,  mesh.vertices, mesh.normals, shape.color) for mesh in shape.meshData]
  )

def convert_joint(joint : JointInfo) -> URobotJoint:
  return URobotJoint(
    name = joint.name.decode("utf-8"),
    parentIndex = joint.parentIndex,
    jointType = urdf_to_joint_type(joint.type),
    jointAxis = mj2unity_pos(joint.jointAxis),
    jointPos = mj2unity_pos(joint.relPos),
    jointRot = mj2unity_quat(joint.relOrientation),
    meshID = joint.shapeID
  )


def convert_robot(robotName : str, joints : List[JointInfo]) -> URobot:
  return URobot(
    name = robotName,
    rootJointIndex=0,
    joints = [convert_joint(joint) for joint in joints], 
    manipulable = False
  )



end = time.monotonic()
print(f"Took { end - start } s")
start = end

header = UData([convert_robot(robot_name, joints)], [convert_shape(shape) for shape in shapeInfo])
data = header.package()
string_data = json.dumps(data)

end = time.monotonic()
print(f"Took { end - start } s")

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