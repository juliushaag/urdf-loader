from abc import ABC, abstractmethod
import base64
from dataclasses import dataclass, is_dataclass
import dataclasses
from enum import Enum, auto
from functools import reduce
import json
import struct
from typing import Any, Iterable, Optional, Self, List, Tuple, Union, Set
from attr import asdict
from dataclasses_json import dataclass_json
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
    
    return (UHeaderType.MESH, json.dumps(result))



@dataclass(frozen=True)
class UShape:
  name : str
  type: UMeshType
  position : List[float]
  rotation : List[float]
  meshes : List[UMesh]

  def package(self) -> List[str]:
    print(self.dimensions)
    result = [(UHeaderType.SHAPE, json.dumps(dataclass_to_dict_rec(self, exclude={ "meshes" })))]
    result += [mesh.package() for mesh in self.meshes] if self.meshes else []
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
    return (UHeaderType.ENTITY, json.dumps(dataclass_to_dict_rec(self)))


@dataclass(frozen=True)
class UObject(UEntity):
  pass


@dataclass(frozen=True)
class UData():
  entities : List[UEntity] = None
  shapes : List[UShape] = None

  def package(self) -> List[Tuple[UHeaderType, str]]:
    shapes = reduce(lambda x, y: x + y, [shape.package() for shape in self.shapes]) if self.shapes else []  
    entities = [entity.package() for entity in self.entities] if self.entities else []
    return shapes + entities


