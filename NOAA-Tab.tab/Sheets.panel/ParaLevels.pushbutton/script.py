__title__="InheritLevels"
__author__="Bogdan Popa"
__doc__="""Populates 'Level' parameter based on the level of the View"""

import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Transaction, ViewSheet, ViewPlan
from pyrevit import forms

# Main script
doc = __revit__.ActiveUIDocument.Document

# Get all sheets in the project
all_sheets_collector = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()

# Prompt user to select sheets to modify
selected_sheets = forms.select_sheets(title='Select Sheets to Update Level Parameter')

# If user cancels selection, end script
if not selected_sheets:
    forms.alert('No sheets selected. Exiting.', exitscript=True)

# Start a transaction to modify the document
t = Transaction(doc, "Update Level Parameter on Sheets")
t.Start()

try:
    for sheet in selected_sheets:
        # Collect all plan views on the sheet
        placed_views = [doc.GetElement(view_id) for view_id in sheet.GetAllPlacedViews()]
        plan_views = [view for view in placed_views if isinstance(view, ViewPlan)]

        # Get the level number from the first plan view and format it
        if plan_views:
            level = plan_views[0].GenLevel
            if level:
                level_number = ''.join(c for c in level.Name if c.isdigit())
                formatted_level_number = "{:02d}".format(int(level_number))
                
                # Set the 'Level' parameter on the sheet
                level_param = sheet.LookupParameter('Level')
                if level_param and not level_param.IsReadOnly:
                    level_param.Set(formatted_level_number)
                    print("Updated sheet: {} with Level: {}".format(sheet.SheetNumber, formatted_level_number))
                else:
                    print("Sheet: {} does not have a 'Level' parameter or it is read-only.".format(sheet.SheetNumber))
            else:
                print("No associated level found for the plan view on sheet: {}".format(sheet.SheetNumber))
        else:
            print("No plan view found on sheet: {}".format(sheet.SheetNumber))

    t.Commit()
except Exception as e:
    print(str(e))
    t.RollBack()











