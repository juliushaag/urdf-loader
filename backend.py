import dataclasses
import json
import os
import numpy as np
import pybullet as pb
from dataclasses import dataclass
from typing import Optional, Self, List, Tuple, Union, dataclass_transform
from collada import Collada
import time

from udata import UJointType, UMesh, UMeshType, UObjectType, URobot, URobotJoint


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
    dimensions: Tuple[float, ...]
    meshFile: str
    framePosition: Tuple[float, float, float]
    frameOrientation: Tuple[float, float, float, float]
    color: Tuple[float, float, float, float]
    meshData: MeshData = None

    @staticmethod
    def from_robot(robot) -> List[Self]:
      shape_data = pb.getVisualShapeData(robot)
      shapes = [VisualShapeInfo(*data) for data in shape_data]

      for shape in shapes:
        mesh = Collada(shape.meshFile)

        for geom in mesh.geometries:
          for prim in geom.primitives:
            shape.meshData = MeshData( # loads mesh data (could be extended to uvs etc.)
                vertices = prim.vertex.tolist(),
                normals = prim.normal.tolist() if isinstance(prim.normal, np.ndarray) else prim.normal,
                indices = prim.indices.tolist() if isinstance(prim.indices, np.ndarray) else prim.indices
            )

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
  mesh : VisualShapeInfo = None
  
  @staticmethod
  def from_robot(robot, jointIndex) -> Self:
    return JointInfo(*pb.getJointInfo(robot, jointIndex))



    

    
num_elements = pb.getNumJoints(robot)
joints = [JointInfo.from_robot(robot, jointIndex) for jointIndex in range(num_elements)]
shapeInfo = VisualShapeInfo.from_robot(robot)

for shape in shapeInfo:
    mesh_filename = shape.meshFile
    linkIndex = shape.linkIndex
    joints[linkIndex].mesh = shape

def convert_mesh(mesh : VisualShapeInfo) -> UMesh:
  return UMesh(
    urdf_to_mesh_type(mesh.geometryType),
    indices = mesh.meshData.indices,
    normals = mesh.meshData.normals,
    vertices= mesh.meshData.vertices,
    color = mesh.color
  )

def convert_joint(joint : JointInfo) -> URobotJoint:
  return URobotJoint(
    name = joint.name.decode("utf-8"),
    parentIndex= joint.parentIndex,
    jointType= urdf_to_joint_type(joint.type),
    jointAxis= joint.jointAxis,
    jointPos= joint.relPos,
    jointRot= joint.relOrientation,
    mesh=  convert_mesh(joint.mesh) if joint.mesh else None 
  )


def convert_robot(robotName, joints : List[JointInfo]) -> URobot:
  return URobot(
    name = robotName,
    rootJointIndex=0,
    joints = [convert_joint(joint) for joint in joints], 
    type = UObjectType.ROBOT,
    manipulable = False
  )



end = time.monotonic()
print(f"Took { end - start } s")

### Everything loaded 
class EnhancedJSONEncoder(json.JSONEncoder):
  def default(self, o): return dataclasses.asdict(o) if dataclasses.is_dataclass(o) else super().default(o)
    

with open("test.json", "w") as fp:
  json.dump(convert_robot(robot_name, joints), fp, cls=EnhancedJSONEncoder)

