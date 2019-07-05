
import c4d


def bakeAnim(doc, obj, fstart=0, fend=10):
    """
    Function for Bake Animation use World Matrix for camera or object

    - "doc": Cinema 4D Document.
    - "obj": Object to Bake.
    - "fstart": First frame for baking.
    - "fend": Last frame for baking.

    """
    if obj:
        fps = doc.GetFps()

        #baked_object = c4d.BaseObject(obj.GetType())
        baked_object = obj.GetClone()
        for tag in baked_object.GetTags():
            if tag:
                baked_object.KillTag(tag.GetType())
        baked_object.SetName('{}_baked'.format(obj.GetName()))
        doc.InsertObject(baked_object)

        trans_list = []

        # Get All Basec Transform Paremeters
        for axis_id in range(1000, 1003):
            for orient in [c4d.ID_BASEOBJECT_POSITION, c4d.ID_BASEOBJECT_ROTATION, c4d.ID_BASEOBJECT_SCALE]:
                tr = c4d.CTrack(baked_object, c4d.DescID(c4d.DescLevel(orient, c4d.DTYPE_VECTOR, 0, ), c4d.DescLevel(axis_id, c4d.DTYPE_REAL, 0)))
                baked_object.InsertTrackSorted(tr)
                trans_list.append(tr)
        
        # Check if object is a Camera, if so we need to add more parms to bake
        if obj.GetType() == 5103:
            cam_parms = [c4d.CAMERAOBJECT_TARGETDISTANCE, c4d.CAMERA_FOCUS]
            for parm in cam_parms:
                ctrack_parm = c4d.CTrack(baked_object, parm)
                baked_object.InsertTrackSorted(ctrack_parm)
                trans_list.append(ctrack_parm)

        for frame in range(fstart, fend):
            # Walk through timeline
            doc.SetTime(c4d.BaseTime(float(frame)/fps))
            doc.ExecutePasses(None, True, True, True, 0)
            c4d.GeSyncMessage(c4d.EVMSG_TIMECHANGED)
            CurrTime = c4d.BaseTime(frame,fps)
            
            # Get World Matrix
            obj_mg = obj.GetMg()
            
            for tr in trans_list:                
                # Create Animation Curve
                curve = tr.GetCurve()
                # Set World Matrix to Baked object
                baked_object.SetMg(obj_mg)

                desc_id = tr.GetDescriptionID()
                
                # Get Value to Bake
                if desc_id.GetDepth() > 1:
                    val = baked_object[desc_id[0].id, desc_id[1].id]
                else:
                    val = obj[desc_id[0].id]

                # Set Keyframes
                key = curve.AddKey(CurrTime)['key']
                key.SetValue(curve, val)
        
        return baked_object
    else:
        return None