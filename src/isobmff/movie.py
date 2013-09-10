
import sys
import box

class MovieHeader(box.FullBox):
    def __init__(self, buf, parent=None):
        self.parent = parent
        self.parse(buf)

    def parse(self, buf):
        super(MovieHeader, self).parse(buf)
        if self.version == 1:
            self.creation_time = buf.readint64()
            self.modification_time = buf.readint64()
            self.timescale = buf.readint32()
            self.duration = buf.readint64()
        else:
            self.creation_time = buf.readint32()
            self.modification_time = buf.readint32()
            self.timescale = buf.readint32()
            self.duration = buf.readint32()
        self.rate = buf.readint32()
        self.volume = buf.readint16()
        buf.skipbytes(2 + 8)
        self.matrix = []
        for i in range(3):
            self.matrix.append([buf.readint32() for j in range(3)])
        buf.skipbytes(24)
        self.next_track_id = buf.readint32()

    def generate_fields(self):
        super(MovieHeader, self).generate_fields()
        from utils import get_utc_from_seconds_since_1904
        yield ("creation time", self.creation_time, get_utc_from_seconds_since_1904(self.creation_time).ctime())
        yield ("modification time", self.creation_time, get_utc_from_seconds_since_1904(self.modification_time).ctime())
        yield ("timescale", self.timescale)
        yield ("duration", self.duration)
        yield ("rate", "0x%08X" %(self.rate))
        yield ("volume", "0x%04X" %(self.volume))
        yield ("matrix", self.matrix)
        yield ("next track id", self.next_track_id)


class TrackHeader(box.FullBox):
    def __init__(self, buf, parent=None):
        self.parent = parent
        self.parse(buf)

    def parse(self, buf):
        super(TrackHeader, self).parse(buf)
        if self.version == 1:
            self.creation_time = buf.readint64()
            self.modification_time = buf.readint64()
            self.track_id = buf.readint32()
            buf.skipbytes(4)
            self.duration = buf.readint64()
        else:
            self.creation_time = buf.readint32()
            self.modification_time = buf.readint32()
            self.track_id = buf.readint32()
            buf.skipbytes(4)
            self.duration = buf.readint32()
        buf.skipbytes(8)
        self.layer = buf.readint16()
        self.altgroup = buf.readint16()
        self.volume = buf.readint16()
        buf.skipbytes(2)
        self.matrix = []
        for i in range(3):
            self.matrix.append([buf.readint32() for j in range(3)])
        self.width = buf.readint32()
        self.height = buf.readint32()

    def generate_fields(self):
        super(TrackHeader, self).generate_fields()
        from utils import get_utc_from_seconds_since_1904
        yield ("creation time", self.creation_time, get_utc_from_seconds_since_1904(self.creation_time).ctime())
        yield ("modification time", self.modification_time, get_utc_from_seconds_since_1904(self.modification_time).ctime())
        yield ("track id", self.track_id)
        yield ("duration", self.duration)
        yield ("layer", "0x%04X" %(self.layer))
        yield ("alternate group", "0x%04X" %(self.altgroup))
        yield ("volume", "0x%04X" %(self.volume))
        yield ("matrix", self.matrix)
        yield ("width", self.width)
        yield ("height", self.height)


class MediaHeader(box.FullBox):
    def __init__(self, buf, parent=None):
        self.parent = parent
        self.parse(buf)

    def parse(self, buf):
        super(MediaHeader, self).parse(buf)
        if self.version == 1:
            self.creation_time = buf.readint64()
            self.modification_time = buf.readint64()
            self.timescale = buf.readint32()
            self.duration = buf.readint64()
        else:
            self.creation_time = buf.readint32()
            self.modification_time = buf.readint32()
            self.timescale = buf.readint32()
            self.duration = buf.readint32()
        self.language = buf.readint16() & 0x7FFF
        buf.skipbytes(2)

    def generate_fields(self):
        from utils import parse_iso639_2_15bit
        from utils import get_utc_from_seconds_since_1904
        super(MediaHeader, self).generate_fields()
        yield ("creation time", self.creation_time, get_utc_from_seconds_since_1904(self.creation_time).ctime())
        yield ("modification time", self.modification_time, get_utc_from_seconds_since_1904(self.modification_time).ctime())
        yield ("timescale", self.timescale)
        yield ("duration", self.duration)
        yield ("language", self.language, parse_iso639_2_15bit(self.language))


