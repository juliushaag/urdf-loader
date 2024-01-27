from dataclasses import dataclass
import os
from typing import Any, Dict, List, Self, Tuple, TypeVar
import xml.etree.ElementTree as ET

####### Shared properties #######

XMLNode = ET.Element

def notnone(func): return lambda node: None if node is None else func(node)

def _load_attrib(node : XMLNode, attrib : str, default : Any) -> Any:
  if node is None or attrib not in node.attrib: return default
  return type(default)(node.attrib[attrib]) # parse to the type of the default (mostly used for float and int values)


def _load_attrib_array(node : XMLNode, attrib : str, default : List[Any], seperator=" "):
  if node is None or attrib not in node.attrib: return default
  return [type(default[0])(i) for i in node.attrib[attrib].split(seperator)]


@dataclass
class URDFOrigin:
  position : List[float]
  rotation : List[float]

  @notnone
  @staticmethod
  def parse(node : XMLNode) -> Self:
    return URDFOrigin( 
      _load_attrib_array(node, "xyz", [0.0, 0.0, 0.0]),
      _load_attrib_array(node, "rpy", [0.0, 0.0, 0.0, 1.0]),
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
class URDFInertia:
  origin : URDFOrigin
  mass : float
  inertia : Dict[str, float]

  @notnone
  @staticmethod
  def parse( node : XMLNode):
    return URDFInertia(
      URDFOrigin.parse(node.find("origin")),
      _load_attrib(node, "mass", 0.0),
      { name : float(value) for name, value in inertia.attrib.items() } if (inertia := node.find("inertia") is not None) else None  # yeah dont care 
    )


@dataclass
class URDFGeometry:
  type : str
  size : List[float]    # box
  length : float        # cylinder
  radius : float        # cylinder and sphere
  fileName : str        # mesh
  scale : List[float]

  @notnone
  @staticmethod
  def parse( node : XMLNode):
    child = node[0]
    viztype, = child.tag,
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
      _load_attrib_array(node, "color", [0.0, 0.0, 0.0, 1.0]),
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
    assert node.find("geometry") is not None, "<geometry> is a required field in the field <visual>"
    return URDFVisual(
      _load_attrib(node, "name", ""),
      URDFOrigin.parse(node.find("origin")),
      URDFGeometry.parse(node.find("geometry")),
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
class URDFLink:
  name : str
  inertia : URDFInertia
  visual : URDFVisual
  collision : URDFCollision

  @notnone
  @staticmethod
  def parse( node : XMLNode):
    return URDFLink(
      _load_attrib(node, "name", ""),
      URDFInertia.parse(node.find("inertia")),
      URDFVisual.parse(node.find("visual")),
      URDFCollision.parse(node.find("collsion"))
    )
  
  
  def __repr__(self) -> str:
    return f"<URDFLink {self.name} with visual {self.visual}>"

@dataclass
class URDFJoint:
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


class UrdfParser: # http://wiki.ros.org/urdf/XML/model
  
  def __init__(self, file_name : str):
    fileData = ""
    with open(file_name, "r") as fp: fileData = fp.read()

    robot = ET.XML(fileData)
    
    assert robot is not None, f"Failed to parse the specified file {file_name} as xml"

    self.fileName = file_name

    assert robot is not None, f"The supplied file {file_name} does not contain a <robot> tag"

    self.name = robot.attrib["name"] if "name" in robot.attrib else os.path.basename(file_name).split(".")[0] # if no name specified infere it from the file name

    self.joints = [URDFJoint.parse(joint) for joint in robot.findall("joint")]
    
    self.links = [URDFLink.parse(link) for link in robot.findall("link")]

    for joint in self.links: print(joint)

    print(self)

  def __repr__(self) -> str:
    return f"<URDFData {self.name}, with {len(self.joints)} joints and {len(self.links)} links>"

if __name__ == "__main__":
  UrdfParser("res/models/pybullet/robots/camera.urdf")