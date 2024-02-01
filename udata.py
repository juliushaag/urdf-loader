from dataclasses import dataclass, is_dataclass
import dataclasses
from enum import Enum
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
  
class UGeoType(str, Enum):
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

@dataclass
class UMesh:
  name : str
  position : List[float]
  rotation : List[float]
  scale : List[float]
  indices : List[int]
  vertices : List[List[float]]
  normals : List[List[float]]
  color : List[float] = None
  material : str = None

  def __repr__(self):
    return f"<UMesh {self.name} with {len(self.indices) } indices and {len(self.vertices)} vertices>"


@dataclass
class UMaterial:
  name : str
  id : str
  emission : List[float] 
  ambient : List[float]
  diffuse : List[float]
  specular : List[float]
  shininess : float
  reflective : List[float]
  reflectivity : float 
  transparent : List[float]
  transparency : float 


@dataclass(frozen=True)
class UVisual:
  name : str
  type : str
  position : List[float]
  rotation : List[float]
  scale : List[float]
  meshes : List[UMesh]
  materials : List[UMaterial]

  def package(self) -> List[str]: # maybe send as bin   
    result = dataclass_to_dict_rec(self)
    result['materials'] = { mat.id : dataclass_to_dict_rec(mat) for mat in self.materials }
    return result 
  
@dataclass(frozen=True)
class UJoint:
  name : str
  position : Tuple[float, float, float]
  rotation : Tuple[float, float, float]
  parentLink : str
  childLink : str
  type : UJointType
  axis : Tuple[float, float, float]

@dataclass(frozen=True)
class ULink:
  name : str
  visualName : str
  position : Tuple[float, float, float]
  rotation : Tuple[float, float, float]
  


@dataclass(frozen=True)
class URobot(UEntity):
  joints : List[UJoint]
  links : List[ULink]
  visuals : List[UVisual]

  def package(self) -> dict:
    return {
      "name" : self.name,
      "startLink" : self.links[0].name,
      "manipulable" : self.manipulable,
      "joints" :  { joint.name : dataclass_to_dict_rec(joint) for joint in self.joints },
      "links" :   { link.name  : dataclass_to_dict_rec(link) for link in self.links },
      "visuals" : { visual.name : visual.package() for visual in self.visuals }
    }


@dataclass(frozen=True)
class UObject(UEntity):
  pass


@dataclass(frozen=True)
class UData():
  entities : List[UEntity] = None

  def package(self) -> List[dict]:
    return [entity.package() for entity in self.entities]
  


