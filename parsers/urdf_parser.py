from dataclasses import dataclass
from typing import Dict, List
import xml.etree.ElementTree as ET

@dataclass
class URDFLinkInertial:
  originPos : List[float]
  originRot : List[float]
  mass : int
  inertia : Dict[str, int]

@dataclass
class URDFGeometry:
  type : str
  size : List[float]
  fileName : str


@dataclass
class URDFMaterial:
  fileName : str
  color : List[float]


@dataclass
class URDFLinkVisual:
  originPos : List[float]
  originRot : List[float]
  geometry : URDFGeometry
  material : URDFMaterial

@dataclass
class URDFLinkCollision:
  name : str
  originPos : List[float]
  originRot : List[float]
  geometry : URDFGeometry

@dataclass
class URDFJoint:
  name : str
  type : str  
  originPos : List[float]
  originRot : List[float]
  parent : str
  child : str
  calibrationRising : float
  damping : float
  friction : float
  effort : float
  velocity : float
  lower : float
  upper : float
  # skipping safety controllers


class UrdfParser: # http://wiki.ros.org/urdf/XML/model
  
  def __init__(self, file_name : str):
    fileData = ""
    with open(file_name, "r") as fp: fileData = fp.read()
    root = ET.XML(fileData)
    
    self.fileName = file_name

    self.joints = [self.load_joint(joint) for joint in root.findall("joint")]
    
    self.links = [self.load_link(link) for link in root.findall("link")]
  

  def load_joint(self, element): # http://wiki.ros.org/urdf/XML/joint
    
    origin = element.find("origin").attrib
    parent = element.find("parent").attrib
    child = element.find("child").attrib
    cali = element.find("calibration").attrib if element.find("calibration") else None
    dynamics = element.find("dynamics").attrib if element.find("calibration") else None
    limit = element.find("limit").attrib if element.find("calibration") else None


    result = URDFJoint(
      name = element.attrib["name"],
      type = element.attrib["type"],
      originPos = [float(num) for num in origin["xyz"].split(" ")],
      originRot = [float(num) for num in origin["rpy"].split(" ")],
      parent = parent["link"],
      child = child["link"],
      calibrationRising = float(cali["rising"]) if cali is not None else None,
      damping = dynamics["damping"] if dynamics is not None else None,
      friction= dynamics["friction"] if dynamics is not None else None,
      effort=limit['limit'] if limit is not None else None,
      velocity=['velocity'] if limit is not None else None,
      lower=limit['lower'] if limit is not None else None,
      upper=limit["upper"] if limit is not None else None,
    )

    return result
  

  def load_link(self, element): # http://wiki.ros.org/urdf/XML/link
    inertial = element.find("inertial")
    visual = element.find('visual')
    collison = element.find("collision")


    vistype = visual[0].tag
    visualResult = URDFLinkVisual(
      originPos = [float(num) for num in visual.find("origin").attrib["xyz"].split(" ")],
      originRot = [float(num) for num in visual.find("origin").attrib["rpy"].split(" ")],
      type = vistype,
      size = [float(num) for num in visual[0].attrib["size"].split(" ")] if vistype == "box" else None,
      radius = visual[0].attrib["radius"] if vistype == "sphere" or vistype == "cylinder" else None,
      length = visual[0].attrib["length"] if vistype == "cylinder" else None,
      fileName = visual[0].attrib["filename"] if vistype == "mesh" else None,
      scale = [float(num) for num in visual[0].attrib["scale"].split(" ")] if vistype == "mesh" else None,
    )

    collisionResult = URDFLinkCollision(
      name = collison.attrib["name"],
      originPos = [float(num) for num in collison.find("origin").attrib["xyz"].split(" ")],
      originRot = [float(num) for num in collison.find("origin").attrib["rpy"].split(" ")],
      # TODO load geometry
    )
    
    print(element)



if __name__ == "__main__":
  UrdfParser("res/models/pybullet/robots/panda_arm_hand.urdf")