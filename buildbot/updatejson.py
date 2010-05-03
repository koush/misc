import re
import shutil
import simplejson
import sys
import os
import zipfile

class AndroidBuild:
    def __init__(self, filename):
        self.filename = filename
        self.buildprop = {}
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
        bd = re.match(r"^CyanogenMod-5-(\d{8})-NIGHTLY-\w*$", self.getModVersion())
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

        shouldAdd = True
        d = self.getDevice().split("_")
        for device in d:
            for build in oldJSON[device]:
                if build['date'] == newEntry['date']:
                    shouldAdd = False

            if (shouldAdd): oldJSON[device].insert(0, newEntry)
        return simplejson.dumps(oldJSON)

    def dumpRMJSON(self, oldJSON):
        oldJSON = simplejson.loads(oldJSON)
        d = self.getDevice().split("_")
        shouldAdd = True
        modversion = self.getModVersion()

        for device in d:
            for rom in oldJSON['roms']:
                if rom['modversion'] == modversion:
                    shouldAdd = False
            if shouldAdd:
                newEntry = {
                    "name": modversion,
                    "modversion": modversion,
                    "summary": "Experimental",
                    "incremental": self.getBuildDate(),
                    "product": "CyanogenModNightly",
                    "device": device,
                    "addons": [{
                        "name": "Google Apps",
                        "urls": ["http://koush.romraid.com//common/gapps-passion-EPE54B-signed.zip", "http://www.droidaftermarket.com/koush//common/gapps-passion-EPE54B-signed.zip", "http://droidk.macleodweb.net//common/gapps-passion-EPE54B-signed.zip", "http://android.antbox.org/koush//common/gapps-passion-EPE54B-signed.zip", "http://www.thekilpatrickproject.com/downloads/koush//common/gapps-passion-EPE54B-signed.zip", "http://briancrook.ca/android/nexus/gapps/gapps-passion-EPE54B-signed.zip"]
                    }],
                    "urls": [ "http://buildbot.teamdouche.net/nightly/%s" % self.getFilename() ]
                }
                oldJSON['roms'].insert(0, newEntry)

        return simplejson.dumps(oldJSON)

    def moveFile(self, destinationdir):
        fullPath = destinationdir + "/" + self.getFilename()
        shutil.move(self.filename, fullPath)
        os.chmod(fullPath, 0644)

def main():
    if len(sys.argv) == 1:
        print "Usage: %s <filename>" % sys.argv[0]
        sys.exit(1)
    else:
        fn = sys.argv[1]
        oldJSON = open("nightly.js").read()

        ab = AndroidBuild(fn)
        ab.moveFile("/home/buildbot/nightly/")
        
        f = open("nightly.js", "w")
        f.write(ab.dumpJSON(oldJSON))
        f.close()
        
        oldJSON = open("rmnightly.js").read()
        #print ab.dumpRMJSON(oldJSON)
        f = open("rmnightly.js", "w")
        f.write(ab.dumpRMJSON(oldJSON))
        f.close()

if __name__ == "__main__":
     main()
