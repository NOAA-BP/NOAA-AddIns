__title__="ApplyTitleblock"
__author__="Bogdan Popa"
__doc__="""Applies chosen title block from all availabele titleblocks, on multiple sheets"""

# Import necessary modules
import System
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ViewSheet
from Autodesk.Revit.UI import TaskDialog
from pyrevit import forms
from pyrevit import revit, DB

# Get the active Revit application and document
doc = __revit__.ActiveUIDocument.Document

# Prompt the user to select sheets
sheets_to_modify = forms.select_sheets(title='Select Sheets to Modify Title Block')

# Collect all Title Blocks in the document
collector = FilteredElementCollector(doc).OfClass(DB.FamilySymbol).OfCategory(BuiltInCategory.OST_TitleBlocks)
title_blocks = {tb.FamilyName: tb.Id for tb in collector.ToElements()}

# Prompt the user to select a title block
selected_title_block_name = forms.SelectFromList.show(title_blocks.keys(), title='Select a Title Block')
if not selected_title_block_name:
    print("No title block selected.")
else:
    selected_title_block_id = title_blocks[selected_title_block_name]

# Make sure the user has selected at least one sheet and one title block
if not sheets_to_modify or not selected_title_block_name:
    TaskDialog.Show("Error", "Please select at least one sheet and one title block.")
else:
    with revit.Transaction("Apply Title Block to Sheets"):
        for sheet in sheets_to_modify:
            # Get the existing title block on the sheet (if any)
            old_title_blocks = FilteredElementCollector(doc, sheet.Id).OfCategory(BuiltInCategory.OST_TitleBlocks).ToElements()
            
            # Change the FamilySymbol of the existing title block to the new selected one
            for old_title_block in old_title_blocks:
                old_title_block.Symbol = doc.GetElement(selected_title_block_id)

    TaskDialog.Show("Success", "Selected title block has been applied to the sheets.")













