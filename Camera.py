from Backdrop.Backdrop import Backdrop
from camera.Camera import Camera


cam1 = "192.168.1.104"
cam2 = "192.168.1.108"
username = "admin"
password = "Benehiko123!"

camera = Camera(cam1, username, password)
camera2 = Camera(cam2, username, password)

camera.start()
camera2.start()

#runner1 = Backdrop(camera, camera2)
#runner1.run()



#cv2.destroyAllWindows()