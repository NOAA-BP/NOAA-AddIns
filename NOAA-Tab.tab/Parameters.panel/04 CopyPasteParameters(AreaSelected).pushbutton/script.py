__title__="04 CopyPasteParameters(AreaSelected)"
__author__="Bogdan Popa"
__doc__="""Select areas based on AREA TYPE and replaces target Para from source Para (excludes areas in groups)"""



import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')

from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Transaction, Area, Group, ElementId
from pyrevit import forms

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

# Collect all areas in the model
all_areas = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Areas).WhereElementIsNotElementType().ToElements()
print("Areas collected:{}".format(len(all_areas)))

# Group areas by their 'Name' parameter
area_groups = {}
for area in all_areas:
    name_param = area.LookupParameter('AREA TYPE')
    if name_param and name_param.HasValue:
        area_name = name_param.AsString()
        if area_name in area_groups:
            area_groups[area_name].append(area)
        else:
            area_groups[area_name] = [area]

# Prompt user to pick area names from the list
selected_area_names = forms.SelectFromList.show(sorted(area_groups.keys()), title='Select Areas', multiselect=True)

# If no area names are selected, exit the script
if not selected_area_names:
    forms.alert('No areas selected. Exiting.', exitscript=True)

# Get the selected area elements
selected_areas = []
for name in selected_area_names:
    selected_areas.extend(area_groups[name])


# Get all parameters from the first selected area to let the user choose
area = selected_areas[0]
parameters = area.Parameters
param_names = [param.Definition.Name for param in parameters if not param.IsReadOnly]

# Prompt user to select source and target parameters
source_param_name = forms.SelectFromList.show(param_names, title='Select Source Parameter')
target_param_name = forms.SelectFromList.show(param_names, title='Select Target Parameter')

# Ensure the user selected different parameters for source and target
if source_param_name == target_param_name:
    forms.alert('Source and target parameters must be different. Exiting.', exitscript=True)

count = 0
# Start copying values between parameters
with Transaction(doc, 'Copy Parameter Values') as t:
    t.Start()
    for area in selected_areas:
        # Check if the area is part of a group
        area_group_id = area.GroupId
        if area_group_id != ElementId.InvalidElementId:
            group = doc.GetElement(area_group_id)
            if isinstance(group, Group):
                print("Area ID: {} is part of group ID: {}. Skipping...".format(area.Id,group.Id))
                continue

        source_param = area.LookupParameter(source_param_name)
        target_param = area.LookupParameter(target_param_name)

        # Rest of your logic...
        if source_param and target_param and not target_param.IsReadOnly:
            if source_param.HasValue:
                target_param.Set(source_param.AsString())
                count += 1
            else:
                print("Failed to copy parameter for area ID: {}, source parameter does not have a value".format(area.Id))
    t.Commit()

print("Number of areas changed:{}".format(count))




