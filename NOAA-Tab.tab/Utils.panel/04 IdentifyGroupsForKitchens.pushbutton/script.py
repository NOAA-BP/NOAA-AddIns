__title__="03 ScheduleReplaceFilters(SchedulePerSheet)"
__author__="Bogdan Popa"
__doc__="""It removes one filter at index and name, it adds a new filter at the end of the list"""

from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, Transaction, ElementId
from Autodesk.Revit.UI.Selection import ObjectType
from rpw.ui.forms import SelectFromList
from System.Collections.Generic import List

# Access the current document
app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document

# Function to collect plumbing fixtures and allow user selection
def collect_and_select_plumbing_fixtures(doc):
    # Collect all plumbing fixtures
    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures).WhereElementIsNotElementType()
    fixtures = list(collector)

    # Prepare fixture names for selection
    fixture_names = [f.Name for f in fixtures]
    unique_fixture_names = list(set(fixture_names))  # Remove duplicates

    # User selection
    selected_name = SelectFromList('Select Fixture Family', unique_fixture_names)

    return selected_name

# Function to list groups containing the selected fixture family
def list_fixture_groups(doc, selected_name):
    groups = []
    count = 0 
    # Ensure a selection was made
    if selected_name:
        # Collect all instances again to match the selected name and find their groups
        collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures).WhereElementIsNotElementType()
        for f in collector:
            if f.Name == selected_name and f.GroupId.IntegerValue != -1:  # Check if part of a group
                count += 1
                group = doc.GetElement(f.GroupId)
                if group.Name not in groups:
                    groups.append(group.Name)
        print("NUMBRER OF KITCHENS / GROUPS:",count)
    return groups

# Function to collect areas based on 'Apartment Number' and check if they are in the same group as the selected fixture
def list_areas_by_apartment_number(doc, selected_name, selected_groups):
    # Collect all areas
    area_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Areas).WhereElementIsNotElementType()
    areas = list(area_collector)

    # Filter areas by those that have a specified 'Apartment Number' and are in the selected groups
    apartment_areas = {}
    for area in areas:
        apartment_number = area.LookupParameter('Apartment Number')
        if apartment_number and apartment_number.AsString() and area.GroupId in [ElementId(gid) for gid in selected_groups]:
            # Check if area's group is one of the selected fixture's groups
            group_name = doc.GetElement(area.GroupId).Name
            if apartment_number.AsString() not in apartment_areas:
                apartment_areas[apartment_number.AsString()] = [group_name]
            elif group_name not in apartment_areas[apartment_number.AsString()]:
                apartment_areas[apartment_number.AsString()].append(group_name)

    return apartment_areas

# Example usage in a Revit Command
# Replace 'commandData' with the actual command data passed to your Execute method
# doc = commandData.Application.ActiveUIDocument.Document

# Start transaction (if modifying the document)
# t = Transaction(doc, 'List Plumbing Fixture Groups')
# t.Start()

selected_name = collect_and_select_plumbing_fixtures(doc)
groups = list_fixture_groups(doc, selected_name)
print(groups)

selected_groups = [doc.GetElement(f.GroupId).Id.IntegerValue for f in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures).WhereElementIsNotElementType() if f.Name == selected_name and f.GroupId.IntegerValue != -1]

# Get areas by apartment number that are in the same group(s) as the selected fixture
apartment_areas = list_areas_by_apartment_number(doc, selected_name, selected_groups)

# Sort the apartment_areas dictionary by the first two characters of the apartment number
sorted_apartment_numbers = sorted(apartment_areas.items(), key=lambda x: x[0][:8])
# For displaying the result, adjust according to your needs. Example:
#for apartment_number, groups in apartment_areas.items():
for apartment_number, groups in sorted_apartment_numbers:
    print("Apartment Number:", apartment_number,"Groups:",groups)

# Optional: Display results to the user
#TaskDialog.Show("Selected Fixture Groups", "Fixture:", selected_name, "nGroups:", groups)

# Commit transaction (if started)
# t.Commit()