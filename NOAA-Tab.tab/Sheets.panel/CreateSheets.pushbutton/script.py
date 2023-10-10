__title__="CreateSheets"
__author__="Bogdan Popa"
__doc__="""Sheet Number = XX-XXX
Sheet Name = ABC - Level 00"""

import clr
from pyrevit import forms
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Transaction, ElementId

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document

#def pick_title_block():
#    collector = FilteredElementCollector(doc)
#    collector.OfCategory(BuiltInCategory.OST_TitleBlocks)
#    title_blocks = {str(tb.Id): tb.Id for tb in collector.ToElements()}
#    return forms.SelectFromList.show(title_blocks.keys(), multiselect=False)

#def pick_title_block():
#    collector = FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_TitleBlocks)
#    title_blocks = {str(tb.Id): tb.Id for tb in collector.ToElements()}
#    return forms.SelectFromList.show(title_blocks.keys(), multiselect=False)

#def pick_title_block():
#    collector = FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_TitleBlocks)
#    title_blocks = {tb.FamilyName: str(tb.Id) for tb in collector.ToElements()}
#    return forms.SelectFromList.show(title_blocks.values(), multiselect=False)
    
#def pick_title_block():
#    collector = FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_TitleBlocks)
#    title_blocks = {str(tb.Id): tb.FamilyName for tb in collector.ToElements()}
#    selected = forms.SelectFromList.show(title_blocks.values(), multiselect=False)
#    if not selected:
#        print("No title block selected.")
#        return None
#    selected_value = None
#    for key, value in title_blocks.items():
#    #    print(key,value)
#        selected_value = key
#        break
#    #print (selected_value)
#    return selected_value      

def pick_title_block():
    collector = FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_TitleBlocks)
    title_blocks = {tb.FamilyName: tb.Id for tb in collector.ToElements()}
    selected = forms.SelectFromList.show(title_blocks.keys(), multiselect=False)
    if not selected:
        print("No title block selected.")
        return None
    return title_blocks[selected]       #THIS RETURNS ELEMENTID

def prompt_for_starting_info():
    number = forms.ask_for_string("Enter starting sheet number:")
    name = forms.ask_for_string("Enter starting sheet name:")
    number_of_sheets = int(forms.ask_for_string ("Enter the number of sheets to create:"))
    return number, name, number_of_sheets

def increment_name(name):
    # Extract the last three characters
    last_two = name[-2:]

    # If these can be interpreted as a number, increment it
    if last_two.isdigit():
        number = int(last_two)
        number += 1
        # Replace the last three characters with the new number
        name = name[:-2] + str(number).zfill(2)
    else:
        name = name + "01"
    
    return name

def check_duplicate_sheet(sheet_number, sheet_name):
    collector = FilteredElementCollector(doc).OfClass(ViewSheet)
    for sheet in collector:
        if sheet.SheetNumber == sheet_number or (sheet.SheetNumber == sheet_number and sheet.Name == sheet_name):
            return True
    return False

def increment_number(number_str):
    try:
        if "-" in number_str:
            prefix, number = number_str.rsplit("-", 1)
            return "{}-{:0{}}".format(prefix, int(number) + 1, len(number))
        else:
            return str(int(number_str) + 1)
    except ValueError:
        print("Failed to increment number: {}".format(number_str))
        return number_str

def create_sheets(start_number, start_name, title_block, number_of_sheets):
    number = start_number
    name = start_name

    t = Transaction(doc, 'Create Sheets')
    t.Start()

    for i in range(number_of_sheets):
        if check_duplicate_sheet(number, name):
            print("Sheet with number: {} or name: {} already exists.".format(number, name))
            break
        try:
            sheet = ViewSheet.Create(doc, title_block)
            sheet.SheetNumber = number
            sheet.Name = name
            number = increment_number(number)
            name = increment_name(name)
        except Exception as e:
            print("Failed to create sheet. Number: {} Name: {}. Error: {}".format(number, name, str(e)))

    t.Commit()


if __name__ == "__main__":
    title_block_id = pick_title_block()
    start_number, start_name, number_of_sheets = prompt_for_starting_info()
    if title_block_id and start_number and start_name:
        #title_block_id = ElementId(int(title_block_id))
        create_sheets(start_number, start_name, title_block_id, number_of_sheets)
    else:
        print("Failed to gather necessary data. Aborting...")











