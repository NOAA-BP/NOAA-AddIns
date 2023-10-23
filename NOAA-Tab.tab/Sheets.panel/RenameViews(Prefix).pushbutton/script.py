__title__="RenameViews(Prefix)"
__author__="Bogdan Popa"
__doc__="""Sheet Number = XX-XXX
Sheet Name = ABC - Level 00"""

from Autodesk.Revit.DB import FilteredElementCollector, View
from Autodesk.Revit.UI import TaskDialog
from pyrevit import forms
from pyrevit import revit, DB

# Get the active Revit application and document
doc = __revit__.ActiveUIDocument.Document

# Get all the views in the document
all_views = FilteredElementCollector(doc).OfClass(View).ToElements()

# Filter out views that shouldn't be renamed like "<Project View>" etc.
all_views = [v for v in all_views if not v.IsTemplate and v.Name != "<Project View>"]

# Prompt the user to select views
views_to_modify = forms.select_views(title='Select Views to Modify', multiple=True)

# Prompt the user for the new prefix
view_prefix = forms.ask_for_string(default="",
                                   prompt="Enter prefix for view names:",
                                   title="Prefix for View Names")

# Make sure the user has selected at least one view and entered the prefix
if not views_to_modify or not view_prefix:
    TaskDialog.Show("Error", "Please select at least one view and enter the prefix.")
else:
    with revit.Transaction("Modify View Names"):
        for view in views_to_modify:
            # Modify the view name by adding the user-provided prefix
            original_view_name = view.Name
            new_view_name = "{}{}".format(view_prefix, original_view_name)
            view.Name = new_view_name

    TaskDialog.Show("Success", "View names have been modified.")












