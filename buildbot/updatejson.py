import re
import simplejson
import zipfile

class AndroidBuild:
    def __init__(self, filename):
        self.filename = filename
        self.buildprop = {}
        
        print "Loading zipfile..."
        self.zip = zipfile.ZipFile(filename, "r")

    def getBuildProp(self, key):
        if self.buildprop == {}:
            f = self.zip.open("system/build.prop").read()

            for line in [x.split("=") for x in f.split("\n")]:
                if len(line) == 2:
                    self.buildprop[line[0]] = line[1]

        return self.buildprop.get(key, None)

    def getModVersion(self):
        return self.getBuildProp("ro.modversion")

    def getDevice(self):
        return self.getBuildProp("ro.product.device")

    def getBuildDate(self):
        bd = re.match(r"^CyanogenMod-(\d{8})-NIGHTLY-\w*$", self.getModVersion())
        if bd is not None:
            return bd.group(1)

    def getFilename(self):
        return "cyanogen_%s-ota-%s.zip" % (self.getDevice(), self.getBuildDate())

    def dumpJSON(self, oldJSON):
        newEntry = {
            "name": self.getModVersion(),
            "date": self.getBuildDate(),
            "url": "http://buildbot.teamdouche.net/nightly/%s" % self.getFilename()
        }

        oldJSON = simplejson.loads(oldJSON)
        oldJSON[self.getDevice()].insert(0, newEntry)
        return simplejson.dumps(oldJSON)

if __name__ == "__main__":
    oldJSON = simplejson.dumps({"passion":[]})

    ab = AndroidBuild("cyanogen_passion-ota-04232010.zip")
    print ab.dumpJSON(oldJSON)
