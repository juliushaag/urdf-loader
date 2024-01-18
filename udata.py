from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Self, List, Tuple, Union


class UJointType(str, Enum):
  REVOLUTE  = "REVOLUTE"
  PRISMATIC = "PRISMATIC"
  SPHERICAL = "SPHERIACAL"
  PLANAR    = "PLANAR"
  FIXED     = "FIXED"
  
class UMeshType(str, Enum):
  GEOMETRIC = "GEOMETRIC"
  BOX       = "BOX"
  SPHERE    = "SPHERE"
  CYLINDER  = "CYLINDER"
  CAPSULE   = "CAPSULE"
  PLANE     = "PLANE"
  
class UObjectType(str, Enum):
  ROBOT = "ROBOT"
  OBJECT = "OBJECT"

@dataclass(frozen=True)
class UEntity:
  type : UObjectType 
  name : str
  manipulable : bool

@dataclass(frozen=True)
class UMesh:
  type: UMeshType
  indices : List[int] = None
  vertices : List[Tuple[float, float, float]] = None
  normals : List[Tuple[float, float, float]] = None
  color : Tuple[float, float, float] = None


@dataclass(frozen=True)
class URobotJoint:
  name : str
  parentIndex : int
  jointType : UJointType
  jointAxis : Tuple[float, float, float]
  jointPos : Tuple[float, float, float]
  jointRot : Tuple[float, float, float, float]
  mesh : UMesh

@dataclass(frozen=True)
class URobot(UEntity):
  rootJointIndex : int
  joints : List[URobotJoint]


@dataclass(frozen=True)
class UObject(UEntity):
  pass