class HandlerBox(box.FullBox):
    def __init__(self, buf, parent=None):
        self.parent = parent
        self.parse(buf)

    def parse(self, buf):
        super(HandlerBox, self).parse(buf)
        buf.skipbytes(4)
        self.handler = buf.readstr(4)
        buf.skipbytes(12)
        self.consumed_bytes += 20
        remaining = self.size - self.consumed_bytes
        name = ''
        for i in range(remaining):
            c = buf.readbyte()
            if not c:
                break
            name += chr(c)
        self.name = name

    def generate_fields(self):
        super(HandlerBox, self).generate_fields()
        yield ("handler", self.handler)
        yield ("name", self.name if len(self.name) else '<empty>')


class SampleEntry(box.Box):
    def __init__(self, buf, parent=None):
        self.parent = parent
        self.parse(buf)

    def parse(self, buf):
        super(SampleEntry, self).parse(buf)
        buf.skipbytes(6)
        self.data_ref_index = buf.readint16()
        self.consumed_bytes += 8

    def generate_fields(self):
        super(SampleEntry, self).generate_fields()
        yield ("data reference index", self.data_ref_index)


class HintSampleEntry(SampleEntry):
    def __init__(self, buf, parent=None):
        self.parent = parent
        self.parse(buf)
        buf.skipbytes(self.size - self.consumed_bytes)


class VisualSampleEntry(SampleEntry):
    def __init__(self, buf, parent=None):
        self.parent = parent
        self.parse(buf)

    def parse(self, buf):
        super(VisualSampleEntry, self).parse(buf)
        buf.skipbytes(2 + 2 + 3 * 4)
        self.width = buf.readint16()
        self.height = buf.readint16()
        self.hori_resolution = buf.readint32()
        self.vert_resolution = buf.readint32()
        buf.skipbytes(4)
        self.frame_count = buf.readint16()
        compressor_name_length = buf.readbyte()
        self.compressor_name = buf.readstr(compressor_name_length) if compressor_name_length else ''
        buf.skipbytes(32 - compressor_name_length - 1)
        self.depth = buf.readint16()
        buf.skipbytes(2)

    def generate_fields(self):
        s = super(VisualSampleEntry, self).generate_fields()
        yield ("width", self.width)
        yield ("height", self.height)
        yield ("horizontal resolution", "0x%08X" %(self.hori_resolution))
        yield ("vertical resolution", "0x%08X" %(self.vert_resolution))
        yield ("frame count", self.frame_count)
        yield ("compressor name", self.compressor_name)
        yield ("depth", self.depth)

class AudioSampleEntry(SampleEntry):
    def __init__(self, buf, parent=None):
        self.parent = parent
        self.parse(buf)

    def parse(self, buf):
        super(AudioSampleEntry, self).parse(buf)
        buf.skipbytes(8)
        self.channel_count = buf.readint16()
        self.sample_size = buf.readint16()
        buf.skipbytes(4)
        self.sample_rate = buf.readint32()

    def generate_fields(self):
        super(AudioSampleEntry, self).generate_fields()
        yield ("sample size", self.sample_size)
        yield ("sample rate", self.sample_rate, "%d, %d" %(self.sample_rate >> 16, self.sample_rate & 0xFFFF))


class SampleDescription(box.FullBox):
    def __init__(self, buf, parent=None):
        self.parent = parent
        self.parse(buf)

    def parse(self, buf):
        super(SampleDescription, self).parse(buf)
        media = self.find_parent('mdia')
        hdlr = media.find_child('hdlr') if media else None
        handler = hdlr.handler if hdlr else None
        self.entry_count = buf.readint32()
        self.entries = []
        for i in range(self.entry_count):
            if handler == 'soun':
                entry = AudioSampleEntry(buf)
            elif handler == 'vide':
                entry = VisualSampleEntry(buf)
            elif handler == 'hint':
                entry = HintSampleEntry(buf)
            else:
                entry = box.Box(buf)
                buf.skipbytes(entry.size - entry.consumed_bytes)
            self.entries.append(entry)

    def generate_fields(self):
        super(SampleDescription, self).generate_fields()
        yield ("entry count", self.entry_count)
        for entry in self.entries:
            yield entry
