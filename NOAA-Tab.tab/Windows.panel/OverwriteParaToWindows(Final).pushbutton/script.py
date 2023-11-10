__title__="OverwriteParaToWindows"
__author__="Bogdan Popa"
__doc__=""""""

# Import necessary modules
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Transaction
from Autodesk.Revit.UI import TaskDialog
from pyrevit import forms, sys
from pyrevit import revit, DB

# Get the active Revit application and document
doc = __revit__.ActiveUIDocument.Document

#Collect Windows
window_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).ToElements()
if not window_collector:
    print("No windows found in the model.")
    sys.exit(0)

#Collect Ids
window_collector_ids = [window.Id for window in window_collector]

# Prompt the user to select a parameter to modify from the list

#param_names = [param.Definition.Name for param in window_collector[0].Parameters]
#param_to_modify = forms.SelectFromList.show(param_names, title='Select a Parameter to Modify')
#if not param_to_modify:
#    print("No parameter selected. Exiting script.")
#    sys.exit(0)

# Get all parameter names, including shared parameters
param_names = set()  # Using a set to avoid duplicate names
for window in window_collector:
    for param in window.Parameters:
        if param.Definition:  # Checking if the parameter has a definition
            param_names.add(param.Definition.Name)

# Convert set to list for displaying in the UI
param_names = list(param_names)

# Prompt for Parameter Selection
param_to_modify = forms.SelectFromList.show(param_names, title='Select a Parameter to Modify')
if not param_to_modify:
    print("No parameter selected. Exiting script.")
    sys.exit(0)

# STEP 2 - COLLECT WINDOWS WITH PARAMETER VALUE

# Create dictionary window:parameterValue
windows_dict = {}
for window in window_collector:
    param = window.LookupParameter(param_to_modify)
    if param is not None and param.HasValue:
        param_value = param.AsString() or 'Undefined'
        if param_value not in windows_dict:
            windows_dict[param_value] = [window]
        else:
            windows_dict[param_value].append(window)
    

# Prompt the user to select a parameter value to modify from the list
param_value_to_modify = forms.SelectFromList.show(list(windows_dict.keys()), title ='Select Parameter Value to Modify')
if not param_value_to_modify:
    print("No parameter value selected. Exiting script.")
    sys.exit(0)

# STEP 3 - COLLECT NEW VALUE
# Prompt for new value
new_value = forms.ask_for_string(default="NewValue", prompt="Enter the new value for the parameter:", title="New Parameter Value")
if not new_value:
    print("No new value provided. Exiting script.")
    sys.exit(0)

print(windows_dict[param_value_to_modify], len(windows_dict[param_value_to_modify]))
# STEP 4 - WRITE NEW VALUE
# Modify Parameter Values in a Transaction
with Transaction(doc, "Update Window Parameter") as t:
    t.Start()
    count = 0
    for window in windows_dict[param_value_to_modify]:
        try:
            param = window.LookupParameter(param_to_modify)
            if param and param.IsReadOnly == False:
                param.Set(new_value)
                count += 1
        except Exception as e:
            print("Error updating window ID", window.Id.IntegerVallue, str(e))
    doc.Regenerate()
    t.Commit()
    print(count, "Windows updated")
























