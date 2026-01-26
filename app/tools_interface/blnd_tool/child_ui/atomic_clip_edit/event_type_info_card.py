from ....build import*
from .....core.objects.blnd.data_obj.event_data import (EventData, SoundEventData, ParticleEventData, SubmeshVisibilityEventData,
                                               FadeEventData, JointSnapEventData, EnableLookAtEventData)
from .....core.function.general import get_relative_path, extract_number, elf_lower

class Blnk_Event_Type_Info_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.build()

    def build(self):
        empty_label = QLabel("Empty Event", self)
        self.layout.addWidget(empty_label)
        self.layout.addStretch()

    def create_event_data(self, name, e_type, flags, frame):
        return EventData(mEventTypeId=e_type,mFlags=flags,mFrame=frame,mName=name)

    def clear_text_box(self):
        pass

    def show_event_info(self, data):
        pass

class Sound_Event_Type_Info_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.build()

    def build(self):
        self.sound_event_name_box = create_text_box(self, "SoundName: ", self.layout)
        self.layout.addStretch()

    def create_event_data(self, name, e_type, flags, frame):
        s_name = self.sound_event_name_box.text() or ""
        return SoundEventData(mEventTypeId=e_type,mFlags=flags,mFrame=frame,mName=name,mSoundName=s_name)

    def clear_text_box(self):
        self.sound_event_name_box.clear()

    def show_event_info(self, data):
        self.sound_event_name_box.setText(data.mSoundName)

class Particle_Event_Type_Info_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.build()

    def build(self):
        self.particle_event_effectname_box = create_text_box(self, "EffectName: ", self.layout)
        self.particle_event_bonename_box = create_text_box(self, "BoneName: ", self.layout)
        self.particle_event_taregtbonename_box = create_text_box(self, "TargetBoneName: ", self.layout)
        self.particle_event_endframe_box = create_text_box(self, "EndFrame: ", self.layout)
        self.layout.addStretch()

    def create_event_data(self, name, e_type, flags, frame):
        e_name = self.particle_event_effectname_box.text() or ""
        b_name = self.particle_event_bonename_box.text() or ""
        t_name = self.particle_event_taregtbonename_box.text() or ""
        e_frame = extract_number(self.particle_event_endframe_box.text()) if self.particle_event_endframe_box.text() else 0
        return ParticleEventData(mEventTypeId=e_type,
                                 mFlags=flags,mFrame=frame,
                                 mName=name,
                                 mEndFrame=e_frame,
                                 mEffectName=e_name,
                                 mBoneName=b_name,
                                 mTargetBoneName=t_name)

    def clear_text_box(self):
        self.particle_event_effectname_box.clear()
        self.particle_event_bonename_box.clear()
        self.particle_event_taregtbonename_box.clear()
        self.particle_event_endframe_box.clear()

    def show_event_info(self, data):
        self.particle_event_effectname_box.setText(data.mEffectName)
        self.particle_event_bonename_box.setText(data.mBoneName)
        self.particle_event_taregtbonename_box.setText(data.mTargetBoneName)
        self.particle_event_endframe_box.setText(f"{data.mEndFrame}")

class Submesh_Event_Type_Info_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.build()

    def build(self):
        self.submesh_event_showsubmesh_box = create_text_box(self, "ShowSubmesh: ", self.layout)
        self.submesh_event_hidesubmesh_box = create_text_box(self, "HideSubmesh: ", self.layout)
        self.submesh_event_endframe_box = create_text_box(self, "EndFrame: ", self.layout)
        self.layout.addStretch()

    def create_event_data(self, name, e_type, flags, frame):
        s_hash = elf_lower(self.submesh_event_showsubmesh_box.text()) if self.submesh_event_showsubmesh_box.text() else 0
        h_hash = elf_lower(self.submesh_event_hidesubmesh_box.text()) if self.submesh_event_hidesubmesh_box.text() else 0
        e_frame = extract_number(self.submesh_event_endframe_box.text()) if self.submesh_event_endframe_box.text() else 0
        return SubmeshVisibilityEventData(mEventTypeId=e_type,
                                          mFlags=flags,
                                          mFrame=frame,
                                          mName=name,
                                          mEndFrame=e_frame,
                                          mShowSubmeshHash=s_hash,
                                          mHideSubmeshHash=h_hash)

    def clear_text_box(self):
        self.submesh_event_showsubmesh_box.clear()
        self.submesh_event_hidesubmesh_box.clear()
        self.submesh_event_endframe_box.clear()

    def show_event_info(self, data):
        self.submesh_event_showsubmesh_box.setText(f"{data.mShowSubmeshHash}")
        self.submesh_event_hidesubmesh_box.setText(f"{data.mHideSubmeshHash}")
        self.submesh_event_endframe_box.setText(f"{data.mEndFrame}")

