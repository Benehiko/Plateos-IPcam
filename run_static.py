import pathlib
from multiprocessing import Process, Queue
from os import listdir
from os.path import join, isfile
from threading import Thread

import server
from Handlers.PropertyHandler import PropertyHandler
from Views.Image import Image
from tess.tesseract import Tess

try:
    obj_queue = Queue()
    cv_queue = Queue()
    tess = Tess()
    PropertyHandler.load_app()
    PropertyHandler.load_cv()
    PropertyHandler.load_numberplate()
    pathlib.Path("../plateos-files/images").mkdir(parents=True, exist_ok=True)
    files = [f.replace('.jpg', '') for f in listdir("../plateos-files/images/") if
             isfile(join("../plateos-files/images/", f))]

    print(files)
    p2 = Process(target=server.start, args=(obj_queue, cv_queue))

    pool = []
    for f in files:
        t = Image("../plateos-files/images/" + f + ".jpg", tess=tess, cv_q=cv_queue)
        pool.append(Process(target=t.start))

    for p in pool:
        p.start()

    p2.start()

    for p in pool:
        p.join()
    p2.join()
except Exception as e:
    print(e)
