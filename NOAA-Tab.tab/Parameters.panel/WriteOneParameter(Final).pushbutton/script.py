__title__="WriteParaOnSheets"
__author__="Bogdan Popa"
__doc__="""Sheet Number = XX-XXX
Sheet Name = ABC - Level 00"""

# Import necessary modules
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory
from Autodesk.Revit.UI import TaskDialog
from pyrevit import forms
from pyrevit import revit, DB

# Get the active Revit application and document
doc = __revit__.ActiveUIDocument.Document

# Prompt the user to select multiple sheets
sheets_to_modify = forms.select_sheets(title='Select Sheets to Modify')
if not sheets_to_modify:
    TaskDialog.Show("Error", "Please select sheets.")
    exit()

# Get the first selected sheet as a sample
sample_sheet = sheets_to_modify[0]

# Get a list of parameters from the sample sheet
sample_sheet_params = sample_sheet.Parameters
param_names = [param.Definition.Name for param in sample_sheet_params]

# Prompt the user to select a parameter to modify from the list
param_to_modify = forms.SelectFromList.show(param_names, title='Select a Parameter to Modify')
if not param_to_modify:
    TaskDialog.Show("Error", "No parameter selected.")
    exit()

# Prompt the user to enter a string to set as the new value for the selected parameter
new_param_value = forms.ask_for_string(default="", prompt="Enter new value for the parameter:", title="New Parameter Value")
if new_param_value is None:
    TaskDialog.Show("Error", "No value entered.")
    exit()

# Modify the selected parameter value in each of the selected sheets
with revit.Transaction("Modify Sheet Parameters"):
    for sheet in sheets_to_modify:
        # Find the parameter in the sheet
        param = sheet.LookupParameter(param_to_modify)
            
        # Set the parameter value
        if param:
            param.Set(new_param_value)
        else:
            print("Parameter '{}' not found in sheet '{}'.".format(param_to_modify, sheet.Name))
    
    TaskDialog.Show("Success", "Parameter values have been set in the selected sheets.")

















