import logging
import netifaces
import socket
from io import BytesIO

import requests
from PIL import Image

from cvShapeHandler.imgprocess import ImgProcess


class Request:
    
    def __init__(self, url):
        self.url = url
        mac = netifaces.ifaddresses('eth0')[netifaces.AF_LINK]
        self.mac = mac[0].get('addr')
        self.logger = logging.getLogger(__name__)

    # http://docs.python-requests.org/en/latest/user/advanced/#post-multiple-multipart-encoded-files
    async def upload_data(self, multiple_files, backdrop, timestamp):
        if len(multiple_files) > 0:
            if not self.check_connectivity():
                self.logger.debug("Internet may be down...caching all images just in case for later.")
                # backdrop.cache(multiple_files)
                return

            try:
                data = [('mac', self.mac), ('timestamp', timestamp)]
                tmp_img = []
                for nparray in multiple_files:
                    nparray = ImgProcess.compress(nparray)
                    if nparray is not None:
                        image = Image.fromarray(nparray)
                        tmp = BytesIO()
                        image.save(tmp, "JPEG")
                        tmp.seek(0)
                        data.append(('images', tmp))
                        tmp_img.append(tmp)

                self.logger.info("Trying image upload...")
                return self.post(data)
            except Exception as e:
                self.logger.error("Error uploading image: %s", e)
        return

    def post(self, data):
        try:
            self.logger.info("Posting data...")
            r = requests.post(self.url, files=data)
            self.logger.info("Server response: %s", r.text)
            print(r.text)
            print('Upload complete')
            return True
        except Exception as e:
            self.logger.error("Error on post: %s", e)
            return False

    def check_connectivity(self):
        try:
            conn = socket.create_connection(('google.com', 8080))
            conn.close()
            return True
        except Exception as e:
            pass

        return False

