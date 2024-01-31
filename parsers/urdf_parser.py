from dataclasses import dataclass
import os
from typing import Any, Dict, List, Optional, Self, Tuple, TypeVar
import xml.etree.ElementTree as ET

####### Shared properties #######

XMLNode = ET.Element

def notnone(func): return lambda node: None if node is None else func(node)

def _load_attrib(node : XMLNode, attrib : str, default : Any) -> Any:
  if node is None or attrib not in node.attrib: return default
  return type(default)(node.attrib[attrib]) # parse to the type of the default (mostly used for float and int values)


def _load_attrib_array(node : XMLNode, attrib : str, default : List[Any], seperator=" "):
  if node is None or attrib not in node.attrib: return default
  result = [type(default[0])(i) for i in node.attrib[attrib].split(seperator)]
  assert len(result) == len(default)
  return result


@dataclass
class URDFOrigin:
  position : List[float]
  rotation : List[float]

  @notnone
  @staticmethod
  def parse(node : XMLNode) -> Self:
    return URDFOrigin( 
      _load_attrib_array(node, "xyz", [0.0, 0.0, 0.0]),
      _load_attrib_array(node, "rpy", [0.0, 0.0, 0.0]),
    )
  
  def __repr__(self):
    return f"{self.position}, {self.rotation}"

@dataclass
class URDFCalibration:
  rising : float
  falling : float

  @notnone
  @staticmethod
  def parse( node : XMLNode):
    return URDFCalibration( 
      _load_attrib(node, "rising", 0.0),
      _load_attrib(node, "falling", 0.0)
    )

@dataclass
class URDFDynamics:
  damping : float
  friction : float

  @notnone
  @staticmethod
  def parse( node : XMLNode):
    return URDFCalibration( 
      _load_attrib(node, "damping", 0.0),
      _load_attrib(node, "friction", 0.0)
    )

@dataclass
class URDFLimit:
  lower : float
  upper : float
  effort : float
  velocity : float

  @notnone
  @staticmethod
  def parse( node : XMLNode):
    return URDFLimit(
      _load_attrib(node, "lower", 0.0),
      _load_attrib(node, "upper", 0.0),
      _load_attrib(node, "effort", 0.0),
      _load_attrib(node, "velocity", 0.0), 
    )

@dataclass
class URDFMimic:
  joint : str
  mutiplier : float
  offset : float

  @notnone
  @staticmethod
  def parse( node : XMLNode):
    assert "joint" in node.attrib, "<mimic> field does not contain required attribute" 
    return URDFMimic(
      node.attrib["joint"], # required
      _load_attrib(node, "multiplier", 1.0),
      _load_attrib(node, "offset", 0.0)
    )

@dataclass
class URDFSafetyController:
  soft_lower_limit : float
  soft_upper_limit : float
  k_position : float 
  k_velocity : float

  @notnone
  @staticmethod
  def parse( node : XMLNode):
    assert "k_velocity" in node.attrib, "<k_velocity> is a required field in the field <safety_controller>"
    return URDFSafetyController(
      _load_attrib(node, "soft_lower_limit", 0.0),
      _load_attrib(node, "soft_upper_limit", 0.0),
      _load_attrib(node, "k_position", 0.0),
      _load_attrib(node, "k_velocity", 0.0)
    )




@dataclass
class URDFGeometry:
  type : str
  size : List[float]    # box
  length : float        # cylinder
  radius : float        # cylinder and sphere
  fileName : str        # mesh (relative to the parsed file)
  scale : List[float]

  @notnone
  @staticmethod
  def parse( node : XMLNode):
    child = node[0]
    viztype = child.tag
    assert child is not None, f"<geometry> field has to have a subfield in node with children"

    # very hacky 
    return URDFGeometry(
      viztype,
      _load_attrib_array(child, "size", [1.0, 1.0, 1.0]) if viztype == "box" else None,
      _load_attrib(child, "length", 1.0) if viztype == "cylinder" else None,
      _load_attrib(child, "radius", 1.0) if viztype in { "sphere", "cylinder" } else None,
      _load_attrib(child, "filename", "") if viztype == "mesh" else None,
      _load_attrib_array(child, "scales", [1.0, 1.0, 1.0])  if viztype == "mesh" else None,
    )
  
  def __repr__(self) -> str:
    match self.type:
      case "mesh":
        return f"mesh at {self.fileName} and scale {self.scale}"
      case _ :
        return self.type

@dataclass
class URDFMaterial:
  color : List[float]
  fileName : str
  
  @notnone
  @staticmethod
  def parse( node : XMLNode):
    return URDFMaterial(
      _load_attrib_array(node, "color", [0.0, 0.0, 0.0]),
      _load_attrib(node, "filename", "")
    )


