from abc import ABC, abstractmethod
import base64
from dataclasses import dataclass, is_dataclass
import dataclasses
from enum import Enum, auto
from functools import reduce
import json
import struct
from typing import Any, Iterable, Optional, Self, List, Tuple, Union, Set
import numpy as np


def dataclass_to_dict_rec(obj, exclude : Set = {}): 
  return { key: dataclass_to_dict_rec(value) for key, value in dataclasses.asdict(obj).items() if key not in exclude } if dataclasses.is_dataclass(obj) else obj

class UHeaderType(str, Enum):
  ENTITY = "ENTITY"
  MESH = "MESH"
  SHAPE = "SHAPE"
  UPDATE = "UPDATE"
  BEACON = "BEACON"
  SPAWN  = "SPAWN"
  DATA = "DATA"

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
  name : str
  manipulable : bool

  def package(self):
    pass

@dataclass(frozen=True)
class UMesh:
  shapeName : str
  indices : List[int] = None
  vertices : List[Tuple[float, float, float]] = None
  normals : List[Tuple[float, float, float]] = None
  color : Tuple[float, float, float] = None

  def package(self) -> List[str]: # maybe send as bin   
    result = {
      "shapeName" : self.shapeName,
      "vertices" : self.vertices.tolist() if isinstance(self.vertices, np.ndarray) else self.vertices,
      "indices" : [[inner[0] for inner in outer] for outer in self.indices.tolist()] if isinstance(self.indices, np.ndarray) else self.indices,
      "normals" : self.normals.tolist() if isinstance(self.normals, np.ndarray) else self.normals,
      "color" : self.color
    }

    return result



@dataclass(frozen=True)
class UShape:
  name : str
  type: UMeshType
  position : List[float]
  rotation : List[float]
  dimensions : List[float]
  meshes : List[UMesh]

  def package(self) -> List[str]:
    result = dataclass_to_dict_rec(self, exclude={ "meshes", "dimensions" })
    result["meshes"] = [mesh.package() for mesh in self.meshes]
    return result


@dataclass(frozen=True)
class URobotJoint:
  name : str
  parentIndex : int
  jointType : UJointType
  jointAxis : Tuple[float, float, float]
  jointPos : Tuple[float, float, float]
  jointRot : Tuple[float, float, float, float]
  meshID : str


@dataclass(frozen=True)
class URobot(UEntity):
  rootJointIndex : int
  joints : List[URobotJoint]

  def package(self):
    for joint in self.joints: print(joint.name, joint.jointPos)
    return dataclass_to_dict_rec(self)


@dataclass(frozen=True)
class UObject(UEntity):
  pass


@dataclass(frozen=True)
class UData():
  entities : List[UEntity] = None
  shapes : List[UShape] = None

  def package(self) -> List[Tuple[UHeaderType, str]]:
    return {
      "robots" : [robot.package() for robot in self.entities],
      "shapes" : { shape.name : shape.package() for shape in self.shapes}
    }
  


