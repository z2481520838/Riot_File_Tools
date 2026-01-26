from io import BytesIO
from .animation_file import*

def read_anm_file(path):
    magic = read_str(path, 8)
    version = read_uint32(path)
    anm_data = None
    if magic ==  "r3d2canm":
        resourceSize = read_uint32(path)
        formatToken = read_str(path, 4)
        flags = read_uint32(path)
        jointCount = read_int32(path)
        frameCount = read_int32(path)
        jumpCacheCount = read_int32(path)
        duration = read_float(path)
        FrameDuration = read_float(path)
        translationMin = read_vector3(path)
        translationMax = read_vector3(path)
        scaleMin = read_vector3(path)
        scaleMax = read_vector3(path)
        anm_data = AnimationFile_Compressed(resourceSize, formatToken, flags, jointCount, frameCount, jumpCacheCount, duration, FrameDuration, translationMin, translationMax, scaleMin, scaleMax)
    else:
        if version == 3:
            skeletonId = read_uint32(path)
            trackCount = read_int32(path)
            frameCount = read_int32(path)
            frameDuration = read_int32(path)
            anm_data = AnimationFile_(skeletonId, trackCount, frameCount, frameDuration)
        elif version == 4:
            resourceSize = read_uint32(path)
            formatToken = read_uint32(path)
            version_s = read_uint32(path)
            flags = read_uint32(path)
            trackCount = read_int32(path)
            frameCount = read_int32(path)
            FrameDuration = read_float(path)
            anm_data = AnimationFile_V4(resourceSize, formatToken, version_s, flags, trackCount, frameCount, FrameDuration)
        elif version == 5:
            resourceSize = read_uint32(path)
            formatToken = read_uint32(path)
            version_s = read_uint32(path)
            flags = read_uint32(path)
            trackCount = read_int32(path)
            framesPerTrack = read_int32(path)
            FrameDuration = read_float(path)
            anm_data = AnimationFile_V5(resourceSize, formatToken, version_s, flags, trackCount, framesPerTrack, FrameDuration)
        else:
            anm_data = None

    anm_header = AnmHeader(magic, version)
    anm_file = AnimationFile(anm_header,anm_data)
    return anm_file