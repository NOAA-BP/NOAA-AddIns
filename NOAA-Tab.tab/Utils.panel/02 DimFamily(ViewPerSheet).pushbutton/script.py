__title__="02.1 Dim Family"
__author__="Bogdan Popa"
__doc__="""Just pick already.."""

import clr
import System.Collections.Generic
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit import DB
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType
from Autodesk.Revit.UI import TaskDialog
from System.Collections.Generic import List
from pyrevit import forms
from System.Windows.Forms import Form, Label, ComboBox, Button, DialogResult, ComboBoxStyle
from System.Drawing import Size, Point
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, FamilySymbol, FamilyInstanceReferenceType


uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

# Function to prompt user for sheet selection
def select_sheets():
    # Prompt the user to select sheets
    selected_sheets = forms.select_sheets(title='Select Sheets to Modify Title Block')
    # If user cancels selection, end script
    if not selected_sheets:
        forms.alert('No sheets selected. Exiting.', exitscript=True)
    # Return the list of selected sheet elements
    return selected_sheets

def select_family_type():
    # Collect all family types
    collector = FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_Furniture)
    family_types = collector.ToElements()

    # Create a dictionary of family names to FamilySymbol objects
    family_type_dict = {ft.Family.Name: ft for ft in family_types}

    # Prompt the user to select the family type
    selected_family_type_name = forms.SelectFromList.show(family_type_dict.keys(), title='Select a Family Type')
    if not selected_family_type_name:
        print("No family type selected.")
        return None

    # Return the selected FamilySymbol object
    return family_type_dict.get(selected_family_type_name, None)

# Function to get sub-elements of a family instance
def get_sub_elements(family_instance):
    sub_elements = []
    sub_element_ids = family_instance.GetSubComponentIds()

    if sub_element_ids:
        for sub_element_id in sub_element_ids:
            sub_element = doc.GetElement(sub_element_id)
            if isinstance(sub_element, FamilyInstance):
                sub_elements.append(sub_element)

    return sub_elements

def get_dimension_line_from_sub_elements(family_instance, subcategory_name):
    options = Options()
    options.ComputeReferences = True  # Ensure that references are computed
    options.IncludeNonVisibleObjects = True  # Include geometry that might not be visible in views
    options.DetailLevel = ViewDetailLevel.Fine  # Use the finest detail level to get all lines

    geom_element = family_instance.get_Geometry(options)
    
    for geom_object in geom_element:
        if isinstance(geom_object, GeometryInstance):
            symbol_geom = geom_object.GetInstanceGeometry()
            for symbol_obj in symbol_geom:
                # Check if the symbol_obj is a line and belongs to the subcategory
                if isinstance(symbol_obj, Line) and symbol_obj.GraphicsStyleId != ElementId.InvalidElementId:
                    print("LINE FOUND")
                    graphics_style = doc.GetElement(symbol_obj.GraphicsStyleId)
                    if graphics_style.GraphicsStyleCategory.Name == subcategory_name:
                        print("Line of Subcategory {} found:{}".format(subcategory_name, symbol_obj.Id))
                        return symbol_obj  # Found a line with the specified subcategory

    return None  # If no line is found, return None 



# Function to place dimension in view
def place_dimension(view, family_instance, reference_type, line, dim_type):
    if line is None:
        print("No line found for dimensioning.")
        return None
    with Transaction(doc, "Place Dimension") as t:
        t.Start()
        try:
            # Get references from family instance
            references = family_instance.GetReferences(reference_type)
            print("References array: type{}, number {}".format(type(references),len(references)))
            ref_array = ReferenceArray()
            for ref in references:
                print("reference {} is of type:{}".format(ref,type(ref)))
                if isinstance(ref,Reference):
                    ref_array.Append(ref)
            # Create dimension
            dimension = doc.Create.NewDimension(view, line, ref_array)
            if dimension:
                    # Set the dimension type
                    dimension.DimensionType = dim_type
            t.Commit()
            return dimension
        except Exception as e:
            TaskDialog.Show('Error', 'Failed to create dimension: {0}'.format(e))
            t.RollBack()
            return None

def get_all_dimension_types(doc):
    """Retrieve all dimension types in the document."""
    collector = FilteredElementCollector(doc)
    return collector.OfClass(DimensionType)

