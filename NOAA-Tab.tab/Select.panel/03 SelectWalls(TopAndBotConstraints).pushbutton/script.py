__title__="03 SelectWallsAndLink(TopAndBotConstraints)"
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
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Line, XYZ

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

# Helper function to get user input for parameter values
def get_user_input_for_parameters():
    base_offset = forms.ask_for_string(default="", prompt="Enter new Base Level Offset", title="Base Level Offset")
    top_level = forms.ask_for_string(default="", prompt="Enter new Top Level", title="Top Level")
    top_offset = forms.ask_for_string(default="", prompt="Enter new Top Offset", title="Top Offset")
    return base_offset, top_level, top_offset

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

# Function to prompt user for manual group editing
def prompt_for_manual_group_editing():
    forms.alert("Please manually select a group, enter edit mode, and select the walls inside. Press OK when ready.")

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
# STEP 2 - GET TARGETED WALLS, FILTER 2 - BASE AND TOP LEVELS
#========================================================================================

# STEP 2.1 - USER INPUT
levels = FilteredElementCollector(doc).OfClass(Level).ToElements()
level_names = sorted([level.Name for level in levels])
level_names.append("Unconnected")  # Add the "Unconnected" option

selected_base_constraints = forms.SelectFromList.show(level_names, title='Select Base Constraint Level(s)', multiselect=True)
if not selected_base_constraints:
    print("No base constraint level selected. Exiting script.")
    sys.exit(0)
selected_top_constraints = forms.SelectFromList.show(level_names, title='Select Top Constraint Level(s)', multiselect=True)
if not selected_top_constraints:
    print("No top constraint level selected. Exiting script.")
    sys.exit(0)

# STEP 2.2 - FILTER WALLS BASED ON SELECTED CRITERIA
filtered_walls = []
for wall in walls_in_view:
    if Element.Name.GetValue(wall) in selected_wall_type_internal:
        base_level_id = wall.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT).AsElementId()
        top_level_id = wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE).AsElementId()
        base_level = doc.GetElement(base_level_id)
        top_level = doc.GetElement(top_level_id)

        is_base_match = base_level and base_level.Name in selected_base_constraints
        is_top_match = top_level and top_level.Name in selected_top_constraints
        is_unconnected = top_level_id.IntegerValue == -1 and "Unconnected" in selected_top_constraints

        if is_base_match and (is_top_match or is_unconnected):
            filtered_walls.append(wall)

# STEP 2.3 - VERIFY SELECTION
# Highlight filtered walls in the active view
uidoc.Selection.SetElementIds(List[ElementId]([w.Id for w in filtered_walls]))

# Print the IDs of the filtered walls
#for w in filtered_walls:
    #print("Filtered Wall ID:", w.Id)


#========================================================================================
# STEP 3 - PREPARE WALLS
#========================================================================================

# Main Script

# Get all Revit links
revit_links = get_all_revit_links(doc)
link_dict = {link.Name: link.Id for link in revit_links}

# Prompt user for Revit link selection
selected_link_names = forms.SelectFromList.show(sorted(link_dict.keys()), title='Select Revit Link(s)', multiselect=True)
if not selected_link_names:
    forms.alert("No Revit link selected. Exiting script.")
    sys.exit(0)

# Get IDs of selected links
selected_link_ids = [link_dict[name] for name in selected_link_names]
# Main script

# Assuming 'filtered_walls' is a list of wall elements from your previous script
selected_wall_ids = [wall.Id for wall in filtered_walls]

# Combine selected walls and links
selected_elements_ids = selected_wall_ids + selected_link_ids

# Isolate selected walls and links in view
isolate_elements_in_view(doc, selected_elements_ids)

#isolate_walls_in_view(doc, filtered_walls)

# Prompt user for manual action
prompt_for_manual_group_editing()























    











