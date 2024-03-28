from dataclasses import dataclass, is_dataclass, asdict
from enum import Enum
import math



def dataclass_to_dict_rec(obj, exclude : set = {}): 
  return { key: dataclass_to_dict_rec(value) for key, value in asdict(obj).items() if key not in exclude } if is_dataclass(obj) else obj


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
  BOX       = "BOX"
  SPHERE    = "SPHERE"
  CYLINDER  = "CYLINDER"
  CAPSULE   = "CAPSULE"
  PLANE     = "PLANE"
  MESH      = "MESH"
  
@dataclass
class UMaterial:
  name : str
  specular : list[float]
  diffuse : list[float]
  ambient : list[float]
  glossiness : float

  def __post_init__(self):
    assert self.name is not None and len(self.name) > 0

@dataclass
class UMesh:
  name : str
  position : list[float]
  rotation : list[float]
  scale : list[float]
  indices : list[int]
  vertices : list[list[float]]
  normals : list[list[float]]
  material : UMaterial = None

  def __post_init__(self):
    assert self.name is not None and len(self.name) > 0
    assert isinstance(self.position, list) and len(self.position) == 3 and isinstance(self.position[0], float)
    assert isinstance(self.rotation, list) and len(self.rotation) == 3 and isinstance(self.rotation[0], float)
    assert isinstance(self.scale, list) and len(self.scale) == 3

    assert len(self.normals) == len(self.vertices)

@dataclass(frozen=True)
class UVisual:
  name : str
  type : UVisualType
  position : list[float]
  rotation : list[float]
  scale : list[float]
  meshes : list[UMesh]

  def __post_init__(self):
    assert self.name is not None and len(self.name) > 0
    assert isinstance(self.position, list) and len(self.position) == 3 and isinstance(self.position[0], float)
    assert isinstance(self.rotation, list) and len(self.rotation) == 3 and isinstance(self.rotation[0], float)
    assert isinstance(self.scale, list) and len(self.scale) == 3 and isinstance(self.scale[0], float)
    assert self.type in UVisualType, f"Visual type {self.type} is not valid"
  
@dataclass(frozen=True)
class UJoint:
  name : str
  position : list[float]
  rotation : list[float]
  parentLink : str
  childLink : str
  type : UJointType
  axis : list[float]
  minRot : float
  maxRot : float

  def __post_init__(self):
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
  position : list[float]
  rotation : list[float]

  def __post_init__(self):
    assert self.name is not None and len(self.name) > 0
    assert isinstance(self.position, list) and len(self.position) == 3 and isinstance(self.position[0], float)
    assert isinstance(self.rotation, list) and len(self.rotation) == 3 and isinstance(self.rotation[0], float)
    for coord in self.rotation:
      assert coord > -2 * math.pi and coord < 2 * math.pi, f"Validation error on link {self.name}, rotation has to be radians"
  
@dataclass(frozen=True)
class UEntity:
  name : str
  manipulable : bool
  joints :  list[UJoint]
  links :   list[ULink]
  visuals : list[UVisual]

  def __post_init__(self):
    assert self.name is not None and len(self.name) > 0

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
  entities : list[UEntity] = None

  def package(self) -> list[dict]:
    return [entity.package() for entity in self.entities]
  

  


