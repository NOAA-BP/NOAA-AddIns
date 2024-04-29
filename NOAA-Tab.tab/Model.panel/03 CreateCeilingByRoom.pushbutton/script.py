__title__="03 CreateCeilingByRoom"
__author__="Bogdan Popa"
__doc__="""Select Room & Create Ceiling"""


import sys
import clr
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, SpatialElementBoundaryOptions, CurveArray, Transaction, FloorType, Floor, CurveLoop, Level, SpatialElement, CeilingType, Ceiling  
from Autodesk.Revit.DB.Architecture import Room
from Autodesk.Revit.UI.Selection import ObjectType
from pyrevit import forms, revit

# Initialize document and application
uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document
app = doc.Application

def get_ceiling_types(doc):
    return FilteredElementCollector(doc).OfClass(CeilingType).ToElements()

def pick_ceiling_type(doc):
    ceiling_types = get_ceiling_types(doc)
    ceiling_type_names = [cl.FamilyName for cl in ceiling_types]
    selected_ciling_type = forms.SelectFromList.show(ceiling_type_names, title = 'Select Ceiling Type', multiselect=False)
    if not selected_ciling_type:
        sys.exit(0)
    ceiling_type = [cl for cl in ceiling_types if cl.FamilyName == selected_ciling_type][0]
    return ceiling_type

def prompt_for_height_offset(room):
    while True:
        try:
            height_offset = forms.ask_for_string(default="0", prompt = "Enter height offset for rooms:{}".format(str(room)))
            offset_value = float(height_offset)/304.8
            return offset_value
        except ValueError:
            forms.alert("Please enter a valid number.")  

def create_ceiling_from_room(room, ceiling_type, offset_value, doc):
    boundry_options = SpatialElementBoundaryOptions()
    room_boundary = room.GetBoundarySegments(boundry_options)
    if room_boundary:
        curve_list = [boundary.GetCurve() for boundary in room_boundary[0]]
        curve_loop = CurveLoop.Create(curve_list)
        curve_loops = [curve_loop]
        with Transaction(doc,'Create ceiling') as t:
            t.Start()
            Ceiling.Create(doc, curve_loops, ceiling_type.Id, room.Level.Id)

 #           room_zone = room.LookupParameter('Zone').AsString()
#            new_ceiling.LookupParameter('Zone').Set(room_zone)
 #           new_ceiling.LookupParameter('Height Offset From Level').Set(offset_value)
            t.Commit()

def main():
    try:
        # Let user select a room
        ref = uidoc.Selection.PickObject(ObjectType.Element, "Select a room.")
        selected_room = doc.GetElement(ref.ElementId)
        
        ceiling_type = pick_ceiling_type(doc)
        offset_value = prompt_for_height_offset(selected_room)

        create_ceiling_from_room(selected_room, ceiling_type, offset_value, doc)

    except Exception as e:
        print("Error:", str(e))

main()



