def select_dimension_type(doc):
    """Prompt the user to select a dimension type."""
    dimension_types_collector = FilteredElementCollector(doc).OfClass(DimensionType)
    dimension_types = list(dimension_types_collector)

    # Debug: print number of dimension types found
    print("Number of dimension types found: {}".format(len(dimension_types)))

    # Filter out any items that might not have a 'Name' property and create a dictionary
    dimension_type_names = {}
    for dt in dimension_types:
        try:
            name_param = dt.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
            if name_param and name_param.HasValue:
                name = name_param.AsString()
                dimension_type_names[name] = dt
            else:
                print("Found a dimension type without a name.")
        except Exception as e:
            print("Error accessing Name property: {}".format(e))

    # Debug: print dimension type names
    print("Dimension Type Names: {}".format(list(dimension_type_names.keys())))

    # Ensure there are dimension types to choose from
    if not dimension_type_names:
        print('No valid dimension types found.')
        forms.alert('No valid dimension types found.', exitscript=True)

    # Show selection form
    selected_name = forms.SelectFromList.show(sorted(dimension_type_names.keys()), 
                                              button_name='Select',
                                              title='Select Dimension Type')

    if selected_name is None:
        print('No dimension type selected.')
        return None

    return dimension_type_names[selected_name]


# Main script
sheets = select_sheets()
print("Sheets slected:{}".format(sheets))
#selected_family_type = select_family_type()
#if selected_family_type:
#    print("Selected Family Type: {0}".format(selected_family_type.Family.Name))
#else:
#    print("No family type selected.")

reference_type = FamilyInstanceReferenceType.StrongReference  # or another appropriate reference type
referece_type_dim = FamilyInstanceReferenceType.WeakReference

print("References collected {}, dim holder:{}".format(reference_type, referece_type_dim))

# Prompt the user to select a dimension type
selected_dimension_type = select_dimension_type(doc)
if selected_dimension_type is None:
    forms.alert('No dimension type selected.', exitscript=True)

for sheet in sheets:
    print("Processing sheet:{}".format(sheet.Name))
    # Get the view from the sheet
    sheet_id = sheet.Id
    sheet = doc.GetElement(sheet_id)
    print("View name:{}".format(sheet.Name))
    
    # Find family instances in view
    #collector = FilteredElementCollector(doc, view_id).OfClass(FamilyInstance).OfCategory(BuiltInCategory.OST_Furniture).ToElements()
    
    # Get all viewports on the sheet
    viewports = FilteredElementCollector(doc, sheet.Id).OfClass(Viewport).ToElements()
    print("Nuber of viewports:{}".format(len(viewports)))
    
    for viewport in viewports:
        # Get the view associated with each viewport
        view_id = viewport.ViewId
        view = doc.GetElement(view_id)
        
        # Check if view is not None and perform operations on the view
        if view:
            print("Processing view: {0}".format(view.Name))
            collector = FilteredElementCollector(doc, view_id).OfClass(FamilyInstance).OfCategory(BuiltInCategory.OST_Furniture).ToElements()
            print("Collected elements in view:{}".format(collector))
            for element in collector:
                print("Element being processed:{}, of type{}, under name {}".format(element.Id, type(element), element.Name), "Against selected family name:{}".format(selected_family_type.Family.Name))
                if element.Name == "PV-WT-01" or element.Name == "72-WARDROBE TYPE 1 (1800)" or element.Name == "PV-WT-02" or element.Name == "72-WARDROBE TYPE 2 (1500)" or element.Name == "PV-WT-03" or element.Name == "72-WARDROBE TYPE 3 (1200)":
                    print("Attempting to place dimension for element: {0}".format(element.Id))
                    # Assuming you have a FamilyInstance element called 'family_instance' and a subcategory name 'MySubcategoryLine'
                    line = get_dimension_line_from_sub_elements(element, '<Invisible lines>')
                    print("Collected line:{}".format(line))
                    if line:
                        dimension = place_dimension(view, element, reference_type, line, selected_dimension_type)
                        if dimension:
                            # Set the dimension type
                            #dimension.DimensionType = selected_dimension_type
                            print("Dimension placed for family instance ID: {0}".format(element.Id))
                    else:
                         print("No line available for dimensioning.")
        else:
            print("No view associated with viewport ID: {0}".format(viewport.Id))