@dataclass
class URDFVisual:
  name : str
  origin : URDFOrigin
  geometry : URDFGeometry
  material : URDFMaterial

  @notnone
  @staticmethod
  def parse( node : XMLNode):
    geometry = URDFGeometry.parse(node.find("geometry"))
    assert geometry is not None, "<geometry> is a required field in the field <visual>"
    name = _load_attrib(node, "name", os.path.basename(geometry.fileName).split(".")[0] + "_" + geometry.type) # TODO this is not unique

    return URDFVisual(
      name,
      URDFOrigin.parse(node.find("origin")),
      geometry,
      URDFMaterial.parse(node.find("material"))
    ) 
  
  def __repr__(self):
    return f"{self.geometry}"
    



@dataclass
class URDFCollision:
  name : str
  origin : URDFOrigin
  geometry : URDFGeometry

  @notnone
  @staticmethod
  def parse( node : XMLNode):
    assert node.find("geometry") is not None, "<geometry> is a required field in the field <collision>"
    return URDFCollision(
      _load_attrib(node, "name", ""),
      URDFOrigin.parse(node.find("origin")),
      URDFGeometry.parse(node.find("geometry"))
    )

@dataclass
class URDFLink: # DOC: https://wiki.ros.org/urdf/XML/link
  name : str
  # put inertia in this class because its vital
  origin : URDFOrigin
  mass : float
  inertia : Dict[str, float]
  visual : URDFVisual
  collision : URDFCollision

  @notnone
  @staticmethod
  def parse( node : XMLNode):
    inertial = node.find("inertial")
    return URDFLink(
      _load_attrib(node, "name", ""),
      URDFOrigin.parse(inertial.find("origin")) if inertial is not None else None,
      _load_attrib(inertial, "mass", 0.0) if inertial is not None else None,
      { name : float(value) for name, value in inertial.attrib.items() } if inertial is not None else None,  # yeah dont care 
      URDFVisual.parse(node.find("visual")),
      URDFCollision.parse(node.find("collsion"))
    )
  
  
  def __repr__(self) -> str:
    return f"<URDFLink {self.name} with visual {self.visual}>"

@dataclass
class URDFJoint: # DOC: https://wiki.ros.org/urdf/XML/joint
  name : str
  type : str
  origin : URDFOrigin
  parent : str
  child : str
  axis : List[float]
  calibration : URDFCalibration
  dynamics : URDFDynamics
  limit : URDFLimit
  mimic : URDFLimit
  safety_controller : URDFSafetyController

  @notnone
  @staticmethod
  def parse(node : XMLNode):
    parent = node.find("parent")
    child = node.find("child")
    axis = node.find("axis")

    return URDFJoint(
      _load_attrib(node, "name", ""),
      _load_attrib(node, "type", ""),
      URDFOrigin.parse(node.find("origin")),
      _load_attrib(parent, "link", ""),
      _load_attrib(child, "link", ""),
      _load_attrib_array(axis, "xyz", [1.0, 0.0, 0.0]),
      URDFCalibration.parse(node.find("calibration")),
      URDFDynamics.parse(node.find("dynamics")),
      URDFLimit.parse(node.find("limit")),
      URDFMimic.parse(node.find("mimic")),
      URDFSafetyController.parse(node.find("safety_controller"))
    )
  
  def __repr__(self) -> str:
    return f"<URDFJoint {self.name} of type {self.type} with axis {self.axis} and origin {self.origin}>"


@dataclass
class URDFData: # http://wiki.ros.org/urdf/XML/model
  name : str
  joints : List[URDFJoint]
  links : List[URDFLink]
  
  @staticmethod
  def parse(data : str, opt_name : Optional[str]= None) -> Optional[Self]:

    robot = ET.XML(data)

    if not robot: return None
    
    robot_name = robot.attrib["name"] if "name" in robot.attrib else opt_name 

    return URDFData(
      robot_name,
      [URDFJoint.parse(joint) for joint in robot.findall("joint")],
      [URDFLink.parse(link) for link in robot.findall("link")]
    )  
  
  @staticmethod 
  def from_file(file_path : str) -> Optional[Self]:
    with open(file_path, "r") as fp: return URDFData.parse(fp.read(), opt_name=os.path.basename(file_path).split(".")[0]) # if no name specified infere it from the file name

  def __repr__(self) -> str:
    return f"<URDFData {self.name}, with {len(self.joints)} joints and {len(self.links)} links>"




if __name__ == "__main__":
  import time
  start = time.monotonic()
  parser = URDFData.from_file("res/models/pybullet/robots/panda_arm_hand.urdf")
  print(parser)
  print(f"Took {time.monotonic() - start} sec")
  print("\n".join([str(joint) for joint in parser.joints]))
  print("\n".join([str(link) for link in parser.links]))