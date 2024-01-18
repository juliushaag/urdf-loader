import time
import pybullet as pb
from pprint import pprint
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Self, List, Tuple, Union
from collada import Collada

physicsClient = pb.connect(pb.DIRECT)

# Load a URDF model
robot = pb.loadURDF("res/models/pybullet/robots/panda_arm_hand.urdf")


class JointType(Enum):
  JOINT_REVOLUTE = pb.JOINT_REVOLUTE
  JOINT_PRISMATIC = pb.JOINT_PRISMATIC
  JOINT_SPHERICAL = pb.JOINT_SPHERICAL
  JOINT_PLANAR = pb.JOINT_PLANAR
  JOINT_FIXED = pb.JOINT_FIXED
  
  # Extend the MeshType enum to include other geometry types
class MeshType(Enum):
  GEOMETRIC = pb.GEOM_MESH
  BOX = pb.GEOM_BOX
  SPHERE = pb.GEOM_SPHERE
  CYLINDER = pb.GEOM_CYLINDER
  CAPSULE = pb.GEOM_CAPSULE
  PLANE = pb.GEOM_PLANE
  

@dataclass
class MeshData:
  vertices : List[(float, float, float)]
  normals : List[(float, float, float)] = None
  indices : List[int]

    
@dataclass
class VisualShapeInfo:
    id: int
    linkIndex: int
    geometryType: MeshType
    dimensions: Tuple[float, ...]
    meshFile: str
    framePosition: Tuple[float, float, float]
    frameOrientation: Tuple[float, float, float, float]
    color: Tuple[float, float, float, float]
    meshData: Optional[Union[List[Tuple[float, ...]], List[int]]] = None

    @staticmethod
    def from_robot(robot) -> List[Self]:
      shape_data = pb.getVisualShapeData(robot)
      shapes = [VisualShapeInfo(*data) for data in shape_data]

      for shape in shapes:
        mesh = Collada(shape.meshFile)

      return shapes

@dataclass(frozen=True)
class JointInfo:
  index : int
  name : str
  type : JointType
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
  parentFramePos : (float, float, float)
  parentFrameOrn : (float, float, float, float)
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
