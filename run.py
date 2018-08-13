from Backdrop.Backdrop import Backdrop

import xml.etree.ElementTree as ET

# tree = ET.parse("settings.xml")
# root = tree.getroot()
# print(root)
runner = Backdrop()

args = ("admin", "Benehiko123!")
runner.run(args)
