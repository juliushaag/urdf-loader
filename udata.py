from dataclasses import dataclass, is_dataclass
import dataclasses
from enum import Enum
import math
from typing import List, Tuple, Set



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
  
class UVisualType(str, Enum):
  GEOMETRIC = "GEOMETRIC"
  BOX       = "BOX"
  SPHERE    = "SPHERE"
  CYLINDER  = "CYLINDER"
  CAPSULE   = "CAPSULE"
  PLANE     = "PLANE"
  MESH      = "MESH"
  
@dataclass
class UMaterial:
  name : str
  specular : List[float]
  diffuse : List[float]
  ambient : List[float]
  glossiness : float

  def validate(self):
    assert self.name is not None and len(self.name) > 0

@dataclass
class UMesh:
  name : str
  position : List[float]
  rotation : List[float]
  scale : List[float]
  indices : List[int]
  vertices : List[List[float]]
  normals : List[List[float]]
  material : UMaterial = None

  def validate(self):
    assert self.name is not None and len(self.name) > 0
    assert isinstance(self.position, list) and len(self.position) == 3 and isinstance(self.position[0], float)
    assert isinstance(self.rotation, list) and len(self.rotation) == 3 and isinstance(self.rotation[0], float)
    assert isinstance(self.scale, list) and len(self.scale) == 3 and isinstance(self.scale[0], float)

    assert len(self.normals) == len(self.vertices)

    if self.material is not None: self.material.validate()

@dataclass(frozen=True)
class UVisual:
  name : str
  type : UVisualType
  position : List[float]
  rotation : List[float]
  scale : List[float]
  meshes : List[UMesh]

  def validate(self):
    assert self.name is not None and len(self.name) > 0
    assert isinstance(self.position, list) and len(self.position) == 3 and isinstance(self.position[0], float)
    assert isinstance(self.rotation, list) and len(self.rotation) == 3 and isinstance(self.rotation[0], float)
    assert isinstance(self.scale, list) and len(self.scale) == 3 and isinstance(self.scale[0], float)
    assert self.type in UVisualType, f"Visual type {self.type} is not valid"

    for mesh in self.meshes: mesh.validate
  
@dataclass(frozen=True)
class UJoint:
  name : str
  position : Tuple[float, float, float]
  rotation : Tuple[float, float, float]
  parentLink : str
  childLink : str
  type : UJointType
  axis : Tuple[float, float, float]
  minRot : float
  maxRot : float

  def validate(self):
    assert self.name is not None and len(self.name) > 0
    assert isinstance(self.position, list) and len(self.position) == 3 and isinstance(self.position[0], float)
    assert isinstance(self.rotation, list) and len(self.rotation) == 3 and isinstance(self.rotation[0], float)
    for coord in self.rotation:
      assert coord > -2 * math.pi and coord < 2 * math.pi, f"Validation error on joint {self.name}, rotation has to be radians"

    assert self.type in UJointType, f"Invalid joint type {self.type}"
    assert isinstance(self.axis, list) and len(self.axis) == 3 and isinstance(self.axis[0], float)
    assert self.minRot > -2 * math.pi and self.minRot < 2 * math.pi, f"Validation error on joint {self.name}, minRot has to be radians"
    assert self.maxRot > -2 * math.pi and self.maxRot < 2 * math.pi, f"Validation error on joint {self.name}, maxRot has to be radians"
  
    

@dataclass(frozen=True)
class ULink:
  name : str
  visualName : str
  position : Tuple[float, float, float]
  rotation : Tuple[float, float, float]

  def validate(self):
    assert self.name is not None and len(self.name) > 0
    assert isinstance(self.position, list) and len(self.position) == 3 and isinstance(self.position[0], float)
    assert isinstance(self.rotation, list) and len(self.rotation) == 3 and isinstance(self.rotation[0], float)
    for coord in self.rotation:
      assert coord > -2 * math.pi and coord < 2 * math.pi, f"Validation error on link {self.name}, rotation has to be radians"
  
@dataclass(frozen=True)
class UEntity:
  name : str
  manipulable : bool
  joints : List[UJoint]
  links : List[ULink]
  visuals : List[UVisual]

  def validate(self):
    assert self.name is not None and len(self.name) > 0
    for joint in self.joints: joint.validate()
    for link in self.links: link.validate()
    for visual in self.visuals: visual.validate() 

  def package(self) -> dict:
     return {
      "name" : self.name,
      "startLink" : self.links[0].name,
      "manipulable" : self.manipulable,
      "joints" :  { joint.name : dataclass_to_dict_rec(joint) for joint in self.joints },
      "links" :   { link.name  : dataclass_to_dict_rec(link) for link in self.links },
      "visuals" : { visual.name : dataclass_to_dict_rec(visual) for visual in self.visuals }
    }


@dataclass(frozen=True)
class UData():
  entities : List[UEntity] = None

  def validate(self):
    for ent in self.entities: ent.validate()

  def package(self) -> List[dict]:
    self.validate()
    return [entity.package() for entity in self.entities]
  

  


