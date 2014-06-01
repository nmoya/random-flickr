import flickrapi
import urllib
import urllib2
import json
import random
import info  # Simple file with 2 variables. APPKEY and APPSECRET
import os
import glob
import threading

# Documentation: http://stuvel.eu/media/flickrapi-docs/documentation/


class DownloadImage(threading.Thread):
    def __init__(self, id, destination, url):
        threading.Thread.__init__(self)
        self.id = id
        self.url = url
        self.destination = destination

    def run(self):
        save_photo(self.destination, self.url)


def store_photo_url(user_id, photo_id, url_list):
    # https://www.flickr.com/services/oembed?url= \
        # https://www.flickr.com/photos/nmoya/13184707733&format=json
    request_url = "https://www.flickr.com/services/oembed?url="\
        "https://www.flickr.com/photos/%s/%s&format=json" % (user_id, photo_id)
    flicksocket = urllib2.urlopen(request_url)
    reply = flicksocket.read()
    flicksocket.close()
    obj = json.loads(reply)
    url_list.append(obj["url"])


def save_photo(destination, url):
    photo_id = url.split("/")[-1].split("_")[0] + ".jpg"
    urllib.urlretrieve(url, os.path.join(destination + photo_id))


def count_user_photos(flickr_obj, user_id):
    # https://www.flickr.com/services/api/explore/flickr.photos.search
    json = flickr_obj.photos_search(user_id=user_id, format="json")
    return int(json["photos"]["total"])


def load_remote_image_urls(flickr_obj, user_id, total_images):
    url_list = []
    counter = 0
    sets = flickr_obj.photosets_getList(user_id=user_id)
    for pset in sets.find('photosets').findall('photoset'):
        for photo in flickr_obj.walk_set(pset.attrib["id"]):
            store_photo_url(user_id, photo.get('id'), url_list)
            counter += 1
            print "Done: [%d of %d]" % (counter, total_images)
    save_local_image_urls(user_id, url_list)
    return url_list


def save_local_image_urls(user_id, url_list):
    arq = open(user_id+".txt", "w")
    for url in url_list:
        arq.write(url+"\n")
    arq.close()


def load_local_image_urls(flickr_obj, user_id, total_images):
    try:
        arq = open(user_id+".txt")
        content = arq.read()
        content = content.split("\n")
        content = content[:-1]
        arq.close()
    except IOError:
        print "Fetching on flickr. This may take a while..."
        content = load_remote_image_urls(flickr_obj, user_id, total_images)
    return content


def clean_folder(folder):
    if folder[-1] != "/":
        folder = folder + "/"
    files = glob.glob(folder+"*")
    for f in files:
        os.remove(f)


def main():
    user_id = "70997575@N03"  # Find out yours in: http://idgettr.com/
    dynamic_desktop_folder = "/Users/nmoya/Pictures/DynamicDesktop/"
    total_photos = 0
    number_of_photos = 30
    flickr = flickrapi.FlickrAPI(info.APPKEY, format='etree')
    total_photos = count_user_photos(flickr, user_id)

    print "Loading image urls... "
    image_urls = load_local_image_urls(flickr, user_id, total_photos)

    print "Cleaning app folder", dynamic_desktop_folder
    clean_folder(dynamic_desktop_folder)

    print "Shuffling..."
    random.shuffle(image_urls)

    THREADS = []
    print "Downloading to dynamic desktop folder..."
    for i, url in enumerate(image_urls[:number_of_photos]):
        THREADS.append(DownloadImage(i, dynamic_desktop_folder, url))
        THREADS[-1].start()
    print "Downloading [%d of %d]" % (number_of_photos, number_of_photos)

    for i in range(number_of_photos):
        THREADS[i].join()

    print "Done!"
    print "Run: /System/Library/Frameworks/ScreenSaver.framework/Resources/"\
        "ScreenSaverEngine.app/Contents/MacOS/ScreenSaverEngine -background"

main()
