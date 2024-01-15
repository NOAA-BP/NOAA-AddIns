__title__="TagRooms(On Sheets)"
__author__  = "Bogdan Popa"
__version__ = "Version 1.0"
__doc__ = """It tags rooms on every sheet and centers tags to Rooms"""

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import LinkElementId
from pyrevit import forms
from System import Guid

doc = __revit__.ActiveUIDocument.Document


#========================================================================================
# STEP 0 - FUNCTIONS TO TAG ROOMS
#========================================================================================
def collect_sheets(doc):
    all_sheets = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()
    selected_sheets = forms.SelectFromList.show([s.SheetNumber + " - " + s.Name for s in all_sheets], title='Select Sheets', multiselect=True)
    return [s for s in all_sheets if s.SheetNumber + " - " + s.Name in selected_sheets]

def select_room_tag(doc):
    collector = FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_RoomTags)
    room_tags = {tag.FamilyName: tag for tag in collector}
    if not room_tags:
        print("No Room Tags found in the document.")
        return None
    selected_tag_name = forms.SelectFromList.show(sorted(room_tags.keys()), title='Select Room Tag Type')
    return room_tags[selected_tag_name] if selected_tag_name else None

def tag_all_rooms(doc, sheets, room_tag_type):
    for sheet in sheets:
        view_ids = sheet.GetAllPlacedViews()
        for view_id in view_ids:
            view = doc.GetElement(view_id)
            if isinstance(view, ViewPlan):
                place_room_tags(doc, view, room_tag_type)

def place_room_tags(doc, view, room_tag_type):
    with Transaction(doc, "Place Room Tags") as t:
        t.Start()

        rooms = FilteredElementCollector(doc, view.Id).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType().ToElements()
        for room in rooms:
            # Check if the room already has a tag in this view
            if not any(tag.Room.Id == room.Id for tag in FilteredElementCollector(doc, view.Id).OfClass(IndependentTag).ToElements()):
                room_location = room.Location
                if room_location and isinstance(room_location, LocationPoint):
                    # Use the room's location point as the tag location
                    location_point = room_location.Point
                    tag_point = UV(location_point.X, location_point.Y)

                    roomId = LinkElementId(room.Id)
                    # Create a new room tag at the room's location
                    try:
                        roomTag = doc.Create.NewRoomTag(roomId, tag_point, view.Id)
                        if roomTag is None:
                            raise Exception("Create a new room tag failed.")
                    except Exception as e:
                        print("Error creating room tag for room {}: {}".format(room.Id, e))

        t.Commit()

#========================================================================================
# STEP 1 - FUNCTIONS TO MOVE TAGS
#========================================================================================

def move_room_and_tag(tag, room, new_pt):
    """Function to move both Room and Tag Locations, if they are not part of the group.
    :param tag:     Room Tag
    :param room:    Room
    :param new_pt:  XYZ Point."""
    if room.GroupId == ElementId(-1): #ElementId(-1) means None
        room.Location.Point = new_pt

    if tag.GroupId == ElementId(-1):
        tag.Location.Point = new_pt

def align_tags(doc, view):
    print("Aligning Tags in View:{}".format(view.Id))
    # ELEMENTS
    all_room_tags = FilteredElementCollector(doc, view.Id)\
        .OfCategory(BuiltInCategory.OST_RoomTags).WhereElementIsNotElementType().ToElements()
    with Transaction(doc, __title__) as t:
        t.Start()

        for tag in all_room_tags:
            # ROOM DATA
            room = tag.Room
            room_bb = room.get_BoundingBox(view)
            room_center = (room_bb.Min + room_bb.Max) / 2

            # MOVE TO CENTER (if possible)
            if room.IsPointInRoom(room_center):
                move_room_and_tag(tag, room, room_center)

            # FIND ANOTHER LOCATION
            else:
                room_boundaries = room.GetBoundarySegments(SpatialElementBoundaryOptions())
                if len(room_boundaries) > 0:  # Check if there are boundaries
                    room_segments = room_boundaries[0]

                    # Get Longest Segment
                    length = 0
                    longest_curve = None

                    for seg in room_segments:
                        curve = seg.GetCurve()
                        if curve.Length > length:
                            longest_curve = curve
                            length = curve.Length

                    # Get middle point on Curve
                    pt_start = longest_curve.GetEndPoint(0)
                    pt_end = longest_curve.GetEndPoint(1)
                    pt_mid = (pt_start + pt_end) / 2

                    pt_up = XYZ(pt_mid.X, pt_mid.Y + step, pt_mid.Z)
                    pt_down = XYZ(pt_mid.X, pt_mid.Y - step, pt_mid.Z)
                    pt_right = XYZ(pt_mid.X + step, pt_mid.Y, pt_mid.Z)
                    pt_left = XYZ(pt_mid.X - step, pt_mid.Y, pt_mid.Z)

                    # Move on X Axis
                    if not (room.IsPointInRoom(pt_up) and room.IsPointInRoom(pt_down)):
                        if room.IsPointInRoom(pt_up):
                            move_room_and_tag(tag, room, pt_up)

                        elif room.IsPointInRoom(pt_down):
                            move_room_and_tag(tag, room, pt_down)

                    # Move on Y Axis
                    elif not (room.IsPointInRoom(pt_right) and room.IsPointInRoom(pt_left)):
                        if room.IsPointInRoom(pt_right):
                            move_room_and_tag(tag, room, pt_right)

                        elif room.IsPointInRoom(pt_left):
                            move_room_and_tag(tag, room, pt_left)

        t.Commit()



#========================================================================================
# STEP 2 - EXECUTION
#========================================================================================

# CONTROLS
step = 2 # INTERNAL UNITS IN FEET



if __name__ == "__main__":
    sheets = collect_sheets(doc)
    if sheets:
        room_tag_type = select_room_tag(doc)
        if room_tag_type:
            for sheet in sheets:
                view_ids = sheet.GetAllPlacedViews()
                for view_id in view_ids:
                    view = doc.GetElement(view_id)
                    if isinstance(view, ViewPlan):
                        tag_all_rooms(doc, [sheet], room_tag_type)  # Pass the current sheet as a list to tag_all_rooms
                        align_tags(doc, view)  # Pass the current view to align_tags
        else:
            print("No Room Tag type selected.")
    else:
        print("No sheets selected.")






























