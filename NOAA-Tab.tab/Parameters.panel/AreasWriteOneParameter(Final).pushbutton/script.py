__title__="WriteParaToAreas"
__author__="Bogdan Popa"
__doc__=""""""

# Import necessary modules
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory
from Autodesk.Revit.UI import TaskDialog
from pyrevit import forms, sys
from pyrevit import revit, DB

# Get the active Revit application and document
doc = __revit__.ActiveUIDocument.Document

# Collect areas
areas = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Areas).ToElements()

# Prompt the user to select areas by name
area_numbers = [area.LookupParameter("Number").AsString() if area.LookupParameter("Number") else "" for area in areas]
selected_area_numbers = forms.SelectFromList.show(area_numbers, title='Select Area', multiselect=True)

# Create a list of selected areas
selected_areas = [area for area in areas if area.LookupParameter("Number") and area.LookupParameter("Number").AsString() in selected_area_numbers]

if not selected_areas:
    print("No areas selected or no name parameter found. Exiting script.")
    sys.exit(0)

# Prompt the user to select a parameter to modify from the list
param_names = [param.Definition.Name for param in selected_areas[0].Parameters]
param_to_modify = forms.SelectFromList.show(param_names, title='Select a Parameter to Modify')
if not param_to_modify:
    print("No parameter selected. Exiting script.")
    sys.exit(0)

# Prompt the user to enter a string to set as the new value for the selected parameter
new_param_value = forms.ask_for_string(default="", prompt="Enter new value for the parameter:", title="New Parameter Value")
if new_param_value is None:
    print("No value entered. Exiting script.")
    sys.exit(0)

# Modify the selected parameter value in each of the selected areas
with revit.Transaction("Modify Area Parameters"):
    for area in selected_areas:
        # Find the parameter in the area
        param = area.LookupParameter(param_to_modify)

        # Set the parameter value
        if param:
            param.Set(new_param_value)
        else:
            print("Parameter '{}' not found in area '{}'.".format(param_to_modify, area.LookupParameter("Name").AsString()))

print("Parameter values have been set in the selected areas.")






















