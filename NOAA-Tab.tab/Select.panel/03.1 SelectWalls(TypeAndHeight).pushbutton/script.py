__title__="03.1 SelectWalls(TypeAndHeight)"
__author__="Bogdan Popa"
__doc__="""Just pick already.."""



import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import *
from System import *
from System.Collections.Generic import List
from Autodesk.Revit.UI import TaskDialog
from pyrevit import forms, sys, script

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document
active_view = doc.ActiveView


from pyrevit import forms
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, UnitUtils, SpecTypeId, FormatOptions, DisplayUnitType

#========================================================================================
# STEP 0 - FUNCTIONS LIBRARY
#========================================================================================

# Function to get all Revit links in the project
def get_all_revit_links(doc):
    return FilteredElementCollector(doc).OfClass(RevitLinkInstance)

# Function to isolate elements in the view
def isolate_elements_in_view(doc, element_ids):
    with Transaction(doc, "Isolate Elements") as t:
        t.Start()
        view = doc.ActiveView
        # Convert Python list to .NET List[ElementId]
        net_element_ids = List[ElementId](element_ids)
        view.IsolateElementsTemporary(net_element_ids)
        t.Commit()

# Function to isolate walls in the view
def isolate_walls_in_view(doc, walls):
    with Transaction(doc, "Isolate Walls") as t:
        t.Start()
        view = doc.ActiveView
        #view.IsolateElementsTemporary([wall.Id for wall in walls]) #This operates with the list
        # Convert Python list to .NET List[ElementId]
        element_ids = List[ElementId]([wall.Id for wall in walls])
        view.IsolateElementsTemporary(element_ids)
        t.Commit()

# Function to format the height value for display
def format_height(height, doc):
    # Convert internal unit (feet) to the desired display unit (meters or feet)
    # Use SpecTypeId.Length for length measurements
    display_units = doc.GetUnits().GetFormatOptions(SpecTypeId.Length).GetUnitTypeId()
    return UnitUtils.ConvertFromInternalUnits(height, display_units)


#========================================================================================
# STEP 1 - GET TARGETED WALLS, FILTER 1 - WALL TYPE
#========================================================================================
walls_in_view = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType().ToElements()
# Create a list to store all unique Wall Types in the project
wall_types = set()
# Iterate through all walls in the project and add their Wall Types to the list
for wall in walls_in_view:
    wall_type = Element.Name.GetValue(wall)
    if wall_type is not None:
        wall_types.add(wall_type)
# Convert the set to a sorted list
wall_type_list = sorted(wall_types)
# Prompt the user to select one or more Wall Types
selected_wall_type_internal = forms.SelectFromList.show(wall_type_list, title='Select Wall Type(s) For Internal Boundaries', multiselect=True)
if not selected_wall_type_internal:
    print("No wall type selected. Exiting script.")
    sys.exit(0)


#========================================================================================
# STEP 2 - GET AVAILABLE HEIGHTS FOR SELECTED WALL TYPES
#========================================================================================
wall_heights = set()
for wall in walls_in_view:
    if Element.Name.GetValue(wall) in selected_wall_type_internal:
        wall_height = wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).AsDouble()
        wall_heights.add(wall_height)

# Convert the set to a sorted list and convert heights to human-readable format (e.g., meters or feet)
wall_height_list = sorted([format_height(height,doc) for height in wall_heights])

# Prompt the user to select one or more wall heights
selected_wall_heights = forms.SelectFromList.show(wall_height_list, title='Select Wall Height(s)', multiselect=True)
if not selected_wall_heights:
    print("No wall height selected. Exiting script.")
    sys.exit(0)

#========================================================================================
# STEP 3 - FILTER SELECTED WALLS BY TYPE AND HEIGHT
#========================================================================================
filtered_walls_by_height = []
for wall in walls_in_view:
    if Element.Name.GetValue(wall) in selected_wall_type_internal:
        wall_height = wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).AsDouble()
        formatted_height = format_height(wall_height, doc)
        if formatted_height in selected_wall_heights:
            filtered_walls_by_height.append(wall)

# STEP 2.3 - VERIFY SELECTION
# Highlight filtered walls in the active view
uidoc.Selection.SetElementIds(List[ElementId]([w.Id for w in filtered_walls_by_height]))

# Print the IDs of the filtered walls
#for w in filtered_walls:
    #print("Filtered Wall ID:", w.Id)


#========================================================================================
# STEP 3 - PREPARE WALLS
#========================================================================================

# Main Script

# Assuming 'filtered_walls' is a list of wall elements from your previous script
selected_wall_ids = [wall.Id for wall in filtered_walls_by_height]

# Combine selected walls and links
selected_elements_ids = selected_wall_ids
# Isolate selected walls and links in view
isolate_elements_in_view(doc, selected_elements_ids)























    











