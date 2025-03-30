import numpy as np
import scipy
import cv2
import scipy.spatial


from matplotlib import pyplot as plt

a = 10

def find_class_orient_position(X,Y,T,Template,orientations,objects,choice):

    # Suggested value for choice is 1, which sets it to normalized correlation coefficient
    #kernel1 = np.ones((3,3),np.uint8)
    kernel2 = np.ones((12,12),np.uint8)
    Tmax = np.max(T)
    #Tmin = np.min(T)
    #print Tmax - Tmin
    
    indices = np.where(Tmax-T <1000)[0]
    X = X[indices]
    Y = Y[indices]
    T = T[indices]

    Data = np.zeros((len(X),2))
    Data[:,0] = X
    Data[:,1] = Y

    knn_k = 2
    kdt = scipy.spatial.cKDTree(Data) 
    dists, neighs = kdt.query(Data, knn_k+1)
    avg_dists = np.mean(dists[:, 1:], axis=1)

    #commenting to avoid computation load
    #print(np.mean(avg_dists))

    indices = np.where(avg_dists<4)[0]

    X = X[indices]
    Y = Y[indices]
    T = T[indices]


    methods = ['cv2.TM_CCOEFF', 'cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR',
               'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED']
    meth = eval(methods[choice])

    object_names = ['circle', 'square','triangle']
    Img = np.zeros((76,76))
    for i in range(len(X)):
        Img[6+X[i],6+Y[i]] = 1
    #Img = cv2.morphologyEx(Img, cv2.MORPH_OPEN, kernel1)       
    Img = cv2.morphologyEx(Img, cv2.MORPH_CLOSE, kernel2)
    Img = cv2.morphologyEx(Img, cv2.MORPH_CLOSE, kernel2)

    max_loc = np.zeros((Template.shape[2],2))
    max_val = np.zeros((1,Template.shape[2]))

    for i in range(Template.shape[2]):
        res = cv2.matchTemplate(Img.astype('uint8'), np.squeeze(255*Template[:,:,i]).astype('uint8'), meth)

        min_val, mval, min_loc, mloc = cv2.minMaxLoc(res)
        max_val[0,i] = mval
        max_loc[i,:] = mloc

    max_max = np.argmax(max_val)
    max_location = (max_loc[max_max,0] + (Template.shape[0]/2) - 6, max_loc[max_max,1] + (Template.shape[1]/2) - 6 )

    objindex = objects[0,max_max]-1

    orientation = orientations[0,max_max]
    orientation_final = orientation
    if objindex == 1:
            orientation_final = np.minimum(orientation, 90 - orientation)
            if orientation<=90 - orientation:
                orientation_final = -orientation_final

    elif objindex == 2:
            orientation_final = np.minimum(orientation, 120 - orientation)
            if orientation<= 120 - orientation:
                orientation_final = -orientation_final

    return object_names[objects[0,max_max]-1],max_location,orientation_final,Img,np.double(max_val[0,max_max])