class Fade_Event_Type_Info_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.build()

    def build(self):
        self.fade_event_timetofade_box = create_text_box(self, "TimeToFade: ", self.layout)
        self.fade_event_targetalpha_box = create_text_box(self, "TargetAlpha: ", self.layout)
        self.fade_event_endframe_box = create_text_box(self, "EndFrame: ", self.layout)
        self.layout.addStretch()

    def create_event_data(self, name, e_type, flags, frame):
        t_f = extract_number(self.fade_event_timetofade_box.text()) if self.fade_event_timetofade_box.text() else 0
        t_a = extract_number(self.fade_event_targetalpha_box.text()) if self.fade_event_targetalpha_box.text() else 0
        e_frame = extract_number(self.fade_event_endframe_box.text()) if self.fade_event_endframe_box.text() else 0
        return FadeEventData(mEventTypeId=e_type,
                             mFlags=flags,
                             mFrame=frame,
                             mName=name,
                             mTimeToFade=t_f,
                             mTargetAlpha=t_a,
                             mEndFrame=e_frame)

    def clear_text_box(self):
        self.fade_event_timetofade_box.clear()
        self.fade_event_targetalpha_box.clear()
        self.fade_event_endframe_box.clear()

    def show_event_info(self, data):
        self.fade_event_timetofade_box.setText(f"{data.mTimeToFade}")
        self.fade_event_targetalpha_box.setText(f"{data.mTargetAlpha}")
        self.fade_event_endframe_box.setText(f"{data.mEndFrame}")

class JointSnap_Event_Type_Info_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.build()

    def build(self):
        self.jointsnap_event_jointtooverrideidx_box = create_text_box(self, "JointToOverrideIdx: ", self.layout)
        self.jointsnap_event_jointtosnaptoidx_box = create_text_box(self, "JointToSnapToIdx: ", self.layout)
        self.jointsnap_event_endframe_box = create_text_box(self, "EndFrame: ", self.layout)
        self.layout.addStretch()

    def create_event_data(self, name, e_type, flags, frame):
        j_o = extract_number(self.jointsnap_event_jointtooverrideidx_box.text()) if self.jointsnap_event_jointtooverrideidx_box.text() else 0
        j_s = extract_number(self.jointsnap_event_jointtosnaptoidx_box.text()) if self.jointsnap_event_jointtosnaptoidx_box.text() else 0
        e_frame = extract_number(self.jointsnap_event_endframe_box.text()) if self.jointsnap_event_endframe_box.text() else 0
        return JointSnapEventData(mEventTypeId=e_type,
                                  mFlags=flags,
                                  mFrame=frame,
                                  mName=name,
                                  mEndFrame=e_frame,
                                  mJointToOverrideIdx=j_o,
                                  mJointToSnapToIdx=j_s)

    def clear_text_box(self):
        self.jointsnap_event_jointtooverrideidx_box.clear()
        self.jointsnap_event_jointtosnaptoidx_box.clear()
        self.jointsnap_event_endframe_box.clear()

    def show_event_info(self, data):
        self.jointsnap_event_jointtooverrideidx_box.setText(f"{data.mJointToOverrideIdx}")
        self.jointsnap_event_jointtosnaptoidx_box.setText(f"{data.mJointToSnapToIdx}")
        self.jointsnap_event_endframe_box.setText(f"{data.mEndFrame}")

class EnableLookAt_Event_Type_Info_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.build()

    def build(self):
        self.enablelookat_event_enablelookat_box = create_text_box(self, "EnableLookAt: ", self.layout)
        self.enablelookat_event_lockcurrentvalues_box = create_text_box(self, "LockCurrentValues: ", self.layout)
        self.enablelookat_event_endframe_box = create_text_box(self, "EndFrame: ", self.layout)
        self.layout.addStretch()

    def create_event_data(self, name, e_type, flags, frame):
        e_l = extract_number(self.enablelookat_event_enablelookat_box.text()) if self.enablelookat_event_enablelookat_box.text() else 0
        l_v = extract_number(self.enablelookat_event_lockcurrentvalues_box.text()) if self.enablelookat_event_lockcurrentvalues_box.text() else 0
        e_frame = extract_number(self.enablelookat_event_endframe_box.text()) if self.enablelookat_event_endframe_box.text() else 0
        return EnableLookAtEventData(mEventTypeId=e_type,
                                     mFlags=flags,
                                     mFrame=frame,
                                     mName=name,
                                     mEndFrame=e_frame,
                                     mEnableLookAt=e_l,
                                     mLockCurrentValues=l_v)

    def clear_text_box(self):
        self.enablelookat_event_enablelookat_box.clear()
        self.enablelookat_event_lockcurrentvalues_box.clear()
        self.enablelookat_event_endframe_box.clear()

    def show_event_info(self, data):
        self.enablelookat_event_enablelookat_box.setText(f"{data.mEnableLookAt}")
        self.enablelookat_event_lockcurrentvalues_box.setText(f"{data.mLockCurrentValues}")
        self.enablelookat_event_endframe_box.setText(f"{data.mEndFrame}")
